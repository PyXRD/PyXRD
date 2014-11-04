# coding=UTF-8
# ex:ts=4:sw=4:et:
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
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

import weakref

class WeakList(list):
    """
        A list subclass referring to its items using weak references if possible 
    """
    
    def __init__(self, items=list()):
        list.__init__(self)
        tuple(map(self.append, items))

    def get_value(self, item):
        try:
            item = item()
        finally:
            return item

    def make_ref(self, item):
        try:
            item = weakref.ref(item, self.remove)
        finally:
            return item

    def __contains__(self, item):
        return list.__contains__(self, self.make_ref(item))

    def __getitem__(self, key):
        if isinstance(key, slice):
            return type(self)(self.get_value(item) for item in list.__getitem__(self, key))
        return self.get_value(list.__getitem__(self, key))

    def __getslice__(self, i, j):
        return self.__getitem__(slice(i, j))

    def __setitem__(self, key, item):
        return list.__setitem__(self, key, self.make_ref(item))

    def __iter__(self):
        return iter([self[key] for key in range(len(self))])

    def append(self, item):
        list.append(self, self.make_ref(item))

    def remove(self, item):
        item = self.make_ref(item)
        while list.__contains__(self, item):
            list.remove(self, item)

    def index(self, item):
        return list.index(self, self.make_ref(item))

    def pop(self, item):
        return list.pop(self, self.make_ref(item))

    pass #end of class
