# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#
#  mvc is a framework derived from the original pygtkmvc framework
#  hosted at: <http://sourceforge.net/projects/pygtkmvc/>
#
#  mvc is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  mvc is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor,
#  Boston, MA 02110, USA.
#  -------------------------------------------------------------------------

class LabeledProperty(object):
    """
     A property descriptor base class
     Expects it's label to be set or passed to __init__.
    """

    label = None

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, default=None, label=None):
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
            prop = instance.Meta.get_prop_intel_by_name(self.label)
            if instance._is_inheritable(prop):
                inh_from = instance._get_inherit_from(prop)
                if inh_from is not None:
                    return getattr(inh_from, self.label, self.default)
            return getattr(instance, prop.get_private_name(), self.default)
        else:
            return self.fget(instance)

    def __set__(self, instance, value):
        if self.fset is None:
            prop = instance.Meta.get_prop_intel_by_name(self.label)
            setattr(instance, prop.get_private_name(), value)
        else:
            return self.fset(instance, value)

    def __delete__(self, instance):
        if self.fdel is None:
            raise AttributeError, "can't delete attribute"
        self.fdel(instance)
