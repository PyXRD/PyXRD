# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, sys, types
from shutil import move

import numpy as np
from pyxrd.generic.utils import not_none

import logging
logger = logging.getLogger(__name__)

# Small workaround to provide a unicode-aware open method for PyXRD:
if sys.version_info[0] < 3: # Pre Python 3.0
    import codecs
    _open_func_bak = open # Make a back up, just in case
    open = codecs.open #@ReservedAssignment
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
    from cStringIO import StringIO #@UnusedImport
except:
    from StringIO import StringIO #@Reimport
from zipfile import ZipFile, ZIP_DEFLATED, is_zipfile

import json

def sizeof_fmt(num):
    for x in ['bytes', 'kB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

def get_size(path='.', maxsize=None):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path): #@UnusedVariable
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
            if maxsize is not None and total_size > maxsize:
                break
        if maxsize is not None and total_size > maxsize:
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
        if hasattr(cls, 'Meta') and hasattr(cls.Meta, 'store_id'):
            logger.debug("Registering %s as storage type with id '%s'" % (cls, cls.Meta.store_id))
            self[cls.Meta.store_id] = cls
        else:
            raise TypeError, "Cannot register type '%s' without a Meta.store_id!" % cls
        return cls

    pass # end of class

# This is filled using register decorator
storables = StorableRegistry()

