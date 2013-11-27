# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from warnings import warn

from pyxrd.gtkmvc.model_mt import ModelMT
from pyxrd.gtkmvc.support.propintel import PropIntel
from pyxrd.gtkmvc.support.metaclasses import UUIDMeta
from pyxrd.gtkmvc.model import Signal

from pyxrd.generic.models.signals import HoldableSignal
from pyxrd.generic.utils import not_none

class PyXRDModel(ModelMT):
    """
       Standard model for PyXRD models, with support for refinable properties.
    """

    __metaclass__ = UUIDMeta
    class Meta(ModelMT.Meta):
        properties = [
           PropIntel(name="uuid", data_type=str, storable=True, observable=False),
       ]

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
        if isinstance(list_arg, dict) and "type" in list_arg:
            list_arg = list_arg["properties"]["model_data"]
        if list_arg is not None:
            return [
                self.parse_init_arg(json_obj, None, child=True, **kwargs)
                for json_obj in list_arg
             ]
        else:
            return list()

    def __init__(self, *args, **kwargs):
        super(PyXRDModel, self).__init__(*args, **kwargs)

    def get_base(self, attr):
        intel = self.Meta.get_prop_intel_by_name(attr)
        if intel.inh_name is not None:
            return getattr(self, "_%s" % attr)
        else:
            return getattr(self, attr)

    pass # end of class

class ChildModel(PyXRDModel):
    """
        A PyXRDModel with child-parent relation support.
    """

    # MODEL INTEL:
    class Meta(PyXRDModel.Meta):
        parent_alias = None
        properties = [
            PropIntel(name="parent", data_type=object, storable=False),
            PropIntel(name="removed", data_type=object, storable=False),
            PropIntel(name="added", data_type=object, storable=False),
        ]

    # SIGNALS:
    removed = None
    added = None

    # PROPERTIES:
    _parent = None
    def get_parent(self): return self._parent
    def set_parent(self, value):
        if value != self._parent:
            self._unattach_parent()
            self._parent = value
            self._attach_parent()

    def __init__(self, parent=None, *args, **kwargs):
        super(ChildModel, self).__init__()
        self.removed = Signal()
        self.added = Signal()

        if self.Meta.parent_alias is not None:
            setattr(self.__class__, self.Meta.parent_alias, property(lambda self: self.parent))
        self.parent = parent

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def _unattach_parent(self):
        if self.parent is not None:
            self.removed.emit()

    def _attach_parent(self):
        if self.parent is not None:
            self.added.emit()

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
