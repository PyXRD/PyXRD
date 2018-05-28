# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gi
gi.require_version('Gtk', '3.0')  # @UndefinedVariable
from gi.repository import Gtk

import logging
logger = logging.getLogger(__name__)

from mvc.models.properties import (
    StringProperty, BoolProperty, LabeledProperty, FloatProperty,
    SignalMixin, SetActionMixin
)

from pyxrd.generic.io import storables, Storable
from pyxrd.generic.models import DataModel

from pyxrd.refinement.refinables.properties import RefinableMixin
from pyxrd.refinement.refinables.mixins import RefinementValue
from pyxrd.refinement.refinables.metaclasses import PyXRDRefinableMeta

from .atom_relations import ComponentPropMixin

@storables.register()
class UnitCellProperty(ComponentPropMixin, RefinementValue, DataModel, Storable, metaclass=PyXRDRefinableMeta):
    """
        UnitCellProperty's are an integral part of a component and allow to 
        calculate the dimensions of the unit cell based on compositional
        information such as the iron content.
        This class is not responsible for keeping its value up-to-date.
        With other words, it is the responsibility of the higher-level class
        to call the 'update_value' method on this object whenever it emits a
        'data_changed' signal. The reason for this is to prevent infinite 
        recursion errors. 
    """
    class Meta(DataModel.Meta):
        store_id = "UnitCellProperty"

    component = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:

    #: The UnitCellProperty name
    name = StringProperty(
        default="", text="Name",
        visible=False, persistent=False,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: Flag indicating if this UnitCellProperty is enabled
    enabled = BoolProperty(
        default=False, text="Enabled",
        visible=True, persistent=True,
        set_action_name="update_value",
        mix_with=(SetActionMixin,)
    )

    #: Flag indicating if this UnitCellProperty is inherited
    inherited = BoolProperty(
        default=False, text="Inherited",
        visible=False, persistent=False,
        set_action_name="update_value",
        mix_with=(SetActionMixin,)
    )

    #: The value of the UnitCellProperty
    value = FloatProperty(
        default=0.0, text="Value",
        visible=True, persistent=True, refinable=True, widget_type='float_entry',
        set_action_name="update_value",
        mix_with=(SetActionMixin, RefinableMixin)
    )

    #: The factor of the UnitCellProperty (if enabled and not constant)
    factor = FloatProperty(
        default=1.0, text="Factor",
        visible=True, persistent=True, widget_type='float_entry',
        set_action_name="update_value",
        mix_with=(SetActionMixin,)
    )

    #: The constant of the UnitCellProperty (if enabled and not constant)
    constant = FloatProperty(
        default=0.0, text="Constant",
        visible=True, persistent=True, widget_type='float_entry',
        set_action_name="update_value",
        mix_with=(SetActionMixin,)
    )

    _temp_prop = None # temporary, JSON-style prop
    prop = LabeledProperty(
        default=None, text="Property",
        visible=True, persistent=True, widget_type='combo',
        set_action_name="update_value",
        mix_with=(SetActionMixin,)
    )

    # REFINEMENT VALUE IMPLEMENTATION:
    @property
    def refine_title(self):
        return self.name

    @property
    def refine_descriptor_data(self):
        return dict(
            phase_name=self.component.phase.refine_title,
            component_name=self.component.refine_title
        )

    @property
    def refine_value(self):
        return self.value
    @refine_value.setter
    def refine_value(self, value):
        if not self.enabled:
            self.value = value

    @property
    def refine_info(self):
        return self.value_ref_info

    @property
    def is_refinable(self):
        return not (self.enabled or self.inherited)

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        keys = [prop.label for prop in UnitCellProperty.Meta.get_local_persistent_properties()]
        keys.extend(["data_%s" % prop.label for prop in UnitCellProperty.Meta.get_local_persistent_properties()])
        my_kwargs = self.pop_kwargs(kwargs, "name", *keys)
        super(UnitCellProperty, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.data_changed.hold_and_emit():
            self.name = self.get_kwarg(kwargs, self.name, "name", "data_name")
            self.value = self.get_kwarg(kwargs, self.value, "value", "data_value")
            self.factor = self.get_kwarg(kwargs, self.factor, "factor", "data_factor")
            self.constant = self.get_kwarg(kwargs, self.constant, "constant", "data_constant")
            self.enabled = self.get_kwarg(kwargs, self.enabled, "enabled", "data_enabled")

            self._temp_prop = self.get_kwarg(kwargs, self.prop, "prop", "data_prop")

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def json_properties(self):
        retval = Storable.json_properties(self)
        if retval["prop"]:
            # Try to replace objects with their uuid's:
            try:
                retval["prop"] = [getattr(retval["prop"][0], 'uuid', retval["prop"][0]), retval["prop"][1]]
            except:
                logger.exception("Error when trying to interpret UCP JSON properties")
                pass # ignore
        return retval

    def resolve_json_references(self):
        if getattr(self, "_temp_prop", None):
            self._temp_prop = list(self._temp_prop)
            if isinstance(self._temp_prop[0], str):
                obj = type(type(self)).object_pool.get_object(self._temp_prop[0])
                if obj:
                    self._temp_prop[0] = obj
                    self.prop = self._temp_prop
                else:
                    self._temp_prop = None        
            self.prop = self._temp_prop
            del self._temp_prop

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def create_prop_store(self, extra_props=[]):
        assert(self.component is not None)
        store = Gtk.ListStore(object, str, str)
        # use private properties so we connect to the actual object stores and not the inherited ones
        for atom in self.component._layer_atoms:
            store.append([atom, "pn", atom.name])
        for atom in self.component._interlayer_atoms:
            store.append([atom, "pn", atom.name])
        for prop in extra_props:
            store.append(prop)
        return store

    def get_value_of_prop(self):
        try:
            return getattr(*self.prop)
        except:
            return 0.0

    def update_value(self):
        if self.enabled:
            self._value = float(self.factor * self.get_value_of_prop() + self.constant)
            self.data_changed.emit()

    pass # end of class
