# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import threading
import multiprocessing

from weakref import WeakValueDictionary

from pyxrd.gtkmvc.support.metaclasses import ObservablePropertyMetaMT

from pyxrd.generic.utils import get_unique_list, get_new_uuid

from pyxrd.data import settings

class PyXRDMeta(ObservablePropertyMetaMT):

    extra_key_names = [
        "storables",
        "columns",
        "inheritables",
        "have_no_widget"
    ]

    # ------------------------------------------------------------
    #      Type initialisation:
    # ------------------------------------------------------------
    def __init__(cls, name, bases, d):
        # get the model intel for this class type (excluding bases for now):
        model_intel = get_unique_list(d.get("__model_intel__", list()))

        # Properties to be generated base on model intel named tuples:
        keys = cls.extra_key_names

        # Loop over the variables and fetch any custom values for this class (if present):
        for key in keys + ["observables", ]:
            key_name = "__%s__" % key
            d[key_name] = get_unique_list(d[key_name]) if key_name in d else list()

        # Add 'new' observables before we update the model intel with values from base classes
        for prop in model_intel:
            name, bases, d = cls.__generate_observables__(name, bases, d, prop)

        # Add model intel from the base classes to generate the remaining
        # properties, without overriding intels already present,
        # replace the variable by a set including the complete model intel for
        # all bases and including modifications arising in this metaclass:
        for base in bases:
            base_intel = getattr(base, "__model_intel__", list())
            for prop in base_intel:
                if not prop in model_intel:
                    model_intel.append(prop)
        setattr(cls, "__model_intel__", get_unique_list(model_intel))

        # Generate remaining properties based on model intel (including bases):
        def dummy(*args):
            return tuple(args[:-1])
        for prop in model_intel:
            for key in keys:
                func = getattr(cls, "__generate_%s__" % key, dummy)
                name, bases, d = func(name, bases, d, prop)

        # apply properties:
        for key in keys + ["observables", ]:
            key_name = "__%s__" % key
            setattr(cls, key_name, list(d[key_name  ]))

        return ObservablePropertyMetaMT.__init__(cls, name, bases, d)

    # ------------------------------------------------------------
    #      Instance creation:
    # ------------------------------------------------------------
    def __call__(cls, *args, **kwargs):
        # Check if uuid has been passed (e.g. when restored from disk)
        # if not, generate a new one
        try:
            uuid = kwargs.pop("uuid")
        except KeyError:
            uuid = get_new_uuid()

        # Create instance:
        instance = ObservablePropertyMetaMT.__call__(cls, *args, **kwargs)

        # Add a reference to the instance for each model intel,
        # so function calls (e.g. labels) work as expected
        for prop_intel in instance.__model_intel__:
            prop_intel.container = instance

        # Set the uuid:
        instance.uuid = uuid

        return instance

    # ------------------------------------------------------------
    #      Other methods & functions:
    # ------------------------------------------------------------

    def set_attribute(cls, d, name, value):
        d[name] = value
        setattr(cls, name, value)

    def del_attribute(cls, d, name):
        del d[name]
        delattr(cls, name)

    def __generate_observables__(cls, name, bases, d, prop):
        # loop over the model intel and generate observables list:
        if prop.observable:
            d["__observables__"].append(prop.name)
        if hasattr(cls, prop.name):
            from properties import MultiProperty
            attr = getattr(cls, prop.name)
            if isinstance(attr, MultiProperty):
                pr_prop = "_%s" % prop.name
                pr_optn = "_%ss" % prop.name
                getter_name = "get_%s_value" % prop.name
                setter_name = "set_%s_value" % prop.name

                cls.set_attribute(d, pr_prop, attr.value)
                cls.set_attribute(d, pr_optn, attr.options)

                existing_getter = getattr(cls, getter_name, None)
                existing_setter = getattr(cls, setter_name, None)

                getter, setter = attr.create_accesors(pr_prop, existing_getter, existing_setter)
                cls.set_attribute(d, getter_name, getter)
                cls.set_attribute(d, setter_name, setter)
                cls.del_attribute(d, prop.name)
        return name, bases, d

    def __generate_storables__(cls, name, bases, d, prop):
        if prop.storable:
            if prop.stor_name != None:
                d["__storables__"].append((prop.name, prop.stor_name))
            else:
                d["__storables__"].append((prop.name, prop.name))
        return name, bases, d

    def __generate_columns__(cls, name, bases, d, prop):
        if prop.is_column:
            # replace unicodes with strs for PyGtk
            data_type = prop.data_type if prop.data_type != unicode else str
            d["__columns__"].append((prop.name, data_type))
        return name, bases, d

    def __generate_inheritables__(cls, name, bases, d, prop):
        if prop.inh_name:   d["__inheritables__"].append(prop.name)
        return name, bases, d

    def __generate_have_no_widget__(cls, name, bases, d, prop):
        if not prop.has_widget: d["__have_no_widget__"].append(prop.name)
        return name, bases, d

    pass # end of class


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
        for uuid, obj in items:
            obj.uuid = get_new_uuid()

    def remove_object(self, obj):
        if obj.uuid in self._objects and self._objects[obj.uuid] == obj:
            del self._objects[obj.uuid]

    def get_object(self, uuid):
        return self._objects.get(uuid, None)

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

pyxrd_object_pool = ThreadedObjectPool()
