# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import weakref

class WeakList(list):
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
