# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from warnings import warn
import weakref

from mvc import Model, Signal, PropIntel
from pyxrd.generic.utils import not_none, rec_getattr

from .signals import HoldableSignal
import types

class PyXRDModel(Model):
    """
        A UUIDModel with some common PyXRD functionality
    """

    class Meta(Model.Meta):
        properties = []
        pass # end of class

    def pop_kwargs(self, kwargs, *keys):
        popped = {}
        for key in keys:
            popped[key] = kwargs.pop(key, None)
        return popped

    def get_kwarg(self, fun_kwargs, default, *keywords):
        """
        Convenience function to get a certain keyword 'kw' value from the passed
        keyword arguments 'fun_kwargs'. If the key 'kw' is not in 'fun_kwargs'
        a list of deprecated keywords to be searched for can be passed as an
        optional argument list 'depr_kws'. If one of these is found, its value
        is returned and a deprecation warning is emitted. 
        If neither the 'kw' nor any of the 'depr_kws' are found the 'default'
        value is returned. 
        """
        if len(keywords) < 1:
            raise AttributeError, "get_kwarg() requires at least one keyword (%d given)" % (len(keywords))

        value = default
        for i, key in enumerate(keywords[::-1]):
            if key in fun_kwargs:
                value = not_none(fun_kwargs[key], default)
                if i != 0:
                    warn("The use of the keyword '%s' is deprecated for %s!" %
                        (key, type(self)), DeprecationWarning)
        return value

    def get_list(self, fun_kwargs, default, *keywords, **kwargs):
        """
            Convenience function to get a 'list' type keyword. Supports
            deprecated serialized ObjectListStores (replaced by regular lists).
        """
        return self.parse_list(self.get_kwarg(fun_kwargs, default, *keywords), **kwargs)

    def parse_list(self, list_arg, **kwargs):
        """
            Parses a list keyword argument (be it an actual list, or a
            former JSON-serialized ObjectListStore object).
        """
        if isinstance(list_arg, dict) and "type" in list_arg:
            list_arg = list_arg["properties"]["model_data"]
        if list_arg is not None:
            return [
                self.parse_init_arg(json_obj, None, child=True, **kwargs)
                for json_obj in list_arg
             ]
        else:
            return list()

    pass # end of class

class ChildModel(PyXRDModel):
    """
        A PyXRDModel with child-parent relation support.
        Additionally, if you have properties that can actually be 'inherited'
        from their parent, it provides two functions to facilitate this:
            - '_get_inheritable_property_value'
            - '_get_uninherited_property_value'
    """

    # MODEL INTEL:
    class Meta(PyXRDModel.Meta):
        properties = [
            PropIntel(name="parent", data_type=object, storable=False),
            PropIntel(name="removed", data_type=object, storable=False),
            PropIntel(name="added", data_type=object, storable=False),
        ]

    # SIGNALS:
    removed = None
    added = None

    # PROPERTIES:

    __parent = None
    @property
    def parent(self):
        if callable(self.__parent):
            return self.__parent()
        else:
            return self.__parent
    @parent.setter
    def parent(self, value):
        if not self.parent == value:
            if self.parent is not None:
                self.removed.emit()
            try:
                self.__parent = weakref.ref(value, self.__on_parent_finalize)
            except TypeError:
                self.__parent = value
            if self.parent is not None:
                self.added.emit()

    def __on_parent_finalize(self, ref):
        self.removed.emit()
        self.__parent = None

    def __init__(self, parent=None, *args, **kwargs):
        super(ChildModel, self).__init__(*args, **kwargs)
        self.removed = Signal()
        self.added = Signal()
        self.parent = parent

    def get_uninherited_property_value(self, prop):
        """
            Gets the 'private' value for the given attribute name
            from the object, by-passing the regular inheritance rules.
        """
        if prop.inh_name is not None:
            return self._get_inheritable_property_value(prop.name, apply_inheritance=False)
        else:
            return getattr(self, prop.name)

    def _get_inheritable_property_value(self, prop, apply_inheritance=True):
        """
            Gets either the own or the inherited value for the given attribute 
            name or PropIntel object, applying the inheritance rules if the keyword 
            'apply_inheritance' is True.
        """
        if isinstance(prop, types.StringTypes):
            prop = self.Meta.get_prop_intel_by_name(prop)
        inh_from = self._get_inherit_from(prop)
        if apply_inheritance and self._is_inheritable(prop) and inh_from is not None:
            return getattr(inh_from, prop.name)
        else:
            return getattr(self, prop.get_private_name())

    def _get_inherit_from(self, prop):
        if isinstance(prop, types.StringTypes):
            prop = self.Meta.get_prop_intel_by_name(prop)
        if prop.inh_from is not None:
            return rec_getattr(self, prop.inh_from, None)
        else:
            return None

    def _is_inheritable(self, prop):
        if isinstance(prop, types.StringTypes):
            prop = self.Meta.get_prop_intel_by_name(prop)
        return prop.inh_name is not None and getattr(self, prop.inh_name, False)

    pass # end of class

class DataModel(ChildModel):
    """
        A ChildModel with support for having 'calculation data' and 'visual data'            
    """
    class Meta(ChildModel.Meta):
        properties = [
           PropIntel(name="data_changed", storable=False),
           PropIntel(name="visuals_changed", storable=False),
       ]

    # SIGNALS:
    data_changed = None
    visuals_changed = None

    def __init__(self, *args, **kwargs):
        super(DataModel, self).__init__(*args, **kwargs)
        self.data_changed = HoldableSignal()
        self.visuals_changed = HoldableSignal()

    pass # end of class
