# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import threading
import multiprocessing

from weakref import WeakValueDictionary

from pyxrd.data import settings
from pyxrd.generic.utils import get_new_uuid

class ObjectPool(object):

    def __init__(self, *args, **kwargs):
        object.__init__(self)
        self._objects = WeakValueDictionary()

    def add_or_get_object(self, obj):
        try:
            self.add_object(obj, force=False, silent=False)
            return obj
        except KeyError:
            return self.get_object(obj.uuid)

    def add_object(self, obj, force=False, fail_on_duplicate=False):
        if not obj.uuid in self._objects or force:
            self._objects[obj.uuid] = obj
        elif fail_on_duplicate:
            raise KeyError, "UUID %s is already taken by another object %s, cannot add object %s" % (obj.uuid, self._objects[obj.uuid], obj)
        else:
            # Just change the objects uuid, will break refs, but
            # it prevents issues with inherited properties etc.
            if settings.DEBUG:
                print "A duplicate UUID was passed to an ObjectPool for a %s object." % obj
            obj.uuid = get_new_uuid()

    def change_all_uuids(self):
        # first get a copy of all objects & uuids:
        items = self._objects.items()
        for uuid, obj in items: # @UnusedVariable
            obj.uuid = get_new_uuid()

    def remove_object(self, obj):
        if obj.uuid in self._objects and self._objects[obj.uuid] == obj:
            del self._objects[obj.uuid]

    def get_object(self, uuid):
        obj = self._objects.get(uuid, None)
        return obj 

    def clear(self):
        self._objects.clear()

class ThreadedObjectPool(object):

    def __init__(self, *args, **kwargs):
        object.__init__(self)
        self.pools = {}

    def clean_pools(self):
        for ptkey in self.pools.keys():
            if (ptkey == (None, None) or not ptkey[0].is_alive() or not ptkey[1].is_alive()):
                del self.pools[ptkey] # clear this sucker

    def get_pool(self):
        process = multiprocessing.current_process()
        thread = threading.current_thread()
        pool = self.pools.get((process, thread), ObjectPool())
        self.pools[(process, thread)] = pool
        return pool

    def add_or_get_object(self, *args, **kwargs):
        pool = self.get_pool()
        return pool.add_or_get_object(*args, **kwargs)

    def add_object(self, *args, **kwargs):
        pool = self.get_pool()
        return pool.add_object(*args, **kwargs)

    def change_all_uuids(self, *args, **kwargs):
        pool = self.get_pool()
        return pool.change_all_uuids(*args, **kwargs)

    def remove_object(self, *args, **kwargs):
        pool = self.get_pool()
        return pool.remove_object(*args, **kwargs)

    def get_object(self, *args, **kwargs):
        pool = self.get_pool()
        return pool.get_object(*args, **kwargs)

    def clear(self, *args, **kwargs):
        pool = self.get_pool()
        return pool.clear(*args, **kwargs)

    pass # end of class
