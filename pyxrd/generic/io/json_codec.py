# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import json
import numpy as np

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

    ###########################################################################
    # Convenience functions: use these!
    ###########################################################################
    @classmethod
    def dump_object(cls, obj):
        """ Serialize an object using this encoder and return it as a string """
        return json.dumps(obj, indent=4, cls=cls)

    @classmethod
    def dump_object_to_file(cls, obj, f):
        """ Serialize an object using this encoder and dump it into a file"""
        return json.dump(obj, f, indent=4, cls=cls)

    ###########################################################################
    # Sub class implementation:
    ###########################################################################
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
                 'from_json' method. This mapping is done using a dict mapping
                 the json class name to an actual class type (`mapper` __init__ keyword)
               - parent keyword arguments are passed on (e.g. a project) to
                 the from_json method as well
    """

    def __init__(self, mapper=None, parent=None, **kwargs):
        super(PyXRDDecoder, self).__init__(**kwargs)
        self.mapper = mapper
        self.parent = parent

    ###########################################################################
    # Convenience functions: use these!
    ###########################################################################
    @classmethod
    def decode_multi_part(cls, obj, mapper, parts={}, **kwargs):
        """
            Utility function that allows for multi-part (ZipFile) JSON objects
            Shortens the length of the main file, e.g. by splitting out lists of
            other objects into separate files.
        """
        decoder = cls(mapper, **kwargs)
        obj = json.JSONDecoder.decode(decoder, obj)
        if not hasattr(obj, "update"):
            raise RuntimeError, "Decoding a multi-part JSON object requires the root to be a dictionary object!"
        for partname, partobj in parts.iteritems():
            obj["properties"][partname] = json.JSONDecoder.decode(decoder, partobj)
        return decoder.__pyxrd_decode__(obj) or obj

    @classmethod
    def decode_file(cls, f, mapper, parent=None):
        return json.load(f, cls=PyXRDDecoder, mapper=mapper, parent=parent)

    @classmethod
    def decode_string(cls, string, mapper, parent=None):
        return json.loads(string, cls=PyXRDDecoder, mapper=mapper, parent=parent)

    ###########################################################################
    # Sub class implementation:
    ###########################################################################
    def decode(self, string):
        """ Decodes a json string into an object """
        # First use a regular decode:
        obj = super(PyXRDDecoder, self).decode(string)
        # Then parse this dict into an actual python object:
        return self.__pyxrd_decode__(obj) or obj

    def __pyxrd_decode__(self, obj, **kwargs):
        """ Decodes the PyXRD JSON object serialization """
        if isinstance(obj, list):
            for index, subobj in enumerate(obj):
                obj[index] = self.__pyxrd_decode__(subobj) or subobj
            return obj
        if "type" in obj:
            objtype = self.mapper[obj["type"]]
            if "properties" in obj and hasattr(objtype, "from_json"):
                if self.parent is not None and not "parent" in kwargs:
                    kwargs["parent"] = self.parent
                return objtype.from_json(**dict(obj["properties"], **kwargs))
        raise Warning, "__pyxrd_decode__ will return None for %s!" % str(obj)[:30] + "..." + str(obj)[:-30]
        return None
