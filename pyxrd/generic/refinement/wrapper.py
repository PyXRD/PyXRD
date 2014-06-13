# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from pyxrd.generic.models.base import ChildModel

from pyxrd.generic.refinement.mixins import _RefinementBase, RefinementValue, RefinementGroup
from pyxrd.mvc import PropIntel

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
            PropIntel(name="obj", label="", is_column=True, data_type=object),
            PropIntel(name="is_grouper", label="", is_column=True, data_type=bool),
            PropIntel(name="prop_intel", label="", is_column=True, data_type=object),
            PropIntel(name="prop", label="", is_column=True, data_type=str, has_widget=True),
            PropIntel(name="inh_prop", label="", is_column=True, data_type=str, has_widget=True),
            PropIntel(name="value", label="", is_column=True, data_type=float),
            PropIntel(name="value_min", label="", is_column=True, data_type=float, has_widget=True),
            PropIntel(name="value_max", label="", is_column=True, data_type=float, has_widget=True),
            PropIntel(name="refine", label="", is_column=True, data_type=bool, has_widget=True),
            PropIntel(name="refinable", label="", is_column=True, data_type=bool),
        ]

    # PROPERTIES:
    obj = None

    # The PropIntel object for the attribute
    _prop_intel = None
    def get_prop_intel(self):
        return self._prop_intel
    def set_prop_intel(self, value):
        self._prop_intel = value

    # The attribute name:
    def get_prop(self):
        return self._prop_intel.name

    # A flag indicating whether this is wrapper is representing the group (True) or a member of the group (False):
    _is_grouper = False
    @property
    def is_grouper(self):
        return self._is_grouper

    # The inherit attribute name:
    def get_inh_prop(self):
        return self.prop_intel.inh_name if self.prop_intel else None

    # The (possibly mathtext) label for the refinable property:
    def get_title(self):
        if (isinstance(self.obj, RefinementGroup) and self.is_grouper) or isinstance(self.obj, RefinementValue):
            return self.obj.refine_title
        else:
            if self.prop_intel.math_label is not None:
                return self.prop_intel.math_label
            else:
                return self.prop_intel.label

    # The (pure text) label for the refinable property:
    def get_text_title(self):
        if (isinstance(self.obj, RefinementGroup) and self.is_grouper) or isinstance(self.obj, RefinementValue):
            return self.obj.refine_title
        else:
            return self.prop_intel.label        

    def get_descriptor(self):
        """ Return a longer title that also describes this property's relations """

        # This gets the phase and/or component name for the group or value:
        data = self.obj.refine_descriptor_data

        # Here we still need to get the actual property title:
        data["property_name"] = self.title

        return "%(phase_name)s | %(component_name)s | %(property_name)s" % data

    # The actual value of the refinable property:
    def get_value(self):
        if isinstance(self.obj, RefinementValue):
            return self.obj.refine_value
        elif not self.is_grouper:
            return getattr(self.obj, self.prop)
        else:
            return ""
    def set_value(self, value):
        value = max(min(value, self.value_max), self.value_min)
        if self.is_grouper:
            raise AttributeError, "Cannot set the value for a grouping RefinableWrapper"
        elif isinstance(self.obj, RefinementValue):
            self.obj.refine_value = value
        else:
            setattr(self.obj, self.prop, value)

    # Whether or not this property is inherited from another object
    @property
    def inherited(self):
        return self.inh_prop is not None and hasattr(self.obj, self.inh_prop) and getattr(self.obj, self.inh_prop)

    # Whether or not this property is actually refinable
    @property
    def refinable(self):
        if isinstance(self.obj, _RefinementBase):
            # We have a _RefinementBase property (group or value)
            if isinstance(self.obj, RefinementGroup):
                if self.is_grouper: # the grouper itself
                    return False
                else: # attribute of the grouper
                    return (not self.inherited) and self.obj.children_refinable
            elif isinstance(self.obj, RefinementValue):
                return (not self.inherited) and self.obj.is_refinable
        else:
            # This is actually impossible, but what the hack...
            return (not self.inherited)

    # The refinement info object for the refinable property
    @property
    def ref_info(self):
        if (isinstance(self.obj, RefinementGroup) and self.is_grouper) or isinstance(self.obj, RefinementValue):
            return self.obj.refine_info
        else:
            name = self.prop_intel.get_refinement_info_name()
            if name is not None:
                ref_info = getattr(self.obj, name)
                return ref_info
            else:
                raise AttributeError, "Cannot find refine info model for attribute '%s' on '%s'" % (self.prop, self.obj)

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
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for a RefinableWrapper are:
                obj: the object we are wrapping a parameter for
                prop: the property name of the parameter on the object
        """
        my_kwargs = self.pop_kwargs(kwargs, "obj", "prop", "is_grouper")
        super(RefinableWrapper, self).__init__(**kwargs)
        kwargs = my_kwargs

        self.obj = self.get_kwarg(kwargs, None, "obj")
        self.prop_intel = self.get_kwarg(kwargs, None, "prop")
        self._is_grouper = self.get_kwarg(kwargs, False, "is_grouper")

    pass # end of class
