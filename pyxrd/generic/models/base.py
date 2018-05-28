# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import weakref
from warnings import warn

from mvc import Model
from mvc.models.properties import LabeledProperty, SignalProperty
from mvc.support.utils import pop_kwargs, not_none

class PyXRDModel(Model):
    """
        A UUIDModel with some common PyXRD functionality
    """

    class Meta(Model.Meta):
        @classmethod
        def get_refinable_properties(cls):
            if not hasattr(cls, "all_properties"):
                raise RuntimeError("Meta class '%s' has not been initialized" \
                    " properly: 'all_properties' is not set!" % type(self))
            else:
                return [attr for attr in cls.all_properties if getattr(attr, "refinable", False)]

        pass # end of class

    # ------------------------------------------------------------
    #      Methods & functions
    # ------------------------------------------------------------
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
            raise AttributeError("get_kwarg() requires at least one keyword (%d given)" % (len(keywords)))

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
    """

    # MODEL INTEL:
    class Meta(PyXRDModel.Meta):

        @classmethod
        def get_inheritable_properties(cls): # TODO MOVE THIS TO THE CHILD MODEL!!
            if not hasattr(cls, "all_properties"):
                raise RuntimeError("Meta class '%s' has not been initialized" \
                    " properly: 'all_properties' is not set!" % type(cls))
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
