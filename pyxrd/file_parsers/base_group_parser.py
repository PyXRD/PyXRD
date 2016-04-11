# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import types
import fnmatch

from .base_parser import BaseParser

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
    def _get_file(cls, fp, close=None):
        """
            Returns a three-tuple:
            if fp is a filename:
            filename, filename, close
            or if fp is file-like object:
            filename, file, close
            where filename can be None
            Opening of the file is left to the actual parser class if a filename
            was passed. If a file is passed, care must be taken to ensure it is
            opened in the correct mode (the __file_mode__ attribute on the 
            actual parsers class called). Therefore, it is safer to pass
            filenames to a BaseGroupParser sub-class than it is to pass a 
            file-like object. 
        """
        if isinstance(fp, types.StringType):
            return fp, fp, True if close is None else close
        else:
            return getattr(fp, 'name', None), fp, False if close is None else close

    @classmethod
    def get_parser(cls, filename, fp=None):
        if not type(filename) is str and hasattr(fp, 'name'):
            filename = fp.name
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
    def parse(cls, fp, data_objects=None, close=True):
        """
            Parses the file 'fp' using one of the parsers in this group.
            'fp' should preferably be a filename (str), but can be a file-like
            object. Take care to open the file in the correct mode when passing
            a file-like object.  
        """
        filename, fp, close = cls._get_file(fp, close=close)
        parser = cls.get_parser(filename, fp=fp)
        return parser.parse(fp, data_objects=data_objects, close=close)

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
