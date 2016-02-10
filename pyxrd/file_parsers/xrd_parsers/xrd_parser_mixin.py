# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from .xrd_data_object import XRDDataObject

class XRDParserMixin(object):
    """
        This is a mixin class which provides common functionality and attributes
        for XRD-data parser classes.
    """

    data_object_type = XRDDataObject

    pass #end of class
