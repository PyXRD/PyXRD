# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import types
import weakref
from warnings import warn

from mvc import Model
from mvc.models.properties import LabeledProperty, SignalProperty
from mvc.support.utils import pop_kwargs, not_none
from pyxrd.generic.utils import rec_getattr

class PyXRDModel(Model):
    """
        A UUIDModel with some common PyXRD functionality
    """

    class Meta(Model.Meta):
        @classmethod
        def get_refinable_properties(cls):
            if not hasattr(cls, "all_properties"):
                raise RuntimeError, "Meta class '%s' has not been initialized" \
                    " properly: 'all_properties' is not set!" % type(self)
            else:
                return [attr for attr in cls.all_properties if getattr(attr, "refinable", False)]

        pass # end of class

    def pop_kwargs(self, kwargs, *keys):
        return pop_kwargs(kwargs, *keys)

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

class InheritableMixin(object):
    """
        A mixin class providing functionality for inheritable properties. 
    """

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

class ChildModel(InheritableMixin, PyXRDModel):
    """
        A PyXRDModel with child-parent relation support.
        Additionally, if you have properties that can actually be 'inherited'
        from their parent, it provides two functions to facilitate this:
            - '_get_inheritable_property_value'
            - '_get_uninherited_property_value'
    """

    # MODEL INTEL:
    class Meta(PyXRDModel.Meta):

        @classmethod
        def get_inheritable_properties(cls): # TODO MOVE THIS TO THE CHILD MODEL!!
            if not hasattr(cls, "all_properties"):
                raise RuntimeError, "Meta class '%s' has not been initialized" \
                    " properly: 'all_properties' is not set!" % type(cls)
            else:
                return [attr for attr in cls.all_properties if getattr(attr, "inheritable", False)]

    # SIGNALS:
    removed = SignalProperty()
    added = SignalProperty()

    # PROPERTIES:
    __parent = None
    def __get_parent(self):
        if callable(self.__parent):
            return self.__parent()
        else:
            return self.__parent
    def __set_parent(self, value):
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
    parent = LabeledProperty(fget=__get_parent, fset=__set_parent)

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, parent=None, *args, **kwargs):
        super(ChildModel, self).__init__(*args, **kwargs)
        self.parent = parent

    pass # end of class

class DataModel(ChildModel):
    """
        A ChildModel with support for having 'calculation data' and 'visual data'            
    """

    # SIGNALS:
    data_changed = SignalProperty()
    visuals_changed = SignalProperty()

    pass # end of class
