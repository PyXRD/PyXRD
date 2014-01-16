# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

class IndexProperty(object):
    """decorator used to create indexable properties (e.g. W[1,1])"""

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        if doc is None and fget is not None and hasattr(fget, "__doc__"):
            doc = fget.__doc__
        self._get = fget
        self._set = fset
        self._del = fdel
        self.__doc__ = doc

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return BoundIndexProperty(self, instance)

    def __set__(self, instance, value):
        raise AttributeError, "can't set attribute"

    def __delete__(self, instance):
        raise AttributeError, "can't delete attribute"

    def getter(self, fget):
        return IndexProperty(fget, self._set, self._del, self.__doc__)

    def setter(self, fset):
        return IndexProperty(self._get, fset, self._del, self.__doc__)

    def deleter(self, fdel):
        return IndexProperty(self._get, self._set, fdel, self.__doc__)

class BoundIndexProperty(object):

    def __init__(self, item_property, instance):
        self.__item_property = item_property
        self.__instance = instance

    def __getitem__(self, key):
        fget = self.__item_property._get
        if fget is None:
            raise AttributeError, "unreadable attribute item"
        return fget(self.__instance, key)

    def __setitem__(self, key, value):
        fset = self.__item_property._set
        if fset is None:
            raise AttributeError, "can't set attribute item"
        fset(self.__instance, key, value)

    def __delitem__(self, key):
        fdel = self.__item_property._del
        if fdel is None:
            raise AttributeError, "can't delete attribute item"
        fdel(self.__instance, key)
