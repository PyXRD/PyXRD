# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, sys, struct, fnmatch

import numpy as np
import gtk, gio

from generic.controllers.utils import get_case_insensitive_glob
from generic.utils import u

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
   
#TODO 
# - Generalize the parse and meta_parse methods (common output signature)
# - ...
   
class MetaParser(type):
    def __new__(meta, name, bases, attrs):
        res = super(MetaParser, meta).__new__(meta, name, bases, attrs)
        res.setup_file_filter()
        return res
   
class BaseParser(object):
    """
        Base class providing some common attributes and functions.
        Do not register this class or subclasses without overriding the
        following functions:
            - parse
            - multi_parse
            - setup_file_filter
    """
    
    __metaclass__ = MetaParser

    #This should be changed by sub-classes    
    description = ""
    namespace = "generic"
    extensions  = []
    mimetypes   = []
    can_write   = False
    
    #This should be changed by sub-classes
    __file_mode__ = "r"
    
    file_filter = None
    
    @classmethod
    def _get_file(cls, data):
        if type(data) is file:
            return False, data
        elif type(data) is str:
            return True, open(data, cls.__file_mode__)
        else:
            raise TypeError, "Wrong data type supplied for '%s' format, \
                must be either file or string, but %s was given" % (cls.description, type(data))
    
    @classmethod
    def parse(cls, data):
        """
            This method should be implemented by sub-classes. It should return a
            generator returning a lists containing the values for each data row.
            This method is the most basic parser. For retrieving more information
            from a file, use the multi_parse method. It has a slightly more
            complex output, but can be more useful.
        """
        #This should be implemented by sub-classes
        raise NotImplementedError

    @classmethod     
    def multi_parse(cls, filename):
        """
            This method should be implemented by sub-classes. It should return a
            generator retuning 3-tuples containing:
                - filename
                - sample name
                - splitted data generator, e.g. a (n,2) numpy array with n rows 
                  of x,y values. This differs from the parse method in that it
                  does not return rows if there are multiple columns.
            That way this method allows to generate multiple specimens from
            either multiple filenames (by calling the method several times with
            different filenames), but also to generate multiple specimens
            from a single data file having more then one y data column (e.g.
            exported calculated data files).
        """
        #This should be implemented by sub-classes
        raise NotImplementedError
        
    @classmethod
    def setup_file_filter(cls):
        """
            Creates a file filter based on a list of extensions set in the
            'extensions' attribute of the class using the 'description' attribute
            as the name for the filter. If the 'mimetypes' attribute is also set,
            it will also set these. If additional properties are needed, this function
            should be overriden by subclasses.
        """
        if cls.file_filter==None and cls.description!="" and cls.extensions:
            #Init file filter:        
            cls.file_filter = gtk.FileFilter()
            cls.file_filter.set_name(cls.description)
            for mtpe in cls.mimetypes:
                #cls.file_filter.add_mime_type(mtpe)
                pass
            for expr in cls.extensions:
                cls.file_filter.add_pattern(expr)
            cls.file_filter.set_data("parser", cls)
    
    pass #end of class

class BaseGroupBarser(BaseParser):

    parsers = None

    @classmethod
    def get_parser(cls, data):
        if not type(data) is str:
            raise TypeError, "Wrong data type supplied for '%s' format, must be a string, but %s was given" % (cls.description, type(data))
        else:
            giof = gio.File(data)
            for parser in cls.parsers:
                passed = False
                file_mime = giof.query_info('standard::content-type').get_content_type()
                for mime in parser.mimetypes:
                    if file_mime.split('/')[0] == mime.split('/')[0]: #TODO if an exact match can be made, even better
                        passed = True
                        break
                    else:
                        passed = False
                for extension in parser.extensions:
                    if fnmatch.fnmatch(data, extension):
                        passed = True
                        break
                    else:
                        passed = False
                if passed:
                    return parser
                    break #just for the sake of clarity

    @classmethod
    def parse(cls, data):
        parser = cls.get_parser(data)
        return parser.parse(data)
        
    @classmethod     
    def multi_parse(cls, filename):
        parser = cls.get_parser(filename)
        return parser.multi_parse(filename)
        
    @classmethod
    def setup_file_filter(cls):
        """
            Creates a file filter based on a list of extensions set in the
            'extensions' attribute of the class using the 'description' attribute
            as the name for the filter. If the 'mimetypes' attribute is also set,
            it will also set these. If additional properties are needed, this function
            should be overriden by subclasses.
        """
        if cls.file_filter==None and cls.description and cls.parsers:
            cls.file_filter = gtk.FileFilter()            
            cls.file_filter.set_name(cls.description)
            for parser in cls.parsers:
                for mtpe in parser.mimetypes:
                    #cls.file_filter.add_mime_type(mtpe)    
                    pass        
                for expr in parser.extensions:
                    cls.file_filter.add_pattern(expr)
            cls.file_filter.set_data("parser", cls)

    pass #end of class
    
def create_group_parser(name, *parsers, **kwargs):
    description = kwargs.pop("description", "All supported files")
    namespace = kwargs.pop("namespace", "generic")

    group_parser_type = register_parser(first=True)(type(name, (BaseGroupBarser,), dict(
         namespace = namespace,
         description = description,
         parsers = parsers
    )))
    return group_parser_type

class BaseCSVParser(BaseParser):
    """
        Base ASCII CSV Parser
    """
    
    description = "ASCII data"
    mimetypes   = ["text/plain",]
    can_write   = True
    
    @classmethod
    def parse(cls, data, has_header=True):
        close, f = cls._get_file(data)
        if f != None:
            while True:
                line = f.readline()
                if has_header:
                    has_header=False #skip header
                elif line != "":
                    yield map(float, line.replace(",",".").split())
                else:
                    break
                
        if close: f.close()
           
    @classmethod     
    def multi_parse(cls, filename):
        close, f = cls._get_file(filename)
                
        header = f.readline().replace("\n", "")
        sample_names = header.split(u"##")
        if len(sample_names) > 1:
            sample_names = [sample_names[0] + sample_names[1],] + sample_names[2:]
        name = u(os.path.basename(filename))

        #TODO make this return real generators!
        ays = None
        for data in cls.parse(f, has_header=False):
            x, ay = data[0], data[1:] #ay contains columns with y values
            if ays==None: #setup ays if not yet done,
                # this will be a list of numpy arrays, for each sample one array,
                # in which rows are data points and columns are x and y
                # zodoende:
                # ays[i][:,0] = x waarden voor staal i
                # ays[i][:,1] = y waarden voor staal i
                ays = [ np.zeros(shape=(0,2)) for i in range(len(data)-1) ]
            for i, y in enumerate(ay):
                # go over each y value and append it to the correct ays together with
                # the x value
                # This way the 2D array is being built
                ays[i] = np.append(ays[i], [[x, y]], axis=0)
        
        if ays:
            for i, ay in enumerate(ays):
                sample_name = "#%s" % i
                try:sample_name = sample_names[i]
                except IndexError: pass
                yield name, sample_name, ay
        
        if close: f.close()
        
    @classmethod
    def write(cls, filename, header, x, ys):
        """
            Writes the header to the first line, and will write x, y1, ..., yn
            rows for each column inside the x and ys arguments.
            Header argument should not include a newline.
        """
        f = open(filename, 'w')
        f.write(u"%s\n" % header)
        np.savetxt(f, np.insert(ys, 0, x, axis=0).transpose(), fmt="%.8f")
        f.close()
        
    pass #end of class
