# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.


#
# If we register a parser it should include:
# - information on the extensions this format can have as included in the controllers
# - a general name (crf above)
#

import os, sys, struct

import numpy as np
import gtk

from generic.controllers.utils import get_case_insensitive_glob
from generic.utils import u

parsers = [] # list of subclasses

class BaseParser(object):

    #This should be changed by sub-classes    
    description = ""
    extensions  = []
    
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
            raise TypeError, "Wrong data type supplied for %s format, \
                must be either file or string, but %s was given" % (cls.description, type(data))
    
    @classmethod
    def parse(cls, data):
        #This should be implemented by sub-classes
        raise NotImplementedError

    class __metaclass__(type):
        def __init__(cls, name, bases, dict):
            type.__init__(cls, name, bases, dict)
            
            #Init file filter:
            cls.file_filter = gtk.FileFilter() 
            cls.file_filter.set_name(cls.description)
            for expr in cls.extensions:
                cls.file_filter.add_pattern(expr)  
            cls.file_filter.set_data("parser", cls)  
            
            #Register parser:
            if name!="BaseParser":
                parsers.append(cls)
    
    pass #end of class


class DATParser(BaseParser):

    #TODO add more options for CSV files (separator, decimal field, ...)

    description = "ASCII data"
    extensions  = get_case_insensitive_glob("*.DAT")
    
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
            x, ay = data[0], data[1:]
            if ays==None:
                ays = [ np.zeros(shape=(0,2)) for i in range(len(data)-1) ]
            for i, y in enumerate(ay):
                ays[i] = np.append(ays[i], [[x, y]], axis=0) #ays[0][:,1] = y waarden
        
        if ays:
            for i, ay in enumerate(ays):
                sample_name = "#%s" % i
                try:sample_name = sample_names[i]
                except IndexError: pass
                yield name, sample_name, ay
    
        if close: f.close()
         
    pass #end of class
    
class RDParser(BaseParser):

    description = "Phillips Binary Data"
    extensions  = get_case_insensitive_glob("*.RD")

    __file_mode__ = "rb"

    @classmethod
    def parse(cls, data):
        close, f = cls._get_file(data)
        if f != None:
            #seek data limits
            f.seek(214)
            stepx, minx, maxx = struct.unpack("ddd", f.read(24))
            nx = int((maxx-minx)/stepx)
            #read values                          
            f.seek(250)
            n = 0
            while n < nx:
                y, = struct.unpack("H", f.read(2))
                yield minx + stepx*n, float(y)
                n += 1

        if close: f.close()
        
    @classmethod     
    def multi_parse(cls, filename):
        close, f = cls._get_file(filename)
                
        f.seek(146)
        sample_name = u(str(f.read(16)).replace("\0", ""))
        name = u(os.path.basename(filename))
        yield name, sample_name, cls.parse(f)
    
        if close: f.close()
        
    pass #end of class        
