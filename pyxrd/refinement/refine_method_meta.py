# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from .refine_method_option import RefineMethodOption

class RefineMethodMeta(type):
    """
        The metaclass for creating a RefineMethod (sub)class
        Will register the class type so we can build a list of RefineMethod 
        classes dynamically.
        If the (sub)class does not want to be registered, it should set
        the 'disabled' class attribute to True.
    """
    registered_methods = {}

    def __new__(meta, name, bases, class_dict):  # @NoSelf
        options = []
        for name, value in class_dict.iteritems():
            if isinstance(value, RefineMethodOption):
                options.append(name)
                setattr(value, 'label', name)
        class_dict['options'] = options

        cls = type.__new__(meta, name, bases, class_dict)

        if not getattr(cls, 'disabled', False):
            meta.registered_methods[getattr(cls, 'index')] = cls

        return cls

    pass #end of class
