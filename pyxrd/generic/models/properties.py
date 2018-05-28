# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from mvc.models.properties.observe_mixin import ObserveMixin

from mvc.support.utils import rec_getattr

class ObserveChildMixin(ObserveMixin):
    """
    A descriptor mixin that will make the instance observe and relieve the
    objects set and clear and set the parent property on the old and new object respectively
    """

    def __relieve_old(self, instance, old, new):
        if old is not None:
            instance.relieve_model(old)
            old.parent = None

    def __observe_new(self, instance, old, new):
        if new is not None:
            new.parent = instance
            instance.observe_model(new)

    pass

class InheritableMixin(object):
    """
    Mixing for the ~:class:`mvc.models.properties.LabeledProperty` descriptor
    that allows the property to be inheritable from another property.
    When this Mixin is used, the user should pass two additional keyword 
    arguments to the descriptor:
        - inheritable: boolean set to True if inheriting should be enabled
        - inherit_flag: dotted string describing where to get the flag 
          indicating the property is inherited yes/no
        - inherit_from: dotted string describing where to get the attribute if
          the inherit_flag is True 
    """

    inheritable = True
    inherit_flag = None
    inherit_from = None

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        value = self.get_uninherited(instance, owner)
        if self.inheritable and rec_getattr(instance, self.inherit_flag, False):
            value = rec_getattr(instance, self.inherit_from, value)
        return value

    def get_uninherited(self, instance, owner=None):
        return super(InheritableMixin, self).__get__(instance, owner)

    pass #end of class

class IndexProperty(object):
    """Descriptor used to create indexable properties (e.g. W[1,1])"""

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
        raise AttributeError("can't set attribute")

    def __delete__(self, instance):
        raise AttributeError("can't delete attribute")

    def getter(self, fget):
        return IndexProperty(fget, self._set, self._del, self.__doc__)

    def setter(self, fset):
        return IndexProperty(self._get, fset, self._del, self.__doc__)

    def deleter(self, fdel):
        return IndexProperty(self._get, self._set, fdel, self.__doc__)

    pass #end of class

class BoundIndexProperty(object):

    def __init__(self, item_property, instance):
        self.__item_property = item_property
        self.__instance = instance

    def __getitem__(self, key):
        fget = self.__item_property._get
        if fget is None:
            raise AttributeError("unreadable attribute item")
        return fget(self.__instance, key)

    def __setitem__(self, key, value):
        fset = self.__item_property._set
        if fset is None:
            raise AttributeError("can't set attribute item")
        fset(self.__instance, key, value)

    def __delitem__(self, key):
        fdel = self.__item_property._del
        if fdel is None:
            raise AttributeError("can't delete attribute item")
        fdel(self.__instance, key)

    pass #end of class
