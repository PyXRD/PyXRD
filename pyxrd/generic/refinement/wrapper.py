# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.generic.models.base import ChildModel

from pyxrd.generic.refinement.mixins import _RefinementBase, RefinementValue, RefinementGroup
from pyxrd.gtkmvc.support.propintel import PropIntel

class RefinableWrapper(ChildModel):
    """
        Wrapper class for refinables easing the retrieval of certain
        properties for the different types of refinables.
        Can be used with an ObjectTreeStore.
    """

    # MODEL INTEL:
    class Meta(ChildModel.Meta):
        parent_alias = "mixture"
        properties = [ # TODO add labels
            PropIntel(name="title", label="", is_column=True, data_type=str, has_widget=True),
            PropIntel(name="refine", label="", is_column=True, data_type=bool, has_widget=True),
            PropIntel(name="refinable", label="", is_column=True, data_type=bool),
            PropIntel(name="prop", label="", is_column=True, data_type=str, has_widget=True),
            PropIntel(name="inh_prop", label="", is_column=True, data_type=str, has_widget=True),
            PropIntel(name="value", label="", is_column=True, data_type=float),
            PropIntel(name="value_min", label="", is_column=True, data_type=float, has_widget=True),
            PropIntel(name="value_max", label="", is_column=True, data_type=float, has_widget=True),
            PropIntel(name="obj", label="", is_column=True, data_type=object),
            PropIntel(name="prop_intel", label="", is_column=True, data_type=object)
        ]

    # PROPERTIES:
    obj = None

    # The PropIntel object of the refinable property
    _prop_intel = None
    def get_prop_intel(self):
        if isinstance(self.obj, _RefinementBase) and self.prop == None:
            return None
        else:
            if not self._prop_intel:
                self._prop_intel = self.obj.Meta.get_prop_intel_by_name(self.prop)
            return self._prop_intel

    # The attribute name:
    _prop = ""
    def get_prop(self):
        return self._prop
    def set_prop(self, value):
        self._prop = value

    # The inherit attribute name:
    def get_inh_prop(self):
        return self.prop_intel.inh_name if self.prop_intel else None

    # The label for the refinable property:
    def get_title(self):
        if isinstance(self.obj, _RefinementBase) and self.prop_intel == None:
            return self.obj.refine_title
        else:
            return self.prop_intel.label

    # The actual value of the refinable property:
    def get_value(self):
        if isinstance(self.obj, RefinementValue):
            return self.obj.refine_value
        elif self.prop != None:
            return getattr(self.obj, self.prop)
        else:
            return None
    def set_value(self, value):
        value = max(min(value, self.value_max), self.value_min)
        if isinstance(self.obj, RefinementValue):
            self.obj.refine_value = value
        else:
            setattr(self.obj, self.prop, value)

    # Wether or not this property is inherited from another object
    @property
    def inherited(self):
        return self.inh_prop != None and hasattr(self.obj, self.inh_prop) and getattr(self.obj, self.inh_prop)

    # Wether or not this property is actually refinable
    @property
    def refinable(self):
        if isinstance(self.obj, RefinementGroup) and self.prop_intel != None:
            return self.obj.children_refinable and not self.inherited
        if isinstance(self.obj, _RefinementBase) and self.prop_intel == None:
            return self.obj.is_refinable
        else:
            return (not self.inherited)

    # The refinement info object for the refinable property
    @property
    def ref_info(self):
        name = self.prop_intel.name if self.prop_intel else self.prop
        if hasattr(self.obj, "%s_ref_info" % name):
            return getattr(self.obj, "%s_ref_info" % name)
        elif isinstance(self.obj, _RefinementBase) and self.prop_intel == None:
            return self.obj.refine_info

    # The minimum value for the refinable property
    def get_value_min(self):
        return self.ref_info.minimum if self.ref_info else None
    def set_value_min(self, value):
        if self.ref_info:
            self.ref_info.minimum = value

    # The maximum value of the refinable property
    def get_value_max(self):
        return self.ref_info.maximum if self.ref_info else None
    def set_value_max(self, value):
        if self.ref_info:
            self.ref_info.maximum = value

    # Wether this property is selected for refinement:
    def get_refine(self):
        return self.ref_info.refine if self.ref_info else False
    def set_refine(self, value):
        if self.ref_info:
            self.ref_info.refine = value and self.refinable

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for a RefinableWrapper are:
                obj: the object we are wrapping a parameter for
                prop: the property name of the parameter on the object
        """
        super(RefinableWrapper, self).__init__(**kwargs)

        self.obj = self.get_kwarg(kwargs, None, "obj")
        self.prop = self.get_kwarg(kwargs, None, "prop")

    pass # end of class
