# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import json

from gtk import TextBuffer
       
def get_json_type(strtype):
    parts = strtype.split('/')
    t = parts[-1]
    m = __import__("".join(parts[:-1]), fromlist=[""])
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
    def decode(self, obj):
        #print obj
        obj = json.JSONDecoder.decode(self, obj)
        return PyXRDDecoder.__pyxrd_decode__(obj) or obj
    
    @staticmethod
    def __pyxrd_decode__(obj, **kwargs):
        if "type" in obj:
            objtype = get_json_type(obj["type"])
            if "properties" in obj and hasattr(objtype, "from_json"):
                #print "!!!! LOADING TYPE %s" % objtype
                return objtype.from_json(**dict(obj["properties"], **kwargs))
        raise Warning, "__pyxrd_decode__ will return None for %s!" % obj
        return None
        
class Storable():
    __storables__ = []

    def __init__(self):
        pass #nothind todo atm

    def dump_object(self):
        return json.dumps(self, indent = 4, cls=PyXRDEncoder)

    def print_object(self):
        print self.dump_object()

    def save_object(self, filename):
        f = open(filename, 'w')
        json.dump(self, f, indent = 4, cls=PyXRDEncoder)
        f.close()
        
    @staticmethod
    def load_object(filename):
        f = open(filename, 'r')
        ret = json.load(f, cls=PyXRDDecoder)
        f.close()
        return ret

    def json_properties(self):
        retval = {}
        for name in self.__storables__:
            retval[name] = getattr(self, name)
        return retval
    
    def to_json(self):
        return { 
            "type": json_type(type(self)),
            "properties": self.json_properties()
        }
    
    @classmethod
    def from_json(type, **kwargs):
        return type(**kwargs)
