# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, struct

import numpy as np

from generic.io.file_parsers import BaseParser, register_parser
from generic.controllers.utils import get_case_insensitive_glob
from generic.utils import u

from .xrd_parser_mixin import XRDParserMixin

@register_parser()
class RDParser(XRDParserMixin, BaseParser):
    """
        Philips Binary *.RD format parser
    """

    description = "Phillips Binary *.RD"
    namespace = "xrd"
    extensions  = get_case_insensitive_glob("*.RD")
    mimetypes   = ["application/octet-stream",]

    __file_mode__ = "rb"

    @classmethod
    def parse_header(cls, filename, f=None, data_objects=None, close=False):
        filename, f, close = cls._get_file(filename, f=f, close=close)

        # Adapt XRDFile list
        data_objects = cls._adapt_data_object_list(data_objects, num_samples=1)
           
        # Go to the start of the file
        f.seek(0)
        
        # Read file format version:
        version = str(f.read(2))
           
        if version=="V3":
            #Read wavelength information:        
            f.seek(94)
            alpha1, alpha2, alpha_factor = struct.unpack("ddd", f.read(24))
            #Read sample name:
            f.seek(146)
            sample_name = u(str(f.read(16)).replace("\0", ""))

            #Read data limits:
            f.seek(214)
            twotheta_step, twotheta_min, twotheta_max = struct.unpack("ddd", f.read(24))
            twotheta_count = int((twotheta_max - twotheta_min) / twotheta_step)

            data_objects[0].update(
                filename=u(os.path.basename(filename)),
                name=sample_name,
                twotheta_min=twotheta_min,
                twotheta_max=twotheta_max,
                twotheta_step=twotheta_step,
                twotheta_count=twotheta_count,
                alpha1=alpha1,
                alpha2=alpha2,
                alpha_factor=alpha_factor,
                version=version
            )            
        else:
            raise IOError, "Only V3 *.RD files are supported!"
        
        if close: f.close()
        return data_objects
    
    @classmethod
    def parse_data(cls, filename, f=None, data_objects=None, close=False):
        filename, f, close = cls._get_file(filename, f=f, close=close)
                
        data_objects = cls.parse_header(filename, f=f, data_objects=data_objects)
        
        #RD files are singletons, so no need to iterate over the list,
        #there is only one XRDFile instance:
        if data_objects[0].data == None:
            data_objects[0].data = []
            
        #Parse data:
        if f != None:
            if data_objects[0].version=="V3":
                f.seek(250)
                n = 0
                while n < data_objects[0].twotheta_count:
                    y, = struct.unpack("H", f.read(2))
                    data_objects[0].data.append([
                        data_objects[0].twotheta_min + data_objects[0].twotheta_step*float(n + 0.5),
                        float(y)
                    ])
                    n += 1
            else:
                raise IOError, "Only V3 *.RD files are supported!"
                    
        data_objects[0].data = np.array(data_objects[0].data)
                    
        if close: f.close()
        return data_objects
        
    pass #end of class
