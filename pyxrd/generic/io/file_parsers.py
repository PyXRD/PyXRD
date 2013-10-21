# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import fnmatch

import numpy as np

parsers = {} # dict with lists of BaseParser subclasses, keys are namespaces

def register_parser(first=False):
    """
        Decorator that can be used to register parser sub-classes.       
        If the first argument is set to True, to parser will be inserted
        at the beginning of the namespace list instead of the end.

        Parsers are grouped in a lists using their 'namespace' class attribute.
        The registered classes can be accesed by importing the 'parsers' dict
        from the file_parsers module.
    """
    def wrapped_register(cls):
        global parsers
        if not cls.namespace in parsers:
            parsers[cls.namespace] = []
        if first:
            parsers[cls.namespace].insert(0, cls)
        else:
            parsers[cls.namespace].append(cls)
        return cls
    return wrapped_register


class DataObject(object):
    """
        A generic class holding all the information retrieved from a file
        using a BaseParser class.
    """

    # general information
    filename = None

    def __init__(self, *args, **kwargs):
        super(DataObject, self).__init__()
        self.update(**kwargs)

    def update(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    pass # end of class


class MetaParser(type):
    def __new__(meta, name, bases, attrs): # @NoSelf
        res = super(MetaParser, meta).__new__(meta, name, bases, attrs)
        res.setup_file_filter()
        return res

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
    namespace = "generic"
    extensions = []
    mimetypes = []
    can_write = False
    data_object_type = DataObject

    # This should be changed by sub-classes
    __file_mode__ = "r"

    file_filter = None

    @classmethod
    def _get_file(cls, filename, f=None, close=None):
        """
            Returns a three-tuple:
            filename, file-object, close
        """
        if hasattr(f, "read"):
            return filename, f, False if close == None else close
        elif type(filename) is str:
            return filename, open(filename, cls.__file_mode__), True if close == None else close
        else:
            raise TypeError, "Wrong argument: either a file object or a valid \
                filename must be passed, not '%s' or '%s'" % (cls.description, filename, f)

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
    def parse_header(cls, filename, f=None, data_objects=None, close=False):
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
    def parse_data(cls, filename, f=None, data_objects=None, close=False):
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
    def parse(cls, filename, f=None, data_objects=None, close=True):
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
        filename, f, close = cls._get_file(filename, f=f, close=close)
        data_objects = cls.parse_header(filename, f=f, data_objects=data_objects)
        data_objects = cls.parse_data(filename, f=f, data_objects=data_objects)
        if close: f.close()
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

class BaseGroupBarser(BaseParser):
    """
        Base class for parsers that are composed of several sub-parsers (parsers
        class attribute).
        This allows to quickly find the correct parser based on the filename.
        When a (python) file object is passed to the parse functions, the 'name'
        attribute must be present on the object, otherwise an error is raised.
        Alternatively, you can pass in a file object, together with a (fake)
        filename argument.
    """
    parsers = None

    @classmethod
    def get_parser(cls, filename, f=None):
        if not type(filename) is str and hasattr(f, 'name'):
            filename = f.name
        if not type(filename) is str:
            raise TypeError, "Wrong type for filename (%s), must be a string, but %s was given" % (cls.description, type(filename))
        else:
            try:
                import gio
                giof = gio.File(filename) # @UndefinedVariable
                file_mime = giof.query_info('standard::content-type').get_content_type()
                del giof
            except ImportError:
                file_mime = "NONE/NONE"
                pass

            # TODO init file_mime if importerror was raised...
            for parser in cls.parsers:
                passed = False
                for mime in parser.mimetypes:
                    if file_mime.split('/')[0] == mime.split('/')[0]: # TODO if an exact match can be made, even better
                        passed = True
                        break
                    else:
                        passed = False
                for extension in parser.extensions:
                    if fnmatch.fnmatch(filename, extension):
                        passed = True
                        break
                    else:
                        passed = False
                if passed:
                    return parser
                    break # just for the sake of clarity

    @classmethod
    def parse_header(cls, filename, f=None, data_objects=None, close=False):
        parser = cls.get_parser(filename, f=f)
        return parser.parse_header(filename, f=f, data_objects=data_objects, close=close)

    @classmethod
    def parse_data(cls, filename, f=None, data_objects=None, close=False):
        parser = cls.get_parser(filename, f=f)
        return parser.parse_data(filename, f=f, data_objects=data_objects, close=close)

    @classmethod
    def parse(cls, filename, f=None, data_objects=None, close=True):
        parser = cls.get_parser(filename, f=f)
        return parser.parse(filename, data_objects=data_objects, close=close)

    @classmethod
    def setup_file_filter(cls):
        """
            Creates a file filter based on a list of extensions set in the
            'extensions' attribute of the class using the 'description' attribute
            as the name for the filter. If the 'mimetypes' attribute is also set,
            it will also set these. If additional properties are needed, this function
            should be overriden by subclasses.
        """
        try:
            import gtk
        except ImportError:
            pass
        else:
            if cls.file_filter == None and cls.description and cls.parsers:
                cls.file_filter = gtk.FileFilter()
                cls.file_filter.set_name(cls.description)
                for parser in cls.parsers:
                    for mtpe in parser.mimetypes:
                        # cls.file_filter.add_mime_type(mtpe)
                        pass
                    for expr in parser.extensions:
                        cls.file_filter.add_pattern(expr)
                cls.file_filter.set_data("parser", cls)

    pass # end of class

def create_group_parser(name, *parsers, **kwargs):
    """
        Factory function for creating BaseGroupParser sub-classes,
        pass it a class name and a list of parser classes as arguments.
        Optional key-word arguments are a description and namespace argument,
        which will be set as class attributes. Default values are "All supported files"
        and "generic" respectively.
    """
    description = kwargs.pop("description", "All supported files")
    namespace = kwargs.pop("namespace", "generic")

    group_parser_type = register_parser(first=True)(type(name, (BaseGroupBarser,), dict(
         namespace=namespace,
         description=description,
         parsers=parsers
    )))
    return group_parser_type

class ASCIIParser(BaseParser):
    """
        ASCII Parser
    """
    description = "ASCII data"
    mimetypes = ["text/plain", ]
    can_write = True

    @classmethod
    def get_last_line(cls, f):
        i = -1
        for i, l in enumerate(f):
            pass
        return i + 1, l

    @classmethod
    def write(cls, filename, header, x, ys, delimiter=","):
        """
            Writes the header to the first line, and will write x, y1, ..., yn
            rows for each column inside the x and ys arguments.
            Header argument should not include a newline.
        """
        f = open(filename, 'w')
        f.write(u"%s\n" % header)
        np.savetxt(f, np.insert(ys, 0, x, axis=0).transpose(), fmt="%.8f", delimiter=delimiter)
        f.close()

    pass # end of class
