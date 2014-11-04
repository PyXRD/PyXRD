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
from .obs_wrapper import ObsWrapper

class ObsSeqWrapper (ObsWrapper):
    def __init__(self, obj, method_names):
        ObsWrapper.__init__(self, obj, method_names)

        for _m in "lt le eq ne gt ge len iter".split():
            meth = "__%s__" % _m
            assert hasattr(self._obj, meth), "Not found method %s in %s" % (meth, str(type(self._obj)))
            setattr(self.__class__, meth, getattr(self._obj, meth))
            pass
        return

    def __setitem__(self, key, val):
        self._notify_method_before(self._obj, "__setitem__", (key, val), {})
        res = self._obj.__setitem__(key, val)
        self._notify_method_after(self._obj, "__setitem__", res, (key, val), {})
        return res

    def __delitem__(self, key):
        self._notify_method_before(self._obj, "__delitem__", (key,), {})
        res = self._obj.__delitem__(key)
        self._notify_method_after(self._obj, "__delitem__", res, (key,), {})
        return res

    def __getitem__(self, key):
        return self._obj.__getitem__(key)

    pass # end of class