# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from collections import OrderedDict
from traceback import format_exc

import json
import settings

from gtk import TextBuffer
       
def get_json_type(strtype):
    parts = strtype.split('/')
    t = parts[-1]
    m = "".join(parts[:-1])
    if m == "generic.models" and t=="XYData":
        return None
    else:
        m = __import__(m, fromlist=[""])
        return getattr(m, t)

def json_type(type):
    return type.__module__ + "/" + type.__name__

class PyXRDEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) is TextBuffer:
            return obj.get_text(*obj.get_bounds())
        if hasattr(obj, "to_json") and callable(getattr(obj, "to_json")):
            return obj.to_json()
        #fallback:
        return json.JSONEncoder(self).default(obj)
            
class PyXRDDecoder(json.JSONDecoder):
    def __init__(self, parent=None, **kwargs):
        json.JSONDecoder.__init__(self, **kwargs)
        self.parent = parent

    def decode(self, obj):
        obj = json.JSONDecoder.decode(self, obj)
        return self.__pyxrd_decode__(obj) or obj
    
    def __pyxrd_decode__(self, obj, **kwargs):
        if "type" in obj:
            objtype = get_json_type(obj["type"])
            if "properties" in obj and hasattr(objtype, "from_json"):
                if self.parent!=None and not "parent" in kwargs:
                    kwargs["parent"] = self.parent
                return objtype.from_json(**dict(obj["properties"], **kwargs))
        raise Warning, "__pyxrd_decode__ will return None for %s!" % str(obj)[:30]+"..."+str(obj)[:-30]
        return None
    
def __map_reduce__(json_obj):
    decoder = PyXRDDecoder()
    return decoder.decode(json_obj)
        
class Storable(object):
    __storables__ = []

    def dump_object(self):
        return json.dumps(self, indent = 4, cls=PyXRDEncoder)

    def print_object(self):
        print self.dump_object()

    def save_object(self, filename):
        with open(filename, 'w') as f:
            json.dump(self, f, indent = 4, cls=PyXRDEncoder)
    
    @staticmethod
    def load_object(filename, parent=None):
        """
        Tries to create an object from the file 'filename' (see below).
        
        *filename* the actual filename or a file-like object
        
        *parent* optional parent to pass to the JSON decoder
                
        :rtype: the loaded object instance
        """
        try:
            with open(filename, 'r') as f:
                return json.load(f, cls=PyXRDDecoder, parent=parent)
        except TypeError as error:
            print "Handling run-time error: %s" % error
            tb = format_exc()
            try:
                return json.load(filename, cls=PyXRDDecoder, parent=parent)
            except:
                print tb
                raise #re-raise last error
                
    def json_properties(self):
        retval = OrderedDict()
        for name in self.__storables__:
            retval[name] = getattr(self, name)
        return retval
    
    def to_json(self):
        return { 
            "type": json_type(type(self)),
            "properties": self.json_properties()
        }
    
    def parse_init_arg(self, arg, default, child=False, **kwargs):
        """
        Can be used to transform an argument passed to a __init__ method of a
        Storable (sub-)class containing a JSON dict into the actual object it
        is representing.
        
        *arg* the passed argument
        
        *default* the default value if argument is None
        
        **child* boolean flag indicating wether or not the object is a child,
        if true, self is passed as the parent keyword to the JSON decoder if
        the passed argument is a JSON dict
        
        **kwargs* any other kwargs are passed to the JSON decoder if the passed
        argument is a JSON dict
        
        :rtype: the argument (not a JSON dict), the actual object (argument was
        a JSON dict) or the default value (argument was None)
        """
        if arg==None:
            return default
        elif isinstance(arg, dict) and "type" in arg and "properties" in arg:
            arg = PyXRDDecoder(parent=self if child else None).__pyxrd_decode__(arg, **kwargs)
            return arg
        else:
            return arg
    
    @classmethod
    def from_json(type, *args, **kwargs):
        """
            Method transforming JSON kw-args into __init__ kwargs.
            Ideally this is a 1-in-1 mapping and no transformation is needed,
            q.e. the __init__ function can handle JSON kw-args.
        """
        return type(*args, **kwargs)

    def __reduce__(self):
        props = self.dump_object()
        return __map_reduce__, (props,), None

    pass #end of class
