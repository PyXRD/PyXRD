# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from mvc import PropIntel

from pyxrd.generic.io import storables, Storable
from pyxrd.generic.models import DataModel

from pyxrd.refinement.refinables.mixins import RefinementValue
from pyxrd.refinement.refinables.metaclasses import PyXRDRefinableMeta

from .atom_relations import ComponentPropMixin

@storables.register()
class UnitCellProperty(ComponentPropMixin, RefinementValue, DataModel, Storable):
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


    # MODEL INTEL:
    __metaclass__ = PyXRDRefinableMeta
    class Meta(DataModel.Meta):
        properties = [
            PropIntel(name="name", label="Name", data_type=unicode, is_column=True),
            PropIntel(name="value", label="Value", data_type=float, widget_type='float_entry', storable=True, has_widget=True, refinable=True),
            PropIntel(name="factor", label="Factor", data_type=float, widget_type='float_entry', storable=True, has_widget=True),
            PropIntel(name="constant", label="Constant", data_type=float, widget_type='float_entry', storable=True, has_widget=True),
            PropIntel(name="prop", label="Property", data_type=object, widget_type='combo', storable=True, has_widget=True),
            PropIntel(name="enabled", label="Enabled", data_type=bool, storable=True, has_widget=True),
            PropIntel(name="ready", label="Ready", data_type=bool),
            PropIntel(name="inherited", label="Inherited", data_type=bool)
        ]
        store_id = "UnitCellProperty"

    component = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:
    _name = ""
    def get_name(self): return self._name
    def set_name(self, value):
        if self._name != value:
            self._name = value
            self.visuals_changed.emit()

    _enabled = False
    def get_enabled(self): return self._enabled
    def set_enabled(self, value):
        if self._enabled != value:
            self._enabled = value
            self.update_value()

    _inherited = False
    def get_inherited(self): return self._inherited
    def set_inherited(self, value):
        if self._inherited != value:
            self._inherited = value
            self.update_value()

    _ready = False
    def get_ready(self): return self._ready
    def set_ready(self, value):
        if self._ready != value:
            self._ready = value
            self.update_value()

    _value = 1.0
    def get_value(self): return self._value
    def set_value(self, value):
        try: value = float(value)
        except ValueError: return
        if self._value != value:
            self._value = value
            self.update_value()

    _factor = 1.0
    def get_factor(self): return self._factor
    def set_factor(self, value):
        try: value = float(value)
        except ValueError: return
        if self._factor != value:
            self._factor = value
            self.update_value()

    _constant = 0.0
    def get_constant(self): return self._constant
    def set_constant(self, value):
        try: value = float(value)
        except ValueError: return
        if self._constant != value:
            self._constant = value
            self.update_value()

    _temp_prop = None # temporary, JSON-style prop
    _prop = None # obj, prop tuple
    def get_prop(self): return self._prop
    def set_prop(self, value):
        if self._prop != value:
            self._prop = value
            self.update_value()

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
        keys = [names[0] for names in UnitCellProperty.Meta.get_local_storable_properties()]
        keys.extend(["data_%s" % names[0] for names in UnitCellProperty.Meta.get_local_storable_properties()])
        my_kwargs = self.pop_kwargs(kwargs, "name", *keys)
        super(UnitCellProperty, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.data_changed.hold_and_emit():
            self._name = self.get_kwarg(kwargs, self.name, "name", "data_name")
            self._value = self.get_kwarg(kwargs, self._value, "value", "data_value")
            self._factor = self.get_kwarg(kwargs, self._factor, "factor", "data_factor")
            self._constant = self.get_kwarg(kwargs, self._constant, "constant", "data_constant")
            self._enabled = self.get_kwarg(kwargs, self.enabled, "enabled", "data_enabled")

            self._temp_prop = self.get_kwarg(kwargs, self._prop, "prop", "data_prop")

            self.ready = True

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def json_properties(self):
        retval = Storable.json_properties(self)
        if retval["prop"]:
            # Try to replace objects with their uuid's:
            try:
                retval["prop"] = [getattr(retval["prop"][0], 'uuid', retval["prop"][0]), retval["prop"][1]]
            except any:
                logger.exception("Error when trying to interpret UCP JSON properties")
                pass # ignore
        return retval

    def resolve_json_references(self):
        if getattr(self, "_temp_prop", None):
            self._temp_prop = list(self._temp_prop)
            if isinstance(self._temp_prop[0], basestring):
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
        from gtk import ListStore
        store = ListStore(object, str, object)
        # use private properties so we connect to the actual object stores and not the inherited ones
        for atom in self.component._layer_atoms:
            store.append([atom, "pn", lambda o: o.name])
        for atom in self.component._interlayer_atoms:
            store.append([atom, "pn", lambda o: o.name])
        for prop in extra_props:
            store.append(prop)
        return store

    def get_value_of_prop(self):
        try:
            return getattr(*self.prop)
        except:
            return 0.0

    def update_value(self):
        if self.enabled and self.ready:
            self._value = float(self.factor * self.get_value_of_prop() + self.constant)
            self.data_changed.emit()

    pass # end of class
