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

from weakref import WeakValueDictionary
import threading
import multiprocessing
import logging
logger = logging.getLogger(__name__)

from ..support.utils import get_new_uuid

class ObjectPool(object):
    """
        This class allows to fetch mvc model objects using their UUID.
        This requires to model to have a property called "uuid". All
        class inheriting from the base 'Model' class will have this.
        If implementing a custom model, the UUID property is responsible
        for the removal and addition to the pool when it changes values.
        Also see the UUIDPropIntel class for an example implementation.
        We can use this to store complex relations between objects where 
        references to each other can be replaced with the UUID.
        For a multi-threaded version see ThreadedObjectPool. 
    """

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
            logger.warning("A duplicate UUID was passed to an ObjectPool for a %s object." % obj)
            obj.uuid = get_new_uuid()

    def change_all_uuids(self):
        # first get a copy off all uuids & objects:
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
