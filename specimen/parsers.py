# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, struct

from generic.io.file_parsers import BaseParser, BaseCSVParser, register_parser, create_group_parser
from generic.controllers.utils import get_case_insensitive_glob
from generic.utils import u

################################################################################
#   xrd namespace parsers:
################################################################################

@register_parser()
class DATParser(BaseCSVParser):
    """
        ASCII *.DAT format parser
    """

    namespace = "xrd"
    extensions  = get_case_insensitive_glob("*.DAT")
        
    pass #end of class
    
@register_parser()
class RDParser(BaseParser):
    """
        Philips Binary *.RD format parser
    """

    description = "Phillips Binary Data"
    namespace = "xrd"
    extensions  = get_case_insensitive_glob("*.RD")
    mimetypes   = ["application/octet-stream",]

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
        if f!= None:
            f.seek(146)
            sample_name = u(str(f.read(16)).replace("\0", ""))
            name = u(os.path.basename(filename))
            yield name, sample_name, cls.parse(f)
    
        if close: f.close()
        
    pass #end of class
    
XRDParser = create_group_parser("XRDParser", RDParser, DATParser, namespace="xrd")

################################################################################
#   exc namespace parsers:
################################################################################

@register_parser()
class EXCParser(BaseCSVParser):
    """
        Exclusion range file parser
    """
    
    description = "Exclusion range file"
    namespace = "exc"
    extensions  = get_case_insensitive_glob("*.EXC")
        
    pass #end of class
