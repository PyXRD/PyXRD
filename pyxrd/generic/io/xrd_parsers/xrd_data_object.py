# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.generic.io.file_parsers import DataObject

class XRDDataObject(DataObject):
    """
        A generic class holding all the information retrieved from an XRD data
        file using an XRD-parser class.
    """
    
    #general information
    name = None
    date = None
    
    #x-axis range
    twotheta_min = None
    twotheta_max = None
    twotheta_count = None
    twotheta_step = None
    
    #wavelength and target information
    target_type = None
    alpha1 = None
    alpha2 = None
    alpha_average = None
    beta = None
    alpha_factor = None

    #generator or list of x,y data
    data = None
                
    pass #end of class
