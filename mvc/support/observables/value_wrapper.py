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

from mvc.support.utils import not_none

class ValueWrapper(object):

    wrappers = []

    @staticmethod
    def register_wrapper(cls=None, position=None):
        """
            Decorator that can be applied to wrapper classes (need to 
            define a wrap_value(label, value, model=None) method).
            Can also be called with a position keyword argument to
            force that wrapper to be at a certain position in the list of
            wrappers.
            Otherwise appends the wrapper to the end of wrapper list.
        """
        def inner(cls, position=None):
            position = not_none(position, len(ValueWrapper.wrappers))
            ValueWrapper.wrappers.insert(position, cls.wrap_value)
        if cls == None:
            return inner
        else:
            return inner(cls, position=position)

    @staticmethod
    def wrap_value(label, val, model=None, verbose=False):
        """This is used to wrap a value to be assigned to a
        property. Depending on the type of the value, different values
        are created and returned. For example, for a list, a
        ListWrapper is created to wrap it, and returned for the
        assignment. model is different from None when the value is
        changed (a model exists). Otherwise, during property creation
        model is None"""

        for wrapper in ValueWrapper.wrappers:
            wrapped = wrapper(label, val, model)
            if wrapped is None:
                continue
            else:
                return wrapped

        return val

    pass #end of class