class PyXRDEncoder(json.JSONEncoder):
    """
        A custom JSON encoder that checks if:
            - the object has a to_json callable method, if so it is called to
              convert the object to a JSON encodable object.
              E.g. the default implementation from the Storable class is a dict object
              containing:
               - a 'type' key mapped to the storage type id of the storable class
               - a 'properties' key mapped to a dict of name-values for each
                 property that needs to be stored in order to be able to 
                 recreate the object.
              If the user registered this class as a storable
              (see the 'registes_storable' method or the Storable class)
              then the JSON object is transformed back into the actual Python
              object using its from_json(...) method. Default implementation
              finds the registered class using the 'type' value and passes the
              'properties' value to its constructor as keyword arguments.  
            - if the object is a numpy array, it is converted to a list
            - if the object is a wrapped list, dictionary, ... (ObsWrapper 
              subclass) then the wrapped object is returned, as these are
              directly JSON encodable.
            - fall back to the default JSONEncoder methods
    """

    def default(self, obj):
        from mvc.support.observables import ObsWrapper
        if hasattr(obj, "to_json") and callable(getattr(obj, "to_json")):
            return obj.to_json()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, ObsWrapper):
            return obj._obj # return the wrapped object
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

    @staticmethod
    def decode_multi_part(obj, parts={}, **kwargs):
        """
            Utility function that allows for multi-part (ZipFile) JSON objects
            Shortens the length of the main file, e.g. by splitting out lists of
            other objects into separate files.
        """
        decoder = PyXRDDecoder(**kwargs)
        obj = json.JSONDecoder.decode(decoder, obj)
        if not hasattr(obj, "update"):
            raise RuntimeError, "Decoding a multi-part JSON object requires the root to be a dictionary object!"
        for partname, partobj in parts.iteritems():
            obj["properties"][partname] = json.JSONDecoder.decode(decoder, partobj)
        return decoder.__pyxrd_decode__(obj) or obj

    def decode(self, obj):
        obj = json.JSONDecoder.decode(self, obj)
        return self.__pyxrd_decode__(obj) or obj

    def __pyxrd_decode__(self, obj, **kwargs):
        if isinstance(obj, list):
            for index, subobj in enumerate(obj):
                obj[index] = self.__pyxrd_decode__(subobj) or subobj
            return obj
        if "type" in obj:
            objtype = storables[obj["type"]]
            if "properties" in obj and hasattr(objtype, "from_json"):
                if self.parent is not None and not "parent" in kwargs:
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
        Subclasses should override their 'Meta.store_id' property
        and register themselves by calling the storables.register method
        and applying it as decorator to the subclass:
        
         @storables.register()
         class StorableSubclass(Storable, ...):
            ...
            
        Sub-classes can optionally implement the following methods:
         - 'json_properties' or for more fine-grained control 'to_json'
         - 'from_json'
         
    """
    __storables__ = []

    class Meta():  # override this!
        store_id = None

    def __init__(self, *args, **kwargs):
        # Nothing to do but ignore any extraneous args & kwargs passed down
        object.__init__(self)

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

    def save_object(self, file, zipped=False): # @ReservedAssignment
        """
        Saves the output from dump_object() to a filename, optionally zipping it.
        File can be either a filename or a file-like object. If it is a filename
        extra precautions are taken to prevent malformed data overwriting a good
        file. With file objects this is not the case.
        """

        filename = None
        if isinstance(file, types.StringTypes):
            # We have a filename, not a file object
            filename = file
            # Create temporary filenames for output, and a backup filename if
            # the file already exists.
            file = filename + ".tmp" # @ReservedAssignment
            backup_name = filename + "~"

        try:
            if zipped:
                # Try to safe the file as a zipfile:
                with ZipFile(file, mode="w", compression=ZIP_DEFLATED) as f:
                    for partname, json_object in self.to_json_multi_part():
                        f.writestr(partname, json.dumps(json_object, indent=4, cls=PyXRDEncoder))
            else:
                # Regular text file:
                if filename is not None:
                    with unicode_open(file, 'w') as f:
                        json.dump(self, f, indent=4, cls=PyXRDEncoder)
                else:
                    json.dump(self, file, indent=4, cls=PyXRDEncoder)
        except:
            # In case saving fails, remove the temporary file:
            if filename is not None and os.path.exists(file):
                os.remove(file)
            raise

        if filename is not None:
            # If target file exists, back it up:
            if os.path.exists(filename):
                move(filename, backup_name)
            # Rename temporary saved file:
            move(file, filename)

    @classmethod
    def load_object(cls, filename, data=None, parent=None):
        """
        Tries to create an instance from the file 'filename' (see below), or
        from the JSON string 'data'. If data is passed, filename should be None,
        or it will be ignored
        
        *filename* the actual filename or a file-like object
        
        *parent* optional parent to pass to the JSON decoder
                
        :rtype: the loaded object instance
        """
        if filename is not None:
            try:
                if is_zipfile(filename): # ZIP files
                    with ZipFile(filename, 'r') as zf:
                        parts = dict()
                        for name in zf.namelist():
                            if name != "content":
                                with zf.open(name) as pf:
                                    parts[name] = pf.read()
                        with zf.open('content') as cf:
                            return PyXRDDecoder.decode_multi_part(cf.read(), parts=parts, parent=parent)
                else: # REGULAR files
                    with unicode_open(filename, 'r') as f:
                        return json.load(f, cls=PyXRDDecoder, parent=parent)
            except Exception as error:
                logger.debug("Handling run-time error: %s" % error)
                tb = format_exc()
                try:
                    return json.load(filename, cls=PyXRDDecoder, parent=parent)
                except:
                    print tb
                    raise # re-raise last error
        elif data is not None: # STRINGS:
            return json.loads(data, cls=PyXRDDecoder, parent=parent)


    ###########################################################################
    # Low-level JSON (de)serialisiation related methods & functions:
    ###########################################################################
    def to_json(self):
        """
        Method that should return a dict containing two keys:
         - 'type' -> registered class Meta.store_id
         - 'properties' -> a dict containg all the properties neccesary to 
           re-create the object when serialized as JSON.
        """
        return {
            "type": self.Meta.store_id,
            "properties": self.json_properties()
        }

    def to_json_multi_part(self):
        """
            This should generate two-tuples:
            (partname, json_dict), (partname, json_dict), ...
        """
        yield ('content', self.to_json())

    # Inherited classes can also implement:
    # def multi_file_to_json(self):
    # this should return a list of two-tuples:
    #  (filename, json_dict) (filename, json_dict), ...
    # The combination

    def json_properties(self):
        """
        Method that should return a dict containing all the properties necessary to 
        re-create the object when serialized as JSON.
        """
        retval = OrderedDict()
        def add_prop(val):
            try:
                alias, attr = val
            except ValueError:
                alias, attr = val, val
            retval[alias] = getattr(self, attr)

        from mvc.models import Model
        if isinstance(self, Model):
            for prop in self.Meta.all_properties:
                if prop.storable:
                    add_prop((prop.name, not_none(prop.stor_name, prop.name)))
        elif hasattr(self, "__storables__"): # Fallback:
            for val in self.__storables__:
                add_prop(val)
        else:
            raise RuntimeError, "Cannot find either a '__storables__' or Meta class attribute on Storable '%s' instance!" % type(self)
        return retval

    def parse_init_arg(self, arg, default, child=False, default_is_class=False, **kwargs):
        """
        Can be used to transform an argument passed to a __init__ method of a
        Storable (sub-)class containing a JSON dict into the actual object it
        is representing.
        
        *arg* the passed argument
        
        *default* the default value if argument is None
        
        **child* boolean flag indicating wether or not the object is a child,
        if true, self is passed as the parent keyword to the JSON decoder if
        the passed argument is a JSON dict
        
        **default_is_class** boolean flag indicating whether or not the passed
        default value is an unitialized type. If True, the type will be initialized
        using the kwargs passed to this function.
        
        **kwargs* any other kwargs are passed to the JSON decoder if the passed
        argument is a JSON dict
        
        :rtype: the argument (not a JSON dict), the actual object (argument was
        a JSON dict) or the default value (argument was None)
        """
        if arg == None:
            if not default_is_class:
                return default
            else:
                if child: kwargs["parent"] = self
                return default(**kwargs)
        elif isinstance(arg, dict) and "type" in arg and "properties" in arg:
            arg = PyXRDDecoder(parent=self if child else None).__pyxrd_decode__(arg, **kwargs)
            return arg
        else:
            return arg

    @classmethod
    def from_json(cls, *args, **kwargs):
        """
            Class method transforming JSON kwargs into an instance of this class.
            By default this assumes a 1-on-1 mapping to the __init__ method.
        """
        return cls(*args, **kwargs)

    ###########################################################################
    # Others:
    ###########################################################################
    def __reduce__(self):
        props = self.dump_object()
        return __map_reduce__, (props,), None

    pass # end of class
