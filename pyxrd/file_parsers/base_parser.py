# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from .meta_parser import MetaParser
from .data_object import DataObject
import types

class BaseParser(object):
    """
        Base class providing some common attributes and functions.
        Do not register this class or subclasses without overriding the
        following functions:
            - parse_header
            - parse_data
            - parse (optional)
            - setup_file_filter (optional)
    """

    __metaclass__ = MetaParser

    # This should be changed by sub-classes
    description = "Base Parser"
    extensions = []
    mimetypes = []
    @property
    def can_write(self):
        return getattr(self, "write", None) is not None
    @property
    def can_read(self):
        return getattr(self, "parse", None) is not None
    data_object_type = DataObject

    # This should be changed by sub-classes
    __file_mode__ = "r"

    file_filter = None

    @classmethod
    def _get_file(cls, fp, close=None):
        """
            Returns a three-tuple:
            filename, file-object, close
        """
        if isinstance(fp, types.StringType):
            return fp, open(fp, cls.__file_mode__), True if close is None else close
        else:
            return getattr(fp, 'name', None), fp, False if close is None else close

    @classmethod
    def _adapt_data_object_list(cls, data_objects, num_samples, only_extend=False):
        # If not yet created, create data_objects list:
        if data_objects == None:
            data_objects = [None, ]
        # If not yet the same length, adapt:
        num_data_objects = len(data_objects)
        if num_data_objects < num_samples:
            data_objects.extend([None] * int(num_samples - num_data_objects))
        if not only_extend and num_data_objects > num_samples:
            data_objects = data_objects[:num_samples]
        # If not yet initialized, initialize:
        for i in range(num_samples):
            if not data_objects[i]:
                data_objects[i] = cls.data_object_type()
        return data_objects

    @classmethod
    def _parse_header(cls, filename, fp, data_objects=None, close=False):
        """
            This method is implemented by sub-classes.
            It should parse the file and returns a list of DataObjects 
            with the header properties filled in accordingly.
            The filename argument is always required. If no file object is passed
            as keyword argument, it only serves as a label. Otherwise a new file
            object is created. 
            File objects are not closed unless close is set to True.
            Existing DataObjects can be passed as well and will then 
            be used instead of creating new ones.
        """
        # This should be implemented by sub-classes
        raise NotImplementedError

    @classmethod
    def _parse_data(cls, filename, fp, data_objects=None, close=False):
        """
            This method is implemented by sub-classes.
            It should parse the file and return a list of DataObjects
            with the data properties filled in accordingly.
            The filename argument is always required. If no file object is passed
            as keyword argument, it only serves as a label. Otherwise a new file
            object is created.
            File objects are not closed unless close is set to True.
            Existing DataObjects can be passed as well and will then 
            be used instead of creating new ones.
        """
        # This should be implemented by sub-classes
        raise NotImplementedError


    @classmethod
    def parse(cls, fp, data_objects=None, close=True):
        """
            This method parses the file and return a list of DataObjects
            with both header and data properties filled in accordingly.
            The filename argument is always required. If no file object is passed
            as keyword argument, it only serves as a label. Otherwise a new file
            object is created.
            File objects are closed unless close is set to False.
            Existing DataObjects can be passed as well and will then 
            be used instead of creating new ones.
        """
        filename, fp, close = cls._get_file(fp, close=close)
        data_objects = cls._parse_header(filename, fp, data_objects=data_objects)
        data_objects = cls._parse_data(filename, fp, data_objects=data_objects)
        if close: fp.close()
        return data_objects

    @classmethod
    def setup_file_filter(cls):
        """
            Creates a file filter based on a list of extensions set in the
            'extensions' attribute of the class using the 'description' attribute
            as the name for the filter. If the 'mimetypes' attribute is also set,
            it will also set these. If additional properties are needed, this function
            should be overriden by subclasses.
        """
        if cls.file_filter == None and cls.description != "" and cls.extensions:
            try:
                import gtk
            except ImportError:
                pass
            else:
                # Init file filter:
                cls.file_filter = gtk.FileFilter()
                cls.file_filter.set_name(cls.description)
                for mtpe in cls.mimetypes:
                    # cls.file_filter.add_mime_type(mtpe)
                    pass
                for expr in cls.extensions:
                    cls.file_filter.add_pattern(expr)
                cls.file_filter.set_data("parser", cls)

    pass # end of class