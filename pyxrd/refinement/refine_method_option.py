# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

class RefineMethodOption(object):
    """ Descriptor for refinement methods """
    # TODO MERGE THIS WITH THE DESCRIPTORS FROM THE OTHER BRANCH

    label = None

    def __init__(self, description, default=None, limits=[None, None], value_type=object, fget=None, fset=None, fdel=None, doc=None, label=None):
        self.description = description
        self.limits = limits
        self.value_type = value_type

        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

        self.label = label
        self.default = default

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.fget is None:
            return getattr(instance, "_%s" % self.label, self.default)
        else:
            return self.fget(instance)

    def __set__(self, instance, value):
        _min, _max = self.limits
        if self.value_type in (str, int, float): value = self.value_type(value)
        if _min is not None: value = max(value, _min)
        if _max is not None: value = min(value, _max)

        if self.fset is None:
            setattr(instance, "_%s" % self.label, value)
        else:
            return self.fset(instance, value)

    def __delete__(self, instance):
        if self.fdel is None:
            raise AttributeError, "can't delete attribute"
        self.fdel(instance)

    pass # end of class
