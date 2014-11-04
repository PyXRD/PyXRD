# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#  Copyright (C) 2005 by Tobias Weber
#  Copyright (C) 2005 by Roberto Cavada <roboogle@gmail.com>
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

from .base import ObsWrapperBase

class ObsWrapper (ObsWrapperBase):
    """
    Base class for wrappers, like user-classes and sequences. 
    """

    def __init__(self, obj, method_names):
        ObsWrapperBase.__init__(self)

        self._obj = obj
        self.__doc__ = obj.__doc__

        # Creates a derived class which is a singleton which self is
        # going to be an instance of. All method_names are then
        # wrapped within it.
        # See http://stackoverflow.com/questions/1022499/emulating-membership-test-in-python-delegating-contains-to-contained-object
        d = dict((name, self.__get_wrapper(name)) for name in method_names)
        self.__class__ = type(self.__class__.__name__, (self.__class__,), d)
        return

    def __get_wrapper(self, name):
        def _wrapper_fun(self, *args, **kwargs):
            self._notify_method_before(self._obj, name, args, kwargs)
            res = getattr(self._obj, name)(*args, **kwargs)
            self._notify_method_after(self._obj, name, res, args, kwargs)
            return res
        return _wrapper_fun

    # For all fall backs
    def __getattr__(self, name): return getattr(self._obj, name)
    def __repr__(self): return self._obj.__repr__()
    def __str__(self): return self._obj.__str__()

    pass # end of class
