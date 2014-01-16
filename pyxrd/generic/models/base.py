# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from warnings import warn
import weakref

from pyxrd.mvc import Model, Signal, PropIntel
from pyxrd.generic.utils import not_none

from .signals import HoldableSignal

class PyXRDModel(Model):
    """
        A UUIDModel with some common PyXRD functionality
    """

    class Meta(Model.Meta):
        properties = []
        pass # end of class

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
        super(ChildModel, self).__init__()
        self.removed = Signal()
        self.added = Signal()
        self.parent = parent

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
