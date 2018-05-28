# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from mvc.models.properties import (
    LabeledProperty, StringProperty, BoolProperty,
    ReadOnlyMixin
)

from pyxrd.generic.models.base import ChildModel

from .mixins import _RefinementBase, RefinementValue, RefinementGroup

class RefinableWrapper(ChildModel):
    """
        Wrapper class for refinables easing the retrieval of certain
        properties for the different types of refinables.
        Can be used with an ObjectTreeStore.
    """

    # MODEL INTEL:
    class Meta(ChildModel.Meta):
        parent_alias = "mixture"

    # PROPERTIES:

    #: The wrapped object
    obj = LabeledProperty(
        default=None, text="Wrapped object", tabular=True)

    #: The property descriptor object for the attribute
    prop_descr = LabeledProperty(
        default=None, text="Property descriptor", tabular=True)

    #: The Property label:
    @StringProperty(
        default="", text="Property label", tabular=True, mix_with=(ReadOnlyMixin,))
    def label(self):
        return self.prop_descr.label

    #: A flag indicating whether this is wrapper is representing the group
    #: (True) or a member of the group (False):
    is_grouper = BoolProperty(
        default=False, text="Is grouper", tabular=True, mix_with=(ReadOnlyMixin,))

    #: The inherit attribute name:
    @LabeledProperty(
        default=None, text="Inherit from label", mix_with=(ReadOnlyMixin,))
    def inherit_from(self):
        return self.prop_descr.inherit_from if self.prop_descr else None

    #: The (possibly mathtext) label for the refinable property:
    @StringProperty(
        default="", text="Title", tabular=True, mix_with=(ReadOnlyMixin,))
    def title(self):
        if (isinstance(self.obj, RefinementGroup) and self.is_grouper) or isinstance(self.obj, RefinementValue):
            return self.obj.refine_title
        else:
            if getattr(self.prop_descr, "math_text", None) is not None:
                return self.prop_descr.math_text
            else:
                return self.prop_descr.text

    #: The (pure text) label for the refinable property:
    @StringProperty(
        default="", text="Text title", tabular=True, mix_with=(ReadOnlyMixin,))
    def text_title(self):
        if (isinstance(self.obj, RefinementGroup) and self.is_grouper) or isinstance(self.obj, RefinementValue):
            return self.obj.refine_title
        else:
            return self.prop_descr.text

    @StringProperty(
        default="", text="Descriptor", tabular=True, mix_with=(ReadOnlyMixin,))
    def text_descriptor(self):
        """ Return a longer title that also describes this property's relations """

        # This gets the phase and/or component name for the group or value:
        data = self.obj.refine_descriptor_data

        # Here we still need to get the actual property title:
        data["property_name"] = self.text_title

        return "%(phase_name)s | %(component_name)s | %(property_name)s" % data

    #: The actual value of the refinable property:
    @LabeledProperty(
        default=None, text="Value", tabular=True)
    def value(self):
        if isinstance(self.obj, RefinementValue):
            return self.obj.refine_value
        elif not self.is_grouper:
            return getattr(self.obj, self.label)
        else:
            return ""
    @value.setter
    def value(self, value):
        value = max(min(value, self.value_max), self.value_min)
        if self.is_grouper:
            raise AttributeError("Cannot set the value for a grouping RefinableWrapper")
        elif isinstance(self.obj, RefinementValue):
            self.obj.refine_value = value
        else:
            setattr(self.obj, self.label, value)

    #: Whether or not this property is inherited from another object
    @BoolProperty(
        default=False, text="Inherited", tabular=True, mix_with=(ReadOnlyMixin,))
    def inherited(self):
        return self.inherit_from is not None and hasattr(self.obj, self.inherit_from) and getattr(self.obj, self.inherit_from)

    #: Whether or not this property is actually refinable
    @BoolProperty(
        default=False, text="Refinable", tabular=True, mix_with=(ReadOnlyMixin,))
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

    #: The refinement info object for the refinable property
    @LabeledProperty(
        default=None, text="Refinement info", tabular=True, mix_with=(ReadOnlyMixin,))
    def ref_info(self):
        if (isinstance(self.obj, RefinementGroup) and self.is_grouper) or isinstance(self.obj, RefinementValue):
            return self.obj.refine_info
        else:
            name = self.prop_descr.get_refinement_info_name()
            if name is not None:
                ref_info = getattr(self.obj, name)
                return ref_info
            else:
                raise AttributeError("Cannot find refine info model for attribute '%s' on '%s'" % (self.label, self.obj))

    #: The minimum value for the refinable property
    @LabeledProperty(
        default=None, text="Minimum value", tabular=True)
    def value_min(self):
        return self.ref_info.minimum if self.ref_info else None
    @value_min.setter
    def value_min(self, value):
        if self.ref_info:
            self.ref_info.minimum = value

    #: The maximum value of the refinable property
    @LabeledProperty(
        default=None, text="Maximum value", tabular=True)
    def value_max(self):
        return self.ref_info.maximum if self.ref_info else None
    @value_max.setter
    def value_max(self, value):
        if self.ref_info:
            self.ref_info.maximum = value

    #: Wether this property is selected for refinement
    @BoolProperty(
        default=False, text="Refine", tabular=True)
    def refine(self):
        return self.ref_info.refine if self.ref_info else False
    @refine.setter
    def refine(self, value):
        if self.ref_info:
            self.ref_info.refine = value and self.refinable

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for a RefinableWrapper are:
                obj: the object we are wrapping a parameter for
                prop or prop_descr: the property descriptor
                is_grouper: whether or not this is a grouper object
        """
        my_kwargs = self.pop_kwargs(kwargs, "obj", "prop", "prop_descr", "is_grouper")
        super(RefinableWrapper, self).__init__(**kwargs)
        kwargs = my_kwargs

        self.obj = self.get_kwarg(kwargs, None, "obj")
        self.prop_descr = self.get_kwarg(kwargs, None, "prop_descr", "prop")
        self._is_grouper = self.get_kwarg(kwargs, False, "is_grouper")

    pass # end of class
