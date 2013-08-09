# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from gtk import ListStore

from generic.io import storables, Storable
from generic.models import ChildModel, PropIntel
from generic.models.metaclasses import pyxrd_object_pool
from generic.refinement.mixins import RefinementValue

from phases.atom_relations import ComponentPropMixin

@storables.register()
class UnitCellProperty(ChildModel, Storable, ComponentPropMixin, RefinementValue):
    
    #MODEL INTEL:
    __parent_alias__ = "component"
    __model_intel__ = [
        PropIntel(name="name",       label="Name",      data_type=unicode, is_column=True),
        PropIntel(name="value",      label="Value",     data_type=float,   widget_type='float_input', storable=True, has_widget=True, refinable=True),
        PropIntel(name="factor",     label="Factor",    data_type=float,   widget_type='float_input', storable=True, has_widget=True),
        PropIntel(name="constant",   label="Constant",  data_type=float,   widget_type='float_input', storable=True, has_widget=True),
        PropIntel(name="prop",       label="Property",  data_type=object,  widget_type='combo', storable=True, has_widget=True),
        PropIntel(name="enabled",    label="Enabled",   data_type=bool,    storable=True, has_widget=True),
        PropIntel(name="inherited",  label="Inherited", data_type=bool)
    ]
    __store_id__ = "UnitCellProperty"
    
    #PROPERTIES:
    name = ""
    enabled = False
    inherited = False
    ready = False
    
    _value = 1.0
    value_range = [0,2.0]
    def get_value_value(self): return self._value
    def set_value_value(self, value):
        self._value = float(value)
    
    _factor = 1.0
    def get_factor_value(self): return self._factor
    def set_factor_value(self, value):
        self._factor = float(value)
        self.update_value()
    
    _constant = 0.0
    def get_constant_value(self): return self._constant
    def set_constant_value(self, value):
        self._constant = float(value)
        self.update_value()
    
    _temp_prop = None #temporary, JSON-style prop
    _prop = None #obj, prop tuple
    def get_prop_value(self): return self._prop
    def set_prop_value(self, value):
        if self._prop:
            obj, prop = self._prop
            self.relieve_model(obj)
            self.remove_observing_method((prop,), self.on_prop_changed)
        self._prop = value
        if self._prop:
            obj, prop = self._prop
            self.observe(self.on_prop_changed, str(prop), assign=True)
            self.observe_model(obj)
        self.update_value()
    
    #REFINEMENT VALUE IMPLEMENTATION:
    @property
    def refine_title(self):
        return self.name

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
    def __init__(self, name="", value=0.0, enabled=False, factor=0.0, constant=0.0, prop=None, parent=None, **kwargs):
        super(UnitCellProperty, self).__init__(parent=parent)
               
        self.name = name or self.get_depr(kwargs, self.name, "data_name")
        self.value = value or self.get_depr(kwargs, self._value, "data_value")
        self.factor = factor or self.get_depr(kwargs, self._factor, "data_factor")
        self.constant = constant or self.get_depr(kwargs, self._constant, "data_constant")
        self.enabled = enabled or self.get_depr(kwargs, self.enabled, "data_enabled")        
        
        self._temp_prop = prop or self._parseattr(self.get_depr(kwargs, self._prop, "data_prop"))
        
        self.ready = True
        
   # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------                        
    def json_properties(self):
        retval = Storable.json_properties(self)
        if retval["prop"]:
            #Try to replace objects with their uuid's:
            try:
                retval["prop"] = [getattr(retval["prop"][0], 'uuid', retval["prop"][0]), retval["prop"][1]]
            except:
                from traceback import print_exc
                print_exc()
                pass #ignore
        return retval
        
    def resolve_json_references(self):
        if getattr(self, "_temp_prop", None):
            self._temp_prop = list(self._temp_prop)
            if isinstance(self._temp_prop[0], basestring):
                obj = pyxrd_object_pool.get_object(self._temp_prop[0])
                if obj:
                    self._temp_prop[0] = obj
                    self.prop = self._temp_prop
                else:
                    self._temp_prop = None
            self.prop = self._temp_prop
            del self._temp_prop
            
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    def on_prop_changed(self, model, prop_name, info):
        self.update_value()
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------      
    def create_prop_store(self, extra_props=[]):
        assert(self.component != None)
        store = ListStore(object, str, object)
        #use private properties so we connect to the actual object stores and not the inherited ones
        for i, atom in enumerate(self.component._layer_atoms.iter_objects()):
            store.append([atom, "pn", lambda o: o.name])
        for i, atom in enumerate(self.component._interlayer_atoms.iter_objects()):
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
            self.value = float(self.factor * self.get_value_of_prop() + self.constant)
            self.component.dirty = True
        
    pass #end of class   
