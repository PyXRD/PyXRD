# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, struct

from generic.io.file_parsers import ASCIIParser, register_parser
from generic.controllers.utils import get_case_insensitive_glob
from generic.utils import u

import numpy as np

################################################################################
#   exc namespace parsers:
################################################################################

@register_parser()
class EXCParser(ASCIIParser):
    """
        Exclusion range file parser
    """
    
    #        TODO FIXME
    
    description = "Exclusion range file"
    namespace = "exc"
    extensions  = get_case_insensitive_glob("*.EXC")
        
    pass #end of class
