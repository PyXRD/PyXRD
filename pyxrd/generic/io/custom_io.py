# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, sys

import numpy as np

# Small workaround to provide a unicode-aware open method for PyXRD:
if sys.version_info[0] < 3: # Pre Python 3.0
    import codecs
    _open_func_bak = open # Make a back up, just in case
    open = codecs.open
def unicode_open(*args, **kwargs):
    """
        Opens files in UTF-8 encoding by default, unless an 'encoding'
        keyword argument is passed. Returns a file object.
    """
    if not "encoding" in kwargs:
        kwargs["encoding"] = "utf-8"
    return open(*args, **kwargs)

from collections import OrderedDict
from traceback import format_exc

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
from zipfile import ZipFile, ZIP_DEFLATED, is_zipfile

import json
from pyxrd.data import settings

from gtk import TextBuffer

def sizeof_fmt(num):
    for x in ['bytes', 'kB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

def get_size(path='.', maxsize=None):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
            if maxsize != None and total_size > maxsize:
                break
        if maxsize != None and total_size > maxsize:
            break
    return total_size

class StorableRegistry(dict):
    """
        Basically a dict which maps class names to the actual
        class types. This relies on the classes being registered using
        the 'register' decorator provided in this class type.
        It also has a number of aliases, for backwards-compatibility.
    """

    # For backwards compatibility:
    aliases = {
        'generic.treemodels/XYListStore': 'XYListStore',
        'generic.treemodels/ObjectListStore': 'ObjectListStore',
        'generic.treemodels/ObjectTreeStore': 'ObjectTreeStore',
        'generic.treemodels/IndexListStore': 'IndexListStore',
        'generic.models.treemodels/ObjectListStore': 'ObjectListStore',
        'generic.models.treemodels/ObjectTreeStore': 'ObjectTreeStore',
        'generic.models.treemodels/IndexListStore': 'IndexListStore',
        'generic.models.treemodels/XYListStore': 'XYListStore',
        'generic.models/PyXRDLine': 'PyXRDLine',
        'generic.models/CalculatedLine': 'CalculatedLine',
        'generic.models/ExperimentalLine': 'ExperimentalLine',
        'goniometer.models/Goniometer': 'Goniometer',
        'specimen.models/Specimen': 'Specimen',
        'specimen.models/Marker': 'Marker',
        'mixture.models/Mixture': 'Mixture',
        'atoms.models/AtomType': 'AtomType',
        'atoms.models/Atom': 'Atom',
        'probabilities.R0models/R0G1Model': 'R0G1Model',
        'probabilities.R0models/R0G2Model': 'R0G2Model',
        'probabilities.R0models/R0G3Model': 'R0G3Model',
        'probabilities.R0models/R0G4Model': 'R0G4Model',
        'probabilities.R0models/R0G5Model': 'R0G5Model',
        'probabilities.R0models/R0G6Model': 'R0G6Model',
        'probabilities.R1models/R1G2Model': 'R1G2Model',
        'probabilities.R1models/R1G3Model': 'R1G3Model',
        'probabilities.R1models/R1G4Model': 'R1G4Model',
        'probabilities.R2models/R2G2Model': 'R2G2Model',
        'probabilities.R2models/R2G3Model': 'R2G3Model',
        'probabilities.R3models/R3G2Model': 'R3G2Model',
        'phases.CSDS_models/LogNormalCSDSDistribution': 'LogNormalCSDSDistribution',
        'phases.CSDS_models/DritsCSDSDistribution': 'DritsCSDSDistribution',
        'phases.atom_relations/AtomRelation': 'AtomRelation',
        'phases.atom_relations/AtomRatio': 'AtomRatio',
        'phases.atom_relations/AtomContents': 'AtomContents',
        'phases.models/UnitCellProperty': 'UnitCellProperty',
        'phases.models/Component': 'Component',
        'phases.models/Phase': 'Phase',
        'project.models/Project': 'Project',
    }

    def __getitem__(self, key):
        key = self.aliases.get(key, key)
        return super(StorableRegistry, self).__getitem__(key)

    def register(self):
        """
            Returns a decorator that will register Storable sub-classes.
        """
        return self.register_decorator

    def register_decorator(self, cls):
        if hasattr(cls, '__store_id__'):
            if settings.DEBUG: print "Registering %s as storage type with id '%s'" % (cls, cls.__store_id__)
            self[cls.__store_id__] = cls
        else:
            raise TypeError, "Cannot register an object as storable when it does not have a __store_id__ attribute."
        return cls

    pass # end of class

# This is filled using register decorator
storables = StorableRegistry()

class PyXRDEncoder(json.JSONEncoder):
    """
        A custom JSON encoder that checks if:
            - the object is a gtk.TextBuffer, if so the encodcer translates the
              object to a string containing the text in the buffer
            - the object has a to_json callable method, if so it is called to
              convert the object to a dict object. This dict object should have:
               - a 'type' key mapped to the storage type id of the storable class
               - a 'properties' key mapped to a dict of name-values for each
                 property that needs to be stored in order to be able to 
                 recreate the object.
              The user needs to register the class type as storable
              (see the 'registes_storable' method or the Storable class)
            - fall back to the default JSONEncoder methods
    """

    def default(self, obj):
        if type(obj) is TextBuffer:
            return obj.get_text(*obj.get_bounds())
        if hasattr(obj, "to_json") and callable(getattr(obj, "to_json")):
            return obj.to_json()
        if isinstance(obj, np.ndarray):
            return json.dumps(obj.tolist())
        # fallback:
        return json.JSONEncoder(self).default(obj)


class PyXRDDecoder(json.JSONDecoder):
    """
        A custom JSON decoder that can decode objects, following these steps:
            - decode the JSON object at once using the default decoder
            - the resulting dict is then parsed:
               - if a valid 'type' and a 'properties' key is given,
                 the object is translated using the mapped class type's 
                 'from_json' method.
               - parent keyword arguments are passed on (e.g. a project) to
                 the from_json method as well
    """

    def __init__(self, parent=None, **kwargs):
        json.JSONDecoder.__init__(self, **kwargs)
        self.parent = parent

    def decode(self, obj):
        obj = json.JSONDecoder.decode(self, obj)
        return self.__pyxrd_decode__(obj) or obj

    def __pyxrd_decode__(self, obj, **kwargs):
        if "type" in obj:
            objtype = storables[obj["type"]]
            if "properties" in obj and hasattr(objtype, "from_json"):
                if self.parent != None and not "parent" in kwargs:
                    kwargs["parent"] = self.parent
                return objtype.from_json(**dict(obj["properties"], **kwargs))
        raise Warning, "__pyxrd_decode__ will return None for %s!" % str(obj)[:30] + "..." + str(obj)[:-30]
        return None

# needs to be importable:
def __map_reduce__(json_obj):
    decoder = PyXRDDecoder()
    return decoder.decode(json_obj)

class Storable(object):
    """
        A class with a number of default implementations to serialize objects
        to JSON strings. It used the PyXRDDecoder en PyXRDEncoder.
        Subclasses should override the '__store_id__' property
        and register themsevels by calling the storables.register method
        and applying it as decorator to the subclass:
        
         @storables.register()
         class StorableSubclass(Storable, ...):
            ...
            
        Sub-classes can optionally implement the following methods:
         - 'json_properties' or for more fine-grained control 'to_json'
         - 'from_json'
         
    """
    __storables__ = []

    __store_id__ = None

    ###########################################################################
    # High-level JSON (de)serialisiation related methods & functions:
    ###########################################################################
    def dump_object(self, zipped=False):
        """
        Returns this object serialized as a JSON string
        """
        if zipped:
            f = StringIO()
            z = ZipFile(f, mode="w", compression=ZIP_DEFLATED)
            z.writestr('content', json.dumps(self, indent=4, cls=PyXRDEncoder))
            z.close()
            return f # return unclosed, users need to worry about this...
        else:
            return json.dumps(self, indent=4, cls=PyXRDEncoder)

    def print_object(self):
        """
        Prints the output from dump_object().
        """
        print self.dump_object()

    def save_object(self, filename, zipped=False):
        """
        Saves the output from dump_object() to a filename, optionally zipping it.
        """
        if zipped:
            f = ZipFile(filename, mode="w", compression=ZIP_DEFLATED)
            f.writestr('content', json.dumps(self, indent=4, cls=PyXRDEncoder))
            f.close()
        else:
            with unicode_open(filename, 'w') as f:
                json.dump(self, f, indent=4, cls=PyXRDEncoder)

    @staticmethod
    def load_object(filename, data=None, parent=None):
        """
        Tries to create an instance from the file 'filename' (see below), or
        from the JSON string 'data'. If data is passed, filename should be None,
        or it will be ignored
        
        *filename* the actual filename or a file-like object
        
        *parent* optional parent to pass to the JSON decoder
                
        :rtype: the loaded object instance
        """
        if filename != None:
            try:
                if is_zipfile(filename): # ZIP files
                    with ZipFile(filename, 'r') as zf:
                        with zf.open('content') as cf:
                            return json.load(cf, cls=PyXRDDecoder, parent=parent)
                else: # REGULAR files
                    with unicode_open(filename, 'r') as f:
                        return json.load(f, cls=PyXRDDecoder, parent=parent)
            except Exception as error:
                if settings.DEBUG: print "Handling run-time error: %s" % error
                tb = format_exc()
                try:
                    return json.load(filename, cls=PyXRDDecoder, parent=parent)
                except:
                    print tb
                    raise # re-raise last error
        elif data != None: # STRINGS:
            return json.loads(data, cls=PyXRDDecoder, parent=parent)


    ###########################################################################
    # Low-level JSON (de)serialisiation related methods & functions:
    ###########################################################################
    def to_json(self):
        """
        Method that should return a dict containing two keys:
         - 'type' -> registered class __store_id__
         - 'properties' -> a dict containg all the properties neccesary to 
           re-create the object when serialized as JSON.
        """
        return {
            "type": self.__store_id__,
            "properties": self.json_properties()
        }

    def json_properties(self):
        """
        Method that should return a dict containg all the properties neccesary to 
        re-create the object when serialized as JSON.
        """
        retval = OrderedDict()
        for val in self.__storables__:
            try:
                alias, attr = val
            except ValueError:
                alias, attr = val, val
            retval[alias] = getattr(self, attr)
        return retval

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
        if arg == None:
            return default
        elif isinstance(arg, dict) and "type" in arg and "properties" in arg:
            arg = PyXRDDecoder(parent=self if child else None).__pyxrd_decode__(arg, **kwargs)
            return arg
        else:
            return arg

    @classmethod
    def from_json(type, *args, **kwargs):
        """
            Class method transforming JSON kwargs into an instance of this class.
            By default this assumes a 1-on-1 mapping to the __init__ method.
        """
        return type(*args, **kwargs)

    ###########################################################################
    # Others:
    ###########################################################################
    def __reduce__(self):
        props = self.dump_object()
        return __map_reduce__, (props,), None

    pass # end of class
