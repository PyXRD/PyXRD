# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, types
from shutil import move
from collections import OrderedDict
import logging
logger = logging.getLogger(__name__)

try:
    from cStringIO import StringIO #@UnusedImport
except:
    from StringIO import StringIO #@Reimport

from zipfile import ZipFile, is_zipfile
try:
    # Check if zlib is available, if so, we can use compression when saving
    import zlib #@UnusedImport
    from zipfile import ZIP_DEFLATED as COMPRESSION
except ImportError:
    from zipfile import ZIP_STORED as COMPRESSION

from traceback import format_exc

from ..utils import not_none
from .utils import unicode_open
from .json_codec import PyXRDDecoder, PyXRDEncoder

class StorableRegistry(dict):
    """
        Basically a dict which maps class names to the actual
        class types. This relies on the classes being registered using
        the 'register' decorator provided in this class type.
        It also has a number of aliases, for backwards-compatibility (e.g.
        when class names change or from the era before using this method
        when we stored the entire class path, we might remove these at
        some point)
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

# Needs to be importable, could be used for more compact Python pickling:
def __map_reduce__(json_obj):
    decoder = PyXRDDecoder(mapper=storables)
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

    class Meta():  # Sub classes need to override this and set store_id!!
        store_id = None

    ###########################################################################
    # High-level JSON (de)serialisiation related methods & functions:
    ###########################################################################
    def dump_object(self, zipped=False, filename=None):
        """
            Returns this object serialized as a JSON string.
            If `zipped` is true it returns an in-memory ZipFile.
        """
        content = PyXRDEncoder.dump_object(self)
        if zipped:
            f = StringIO()
            with ZipFile(f, mode="w", compression=COMPRESSION) as z:
                z.writestr('content', content)
            return f
        else:
            return content

    def print_object(self):
        """
        Prints the output from dump_object().
        """
        print self.dump_object()

    def save_object(self, file, zipped=False): # @ReservedAssignment
        """
        Saves the output from dump_object() to `filename`, optionally zipping it.
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
                with ZipFile(file, mode="w", compression=COMPRESSION) as f:
                    for partname, json_object in self.to_json_multi_part():
                        f.writestr(partname, PyXRDEncoder.dump_object(json_object))
            else:
                # Regular text file:
                if filename is not None:
                    with unicode_open(file, 'w') as f:
                        PyXRDEncoder.dump_object_to_file(self, f)
                else:
                    PyXRDEncoder.dump_object_to_file(self, file)
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
            try: # Assume filename is a path
                if is_zipfile(filename): # ZIP files
                    with ZipFile(filename, 'r') as zf:
                        parts = dict()
                        for name in zf.namelist():
                            if name != "content":
                                with zf.open(name) as pf:
                                    parts[name] = pf.read()
                        with zf.open('content') as cf:
                            return PyXRDDecoder.decode_multi_part(cf.read(), parts=parts, mapper=storables, parent=parent)
                else: # REGULAR files
                    with unicode_open(filename, 'r') as f:
                        return PyXRDDecoder.decode_file(f, mapper=storables, parent=parent)
            except Exception as error: # Maybe filename is a file-like object?
                logger.debug("Handling run-time error: %s" % error)
                tb = format_exc()
                try:
                    return PyXRDDecoder.decode_file(filename, mapper=storables, parent=parent)
                except:
                    print tb
                    raise # re-raise last error, filename is something weird
        elif data is not None: # STRINGS:
            return PyXRDDecoder.decode_string(data, mapper=storables, parent=parent)


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
            This should generate a list of two-tuples:
            (partname, json_dict), (partname, json_dict), ...
            These can then be saved as seperate files (e.g. in a ZIP file)
        """
        yield ('content', self.to_json())

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
            arg = PyXRDDecoder(mapper=storables, parent=self if child else None).__pyxrd_decode__(arg, **kwargs)
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
