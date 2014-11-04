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

from ..decorators import good_classmethod_decorator
from .base import ObsWrapperBase

class Observable (ObsWrapperBase):

    @classmethod
    @good_classmethod_decorator
    def observed(cls, _func):
        """
        Decorate methods to be observable. If they are called on an instance
        stored in a property, the model will emit before and after
        notifications.
        """

        def wrapper(*args, **kwargs):
            self = args[0]
            assert(isinstance(self, Observable))

            self._notify_method_before(self, _func.__name__, args, kwargs)
            res = _func(*args, **kwargs)
            self._notify_method_after(self, _func.__name__, res, args, kwargs)
            return res

        return wrapper

    pass # end of class