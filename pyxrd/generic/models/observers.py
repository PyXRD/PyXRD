# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import weakref
from pyxrd.gtkmvc.model import Observer
import types
from pyxrd.generic.utils import not_none

class ListItemObserver(Observer):
    """
        An observer that observes a single item in a list and informs us of changes.
        The observed properties are defined in the list type's meta class by
        setting their PropIntel 'is_column' attribute to True.
    """

    _previous_model_ref = None
    @property
    def _previous_model(self):
        if self._previous_model_ref is not None:
            return self._previous_model_ref()
        else:
            return None
    @_previous_model.setter
    def _previous_model(self, value):
        self._previous_model_ref = weakref.ref(value, self.clear)

    def __init__(self, on_changed, model=None, spurious=False):
        super(ListItemObserver, self).__init__(spurious=spurious)
        self.on_changed = on_changed
        self.observe_model(model)

    def observe_model(self, model):
        if self._previous_model is not None:
            self.relieve_model(self._previous_model)
        if model is not None:
            for prop_name, data_type in model.Meta.get_column_properties():  # @UnusedVariable
                self.observe(self.on_prop_mutation, prop_name, assign=True)
            self._previous_model = model
            super(ListItemObserver, self).observe_model(model)

    def clear(self, *args):
        self.on_changed = None
        if len(args) == 0:
            self.observe_model(None)

    def on_prop_mutation(self, model, prop_name, info):
        if callable(self.on_changed):
            self.on_changed(model)

    pass # end of class

class ListObserver(Observer):
    """
        An observer that wraps the in-instance changes of a list to on_inserted
        and on_deleted handlers.
    """

    _deleted = []

    def __init__(self, on_inserted, on_deleted, prop_name, on_deleted_before=None, model=None, spurious=False):
        super(ListObserver, self).__init__(spurious=spurious)
        self.on_inserted = on_inserted
        self.on_deleted = on_deleted
        self.on_deleted_before = on_deleted_before

        self.observe(self.on_prop_mutation_before, prop_name, before=True)
        self.observe(self.on_prop_mutation_after, prop_name, after=True)
        self.observe_model(model)

    def on_prop_mutation_before(self, model, prop_name, info):
        if info.method_name in ("__setitem__", "__delitem__"):
            i = info.args[0]
            if isinstance(i, types.SliceType):
                self._deleted = info.instance[i]
            elif i <= len(info.instance): # setting an existing item: need a on_delete as well
                self._deleted = [info.instance[i], ]
        if info.method_name == "pop":
            if len(info.instance) > 0:
                self._deleted = [info.instance[-1], ]
        if info.method_name == "remove":
            self._deleted = [info.args[0], ]

        if callable(self.on_deleted_before):
            for old_item in self._deleted[::-1]:
                self.on_deleted_before(old_item)

    def on_prop_mutation_after(self, model, prop_name, info):
        if callable(self.on_deleted):
            for old_item in self._deleted[::-1]:
                self.on_deleted(old_item)
            self._deleted = []

        if info.method_name == "__setitem__":
            i = info.args[0]
            if type(i) is types.SliceType:
                for item in info.instance[i]:
                    self.on_inserted(item)
            else:
                new_item = info.args[1]
                self.on_inserted(new_item)
        if info.method_name == "append":
            new_item = info.args[0]
            self.on_inserted(new_item)
        if info.method_name == "extend":
            items = info.args[0]
            for new_item in items:
                self.on_inserted(new_item)
        if info.method_name == "insert":
            new_item = info.args[1]
            self.on_inserted(new_item)

    pass # end of class

class DictObserver(Observer):
    """
        An observer that wraps the in-instance changes of a dict to on_inserted
        and on_deleted handlers.
    """

    _deleted = []

    def __init__(self, on_inserted, on_deleted, prop_name, model=None, spurious=False):
        super(DictObserver, self).__init__(model=model, spurious=spurious)
        self.on_inserted = on_inserted
        self.on_deleted = on_deleted

        self.observe(self.on_prop_mutation_before, prop_name, before=True)
        self.observe(self.on_prop_mutation_after, prop_name, after=True)

    def on_prop_mutation_before(self, model, prop_name, info):
        if info.method_name in ("__setitem__", "__delitem__", "pop", "setdefault"):
            key = info.args[0]
            if key in info.instance:
                self._deleted.append(info.instance[key])

        if info.method_name == "update":
            if len(info.args) == 1:
                iterable = info.args[0]
            elif len(info.kwargs) > 0:
                iterable = info.kwargs
            if hasattr(iterable, "iteritems"):
                iterable = iterable.iteritems()
            for key, value in iterable: # @UnusedVariable
                if key in info.instance:
                    self._deleted.append(info.instance[key])

        if info.method_name == "clear":
            self._deleted.extend(info.instances.values())

    def on_prop_mutation_after(self, model, prop_name, info):

        if self._deleted:
            for old_item in self._deleted:
                self.on_deleted(old_item)
            self._deleted = []

        if info.method_name == "popitem":
            old_item = info.result[1]
            self.on_deleted(old_item)

    pass # end of class
