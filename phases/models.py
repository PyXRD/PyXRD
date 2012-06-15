# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from random import choice
import zipfile
import time
from warnings import warn
from math import sin, cos, pi, sqrt, exp, radians, log

from gtkmvc.model import Model, Observer, Signal

import numpy as np
from scipy.special import erf

from generic.metaclasses import pyxrd_object_pool
from generic.utils import lognormal, sqrt2pi, sqrt8, print_timing, get_md5_hash, recgetattr, recsetattr
from generic.custom_math import mmult, mdot, mtim, solve_division
from generic.io import Storable, PyXRDDecoder
from generic.model_mixins import ObjectListStoreChildMixin, ObjectListStoreParentMixin
from generic.models import ChildModel, PropIntel
from generic.treemodels import ObjectListStore

from atoms.models import Atom
from probabilities.models import get_correct_probability_model

class ComponentPropMixin():

    #
    # _data_prop contains a string (e.g. data_cell_a or data_layer_atoms.2) which can be parsed
    # into an object and a property to be used for the calculation & observed for changes
    #

    def _parseattr(self, attr):
        attrs = attr.split(".")
        if attrs[0] == "data_layer_atoms":
            return self.component._data_layer_atoms._model_data[int(attrs[1])], "data_pn"
        elif attrs[0] == "data_interlayer_atoms":
            return self.component._data_interlayer_atoms._model_data[int(attrs[1])], "data_pn"
        else:
            return self.component, attr

    def _getattr(self, attr):
        return recgetattr(*self._parseattr(attr))

    def _setattr(self, attr, value):
        return recsetattr(*(self._parseattr(attr) + (value,)))

class ComponentRatioFunction(ChildModel, Storable, ComponentPropMixin, ObjectListStoreChildMixin):
    
    #MODEL INTEL:
    __parent_alias__ = "component"
    __model_intel__ = [
        PropIntel(name="data_name",         inh_name=None,         label="Name",                    minimum=None,  maximum=None,  is_column=True,  ctype=str,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_sum",          inh_name=None,         label="Sum",                     minimum=0.0,   maximum=None,  is_column=True,  ctype=float, refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_ratio",        inh_name=None,         label=lambda p,s: s.data_name,   minimum=0.0,   maximum=1.0,   is_column=True,  ctype=float, refinable=True,  storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_prop1",        inh_name=None,         label="Property 1",              minimum=None,  maximum=None,  is_column=True,  ctype=str,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_prop2",        inh_name=None,         label="Property 2",              minimum=None,  maximum=None,  is_column=True,  ctype=str,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_enabled",      inh_name=None,         label="Enabled",                 minimum=None,  maximum=None,  is_column=True,  ctype=bool,  refinable=False, storable=False,  observable=True,  has_widget=True)
    ]
    
    #SIGNALS:
    
    #PROPERTIES:
    data_name = ""
    
    ready = False
    def get_data_enabled_value(self):
        return (not self.parent.inherit_atom_ratios)
    
    _data_sum = 1.0
    def get_data_sum_value(self): return self._data_sum
    def set_data_sum_value(self, value):
        self._data_sum = float(value)
        self.update_value()
    
    _data_ratio = 0.0
    def get_data_ratio_value(self): return self._data_ratio
    def set_data_ratio_value(self, value):
        self._data_ratio = float(value)
        self.update_value()
    
    _data_prop1 = ""
    def get_data_prop1_value(self): return self._data_prop1
    def set_data_prop1_value(self, value):
        if self._data_prop1:
            obj, prop = self._parseattr(self._data_prop1)
            self.remove_observing_method((prop,), self.on_prop1_changed)
            self.relieve_model(obj)
        self._data_prop1 = str(value)
        if self._data_prop1:
            obj, prop = self._parseattr(self._data_prop1)
            self.observe(self.on_prop1_changed, str(prop), assign=True)
            self.observe_model(obj)
        self.update_value()
    
    _data_prop2 = ""
    def get_data_prop2_value(self): return self._data_prop2    
    def set_data_prop2_value(self, value):
        if self._data_prop2:
            obj, prop = self._parseattr(self._data_prop2)
            self.remove_observing_method((prop,), self.on_prop2_changed)
            self.relieve_model(obj)
        self._data_prop2 = str(value)
        if self._data_prop2:
            obj, prop = self._parseattr(self._data_prop2)
            self.observe(self.on_prop2_changed, str(prop), assign=True)
            self.observe_model(obj)
        self.update_value()
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name="", data_sum=0.0, data_ratio=0.0, data_prop1="", data_prop2="", parent=None):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
        self.data_name = data_name or self.data_name
        self.data_sum = data_sum or self._data_sum
        self.data_ratio = data_ratio or self._data_ratio
        self.data_prop1 = data_prop1 or self._data_prop1
        self.data_prop2 = data_prop2 or self._data_prop2
        
        self.ready = True
        
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    def on_prop1_changed(self, model, prop_name, info):
        self.update_value()
    def on_prop2_changed(self, model, prop_name, info):
        self.update_value()
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update_value(self):
        if self.data_enabled and self.ready:
            self._setattr(self.data_prop1, self.data_ratio*self.data_sum)
            self._setattr(self.data_prop2, (1-self.data_ratio)*self.data_sum)
            self.component.dirty = True
        
    pass #end of class

class UnitCellProperty(ChildModel, Storable, ComponentPropMixin):
    
    #MODEL INTEL:
    __parent_alias__ = "component"
    __model_intel__ = [
        PropIntel(name="value",             inh_name=None,         label="Value",              minimum=None,  maximum=None,  is_column=False, ctype=float, refinable=True,  storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_factor",       inh_name=None,         label="Factor",             minimum=None,  maximum=None,  is_column=False, ctype=float, refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_constant",     inh_name=None,         label="Constant",           minimum=None,  maximum=None,  is_column=False, ctype=float, refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_prop",         inh_name=None,         label="Property",           minimum=None,  maximum=None,  is_column=False, ctype=str,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_enabled",      inh_name=None,         label="Enabled",            minimum=None,  maximum=None,  is_column=False, ctype=bool,  refinable=False, storable=True,  observable=True,  has_widget=True)
    ]
    
    #SIGNALS:
    
    #PROPERTIES:
    
    data_enabled = False
    ready = False
    
    _value = 1.0
    value_range = [0,2.0]
    def get_value_value(self): return self._value
    def set_value_value(self, value):
        self._value = float(value)
    
    _data_factor = 1.0
    def get_data_factor_value(self): return self._data_factor
    def set_data_factor_value(self, value):
        self._data_factor = float(value)
        self.update_value()
    
    _data_constant = 0.0
    def get_data_constant_value(self): return self._data_constant
    def set_data_constant_value(self, value):
        self._data_constant = float(value)
        self.update_value()
    
    _data_prop = ""
    def get_data_prop_value(self): return self._data_prop
    def set_data_prop_value(self, value):
        if self._data_prop:
            obj, prop = self._parseattr(self._data_prop)
            self.remove_observing_method((prop,), self.on_prop_changed)
            self.relieve_model(obj)
        self._data_prop = str(value)
        if self._data_prop:
            obj, prop = self._parseattr(self._data_prop)
            self.observe(self.on_prop_changed, str(prop), assign=True)
            self.observe_model(obj)
        self.update_value()
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, value=0.0, data_enabled=False, data_factor=0.0, data_constant=0.0, data_prop="", parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
               
        self.value = value or self._value
        self.data_factor = data_factor or self._data_factor
        self.data_constant = data_constant or self._data_constant
        self.data_enabled = data_enabled or self.data_enabled
        self.data_prop = data_prop or self._data_prop # last one needs observer so we don't set the private prop
        
        self.ready = True
        
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    def on_prop_changed(self, model, prop_name, info):
        self.update_value()
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    
    def get_prop_value(self):
        if self.data_prop:
            return self._getattr(self.data_prop)
        else:
            return 0.0
            
    def update_value(self):
        if self.data_enabled and self.ready:
            self.value = float(self.data_factor * self.get_prop_value() + self.data_constant)
            self.component.dirty = True
        
    pass #end of class


class Component(ChildModel, Storable, ObjectListStoreChildMixin, ObjectListStoreParentMixin):

    #MODEL INTEL:
    __parent_alias__ = "phase"
    __model_intel__ = [
        PropIntel(name="data_name",                 inh_name=None,                          label="Name",                   minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_linked_with",          inh_name=None,                          label="Linked with",            minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=False, observable=True,  has_widget=True),
        PropIntel(name="data_d001",                 inh_name="inherit_d001",                label="Cell length c [nm]",     minimum=0.0,   maximum=None,  is_column=True,  ctype=float,  refinable=True,  storable=True,  observable=True,  has_widget=True),
        PropIntel(name="default_c",                 inh_name="inherit_default_c",           label="Default c length [nm]",  minimum=0.0,   maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_ucp_a",                inh_name="inherit_ucp_a",               label="Cell length a [nm]",     minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=True,  storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_ucp_b",                inh_name="inherit_ucp_b",               label="Cell length b [nm]",     minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=True,  storable=True,  observable=True,  has_widget=True),      
        PropIntel(name="inherit_d001",              inh_name=None,                          label="Inh. cell length c",     minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_ucp_b",             inh_name=None,                          label="Inh. cell length b",     minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_ucp_a",             inh_name=None,                          label="Inh. cell length a",     minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_default_c",         inh_name=None,                          label="Inh. default length c",  minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_layer_atoms",       inh_name=None,                          label="Inh. layer atoms",       minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_interlayer_atoms",  inh_name=None,                          label="Inh. interlayer atoms",  minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_atom_ratios",       inh_name=None,                          label="Inh. atom ratios",       minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_atom_ratios",          inh_name="inherit_atom_ratios",         label="Atom ratios",            minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=True,  storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_layer_atoms",          inh_name="inherit_layer_atoms",         label="Layer atoms",            minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_interlayer_atoms",     inh_name="inherit_interlayer_atoms",    label="Interlayer atoms",       minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="needs_update",              inh_name=None,                          label="",                       minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="dirty",                     inh_name=None,                          label="",                       minimum=None,  maximum=None,  is_column=False, ctype=bool,   refinable=False, storable=False, observable=True,  has_widget=False),        
    ]

    #SIGNALS:
    needs_update = None

    #PROPERTIES:
    data_name = "Name of this component"
       
    _dirty = True
    def get_dirty_value(self): return (self._dirty)
    def set_dirty_value(self, value):
        if value!=self._dirty: 
            self._dirty = value
            if self._dirty:
                self._cached_factors = dict()
    
    _inherit_ucp_a = False 
    _inherit_ucp_b = False
    _inherit_d001 = False
    _inherit_default_c = False
    _inherit_layer_atoms = False
    _inherit_interlayer_atoms = False
    _inherit_atom_ratios = False
    @Model.getter(*[prop.inh_name for prop in __model_intel__ if prop.inh_name])
    def get_inherit_prop(self, prop_name): return getattr(self, "_%s" % prop_name)
    @Model.setter(*[prop.inh_name for prop in __model_intel__ if prop.inh_name])
    def set_inherit_prop(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        self.dirty = True
        self.liststore_item_changed()
        self.needs_update.emit()

    _data_linked_with = None
    _linked_with_index = None
    _linked_with_uuid = None
    def get_data_linked_with_value(self): return self._data_linked_with
    def set_data_linked_with_value(self, value):
        if value != self._data_linked_with:
            if self._data_linked_with != None:
                self.relieve_model(self._data_linked_with)
            self._data_linked_with = value
            if self._data_linked_with!=None:
                self.observe_model(self._data_linked_with)
            else:
                for prop in self.__inheritables__:
                    setattr(self, prop.replace("data_", "inherit_", 1), False)
            self.liststore_item_changed()
            self.dirty = True
            
    #INHERITABLE PROPERTIES:   
    _data_ucp_a = None
    _data_ucp_b = None
    _data_d001 = 1.0
    _default_c = 1.0
    _data_layer_atoms = None
    _data_interlayer_atoms = None
    _data_atom_ratios = None
    @Model.getter(*[prop.name for prop in __model_intel__ if prop.inh_name])
    def get_inheritable(self, prop_name): #TODO remove the data prefixes!
        inh_name = "inherit_%s" % prop_name.replace("data_", "", 1)
        if self.data_linked_with != None and getattr(self, inh_name):
            return getattr(self.data_linked_with, prop_name)
        else:
            return getattr(self, "_%s" % prop_name)
    @Model.setter(*[prop.name for prop in __model_intel__ if prop.inh_name])
    def set_inheritable(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        if prop_name=="default_d":
            for atom in self.data_interlayer_atoms.iter_objects():
                atom.liststore_item_changed()
        self.dirty = True
        self.liststore_item_changed()
        self.needs_update.emit()
        
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name=None, data_ucp_a=None, data_ucp_b=None, data_d001=None, default_c=None,
                 data_layer_atoms=None, data_interlayer_atoms=None, data_atom_ratios=None,
                 inherit_ucp_a=False, inherit_ucp_b=False, inherit_d001=False, inherit_default_c=False,
                 inherit_layer_atoms=False, inherit_interlayer_atoms=False, inherit_atom_ratios=False, 
                 linked_with_index = None, linked_with_uuid = None, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)

        self.data_name = data_name or self.data_name

        self.needs_update = Signal()
        self.dirty = True
        self._cached_factors = dict()
        
        self._data_layer_atoms = self.parse_liststore_arg(data_layer_atoms, ObjectListStore, Atom)
        self._data_interlayer_atoms = self.parse_liststore_arg(data_interlayer_atoms, ObjectListStore, Atom)
        self._data_atom_ratios = self.parse_liststore_arg(data_atom_ratios, ObjectListStore, ComponentRatioFunction)
        
        for atom in self._data_interlayer_atoms._model_data:
            atom.stretch_values = True

        def on_interlayer_atom_inserted(atom):
            atom.stretch_values = True
            self.dirty = True
            self.needs_update.emit()

        def on_item_changed(*args):
            self.dirty = True
            self.needs_update.emit()
                
        def on_layer_item_changed(*args):
            self.dirty = True
            self._update_lattice_d()
            self.needs_update.emit()
        
        self._data_layer_atoms.connect("item-inserted", on_layer_item_changed)
        self._data_layer_atoms.connect("item-removed", on_layer_item_changed)
        self._data_layer_atoms.connect("row-changed", on_layer_item_changed)
                        
        self._data_interlayer_atoms.connect("item-inserted", on_interlayer_atom_inserted)
        self._data_interlayer_atoms.connect("item-removed", on_item_changed)
        self._data_atom_ratios.connect("item-removed", on_item_changed)
        self._data_atom_ratios.connect("item-inserted", on_item_changed)        
        self._data_interlayer_atoms.connect("row-changed", on_item_changed)
    
        self._data_d001 = data_d001 or self.data_d001
        
        self._default_c = default_c or data_d001 or self._default_c
        self._update_lattice_d()        
        
        if data_ucp_a==None and "data_cell_a" in kwargs and not "data_ucp_a" in kwargs:
            data_ucp_a = UnitCellProperty(data_name="cell length a", value=kwargs.pop("data_cell_a"), parent=self)
            inherit_ucp_a = kwargs.pop("inherit_cell_a", inherit_ucp_a)
        if data_ucp_b==None and "data_cell_b" in kwargs and not "data_ucp_b" in kwargs:
            data_ucp_b = UnitCellProperty(data_name="cell length b", value=kwargs.pop("data_cell_b"), parent=self)
            inherit_ucp_b = kwargs.pop("inherit_cell_b", inherit_ucp_b)
        
        self._data_ucp_a = self.parse_init_arg(data_ucp_a, UnitCellProperty(parent=self), child=True)
        self._data_ucp_b = self.parse_init_arg(data_ucp_b, UnitCellProperty(parent=self), child=True)
        self._data_ucp_a.update_value()
        self._data_ucp_b.update_value()
        
        self._linked_with_uuid = linked_with_uuid if linked_with_uuid!=None else ""
        self._linked_with_index = linked_with_index if linked_with_index > -1 else None
        
        self._inherit_d001 = inherit_d001
        self._inherit_ucp_a = inherit_ucp_a
        self._inherit_ucp_b = inherit_ucp_b
        self._inherit_default_c = inherit_default_c
        self._inherit_layer_atoms = inherit_layer_atoms          
        self._inherit_interlayer_atoms = inherit_interlayer_atoms
        self._inherit_atom_ratios = inherit_atom_ratios


    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Observer.observe("dirty", assign=True)
    def notify_dirty_changed(self, model, prop_name, info):
        if model.dirty: self.dirty = True
        pass
    
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------  
    def resolve_json_references(self):
        for atom in self._data_layer_atoms._model_data:
            atom.resolve_json_references()
        for atom in self._data_interlayer_atoms._model_data:
            atom.resolve_json_references()
        
        if self._linked_with_uuid:
            self.data_linked_with = pyxrd_object_pool.get_object(self._linked_with_uuid)
        elif self._linked_with_index != None and self._linked_with_index != -1:
            warn("The use of object indeces is deprected since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
            self.data_linked_with = self.parent.data_based_on.data_components.get_user_data_from_index(self._linked_with_index)
        del self._linked_with_uuid
        del self._linked_with_index
                        
    def json_properties(self):
        retval = Storable.json_properties(self)    
        if not self.phase.save_links:
            for prop in self.__model_intel__:
                if prop.inh_name:
                    retval[prop.inh_name] = False
            retval["linked_with_uuid"] = ""
        else:
            retval["linked_with_uuid"] = self.data_linked_with.uuid if self.data_linked_with!=None else ""
        return retval

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------  
    def get_factors(self, range_stl):
        hsh = get_md5_hash(range_stl)
        if self.dirty or not hsh in self._cached_factors:
            sf_tot = np.zeros(range_stl.shape, dtype=np.complex_)
            for atom in self.data_layer_atoms._model_data:
                sf_tot += atom.get_structure_factors(range_stl)
            for atom in self.data_interlayer_atoms._model_data:
                sf_tot += atom.get_structure_factors(range_stl)
            self._cached_factors[hsh] = sf_tot, np.exp(2*pi*self.data_d001*range_stl*1j)
            self.dirty = False
        return self._cached_factors[hsh]

    def _update_lattice_d(self):
        self._lattice_d = 0.0
        for atom in self.data_layer_atoms.iter_objects():
            self._lattice_d = max(self._lattice_d, atom.default_z)

    def get_interlayer_stretch_factors(self):
        try:
            return self._lattice_d, (self.data_cell_c - self._lattice_d) / (self.default_c - self._lattice_d)
        except:
            raise
            return None

    @property
    def data_cell_a(self):
        return self._data_ucp_a.value
    @property
    def data_cell_b(self):
        return self._data_ucp_b.value
    @property
    def data_cell_c(self):
        return self.data_d001

    def get_volume(self):
        return self.data_cell_a * self.data_cell_b * self.data_cell_c

    def get_weight(self):
        weight = 0
        for atom in (self.data_layer_atoms._model_data + self.data_interlayer_atoms._model_data):
            weight += atom.data_pn * atom.data_atom_type.data_weight
        return weight


class Phase(ChildModel, Storable, ObjectListStoreParentMixin, ObjectListStoreChildMixin):

    #MODEL INTEL:
    __parent_alias__ = 'project'
    __model_intel__ = [
        PropIntel(name="data_name",             inh_name=None,                      label="Name",                               minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="display_color",         inh_name="inherit_display_color",   label="Display color",                      minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_based_on",         inh_name=None,                      label="Based on phase",                     minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=False, observable=True,  has_widget=True),
        PropIntel(name="data_G",                inh_name=None,                      label="# of components",                    minimum=None,  maximum=None,  is_column=True,  ctype=int,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_R",                inh_name=None,                      label="Reichweite",                         minimum=None,  maximum=None,  is_column=True,  ctype=int,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_mean_CSDS",        inh_name="inherit_mean_CSDS",       label="Mean CSDS",                          minimum=1.0,   maximum=None,  is_column=True,  ctype=float,  refinable=True,  storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_min_CSDS",         inh_name="inherit_min_CSDS",        label="Minimum CSDS",                       minimum=1.0,   maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_max_CSDS",         inh_name="inherit_max_CSDS",        label="Maximum CSDS",                       minimum=1.0,   maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_sigma_star",       inh_name="inherit_sigma_star",      label="σ<sup>*</sup> [°]",                  minimum=0.0,   maximum=90.0,  is_column=True,  ctype=float,  refinable=True,  storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_display_color", inh_name=None,                      label="Inh. display color",                 minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_mean_CSDS",     inh_name=None,                      label="Inh. mean CSDS",                     minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_min_CSDS",      inh_name=None,                      label="Inh. min CSDS",                      minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_max_CSDS",      inh_name=None,                      label="Inh. max CSDS",                      minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_sigma_star",    inh_name=None,                      label="Inh. sigma star",                    minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_probabilities", inh_name=None,                      label="Inh. probabilities",                 minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_probabilities",    inh_name="inherit_probabilities",   label="Probabilities",                      minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=True,  storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_components",       inh_name=None,                      label="Components",                         minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=True,  storable=True,  observable=True,  has_widget=True),
        PropIntel(name="needs_update",          inh_name=None,                      label="",                                   minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="dirty",                 inh_name=None,                      label="",                                   minimum=None,  maximum=None,  is_column=False, ctype=bool,   refinable=False, storable=False, observable=True,  has_widget=False),
    ]
    
    #SIGNALS:
    needs_update = None
    
    #PROPERTIES:
    data_name = "Name of this phase"
    
    _dirty = True
    def get_dirty_value(self): return self._dirty
    def set_dirty_value(self, value):
        if value!=self._dirty:
            self._dirty = value

    _inherit_display_color = False   
    _inherit_mean_CSDS = False
    _inherit_min_CSDS = False
    _inherit_max_CSDS = False
    _inherit_sigma_star = False
    _inherit_probabilities = False
    @Model.getter(*[prop.inh_name for prop in __model_intel__ if prop.inh_name])
    def get_inherit_prop(self, prop_name): return getattr(self, "_%s" % prop_name)
    @Model.setter(*[prop.inh_name for prop in __model_intel__ if prop.inh_name])
    def set_inherit_prop(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        if not prop_name=="inherit_display_color": self.dirty = True
        self.needs_update.emit()
        self.liststore_item_changed()
                
    _based_on_index = None #temporary property
    _based_on_uuid = None #temporary property
    _data_based_on = None
    def get_data_based_on_value(self): return self._data_based_on
    def set_data_based_on_value(self, value):
        if self._data_based_on!=None:
            self.relieve_model(self._data_based_on)
        if value == None or value.get_based_on_root() == self or value.parent != self.parent:
            value = None
        if value != self._data_based_on:
            self._data_based_on = value
            for component in self.data_components._model_data:
                component.data_linked_with = None
        if self._data_based_on!=None:
            self.observe_model(self._data_based_on)
        else:
            for prop in self.__model_intel__:
                if prop.inh_name: setattr(self, prop.inh_name, False)
        self.dirty = True
        self.needs_update.emit()
        self.liststore_item_changed()
    def get_based_on_root(self):
        if self.data_based_on != None:
            return self.data_based_on.get_based_on_root()
        else:
            return self
    
    #INHERITABLE PROPERTIES:
    _display_color = "#FFB600"
    _data_mean_CSDS = 10.0
    data_mean_CSDS_range = [0,500]
    _data_min_CSDS = 1.0
    _data_max_CSDS = 50.0
    _data_sigma_star = 3.0
    data_sigma_star_range = [0,90]
    _data_probabilities = None
    @Model.getter(*[prop.name for prop in __model_intel__ if prop.inh_name])
    def get_inheritable(self, prop_name):
        inh_name = "inherit_" + prop_name.replace("data_", "", 1)
        if self.data_based_on is not None and getattr(self, inh_name):
            return getattr(self.data_based_on, prop_name)
        else:
            return getattr(self, "_%s" % prop_name)
    @Model.setter(*[prop.name for prop in __model_intel__ if prop.inh_name])
    def set_inheritable(self, prop_name, value):
        prob = (prop_name == "data_probabilities")
        col = (prop_name == "display_color")
        if prob and self._data_probabilities:
            self.relieve_model(self._data_probabilities)
        setattr(self, "_%s" % prop_name, value)
        if prob and self._data_probabilities:
            self._data_probabilities.update()
            self.observe_model(self._data_probabilities)
        if not col: self.dirty = True
        self.needs_update.emit()
        self.liststore_item_changed()
    
    _data_components = None    
    def get_data_components_value(self): return self._data_components
    def set_data_components_value(self, value):
        if self._data_components != None:
            for comp in self._data_components._model_data: self.relieve_model(comp)
        self._data_components = value
        if self._data_components != None:
            for comp in self._data_components._model_data: self.observe_model(comp)
        self.dirty = True
        self.liststore_item_changed()
    def get_data_G_value(self):
        if self.data_components != None:
            return len(self.data_components._model_data)
        else:
            return 0
            
    _data_R = 0
    def get_data_R_value(self):
        return self._data_R
    
    #Flag indicating wether or not the links (based_on and linked_with) should
    #be saved as well.
    save_links = True
    #Flag indicating wether or not atom types in the components should be
    #exported using their name rather then their project-uuid.
    export_atom_types = False
    
    line_colors = [
        "#004488",
        "#FF4400",
        "#559911",
        "#770022",
        "#AACC00",
        "#441177",
    ]
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name=None, display_color=None, data_sigma_star=None, 
                 data_G=None, data_R=0, based_on_index = None, based_on_uuid = None,
                 data_mean_CSDS=None, data_max_CSDS=None, data_min_CSDS=None, 
                 data_probabilities=None, data_components=None,
                 inherit_display_color=False, inherit_sigma_star=False,
                 inherit_mean_CSDS=False, inherit_min_CSDS=False, inherit_max_CSDS=False, 
                 inherit_probabilities=False, inherit_wtfractions=False,
                 parent=None):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        self._dirty = True
        self._cached_diffracted_intensities = dict()  
        
        self.needs_update = Signal()
        
        self.data_name = data_name or self.data_name
        
        self._display_color = display_color or choice(self.line_colors)
        self._data_mean_CSDS = data_mean_CSDS or self.data_mean_CSDS
        self._data_min_CSDS = data_min_CSDS or self.data_min_CSDS
        self._data_max_CSDS = data_max_CSDS or self.data_max_CSDS
        self._data_sigma_star = data_sigma_star or self.data_sigma_star 
        
        self.inherit_display_color = inherit_display_color       
        self.inherit_mean_CSDS = inherit_mean_CSDS
        self.inherit_min_CSDS = inherit_min_CSDS
        self.inherit_max_CSDS = inherit_max_CSDS
        self.inherit_sigma_star = inherit_sigma_star


        self.data_components = self.parse_liststore_arg(
            data_components, ObjectListStore, Component)
        if data_G != None and data_G > 0:
            for i in range(len(self.data_components._model_data), data_G):
                new_comp = Component("Component %d" % (i+1), parent=self)
                self.data_components.append(new_comp)
                self.observe_model(new_comp)
        self._data_R = data_R
        
        self.data_probabilities = self.parse_init_arg(data_probabilities,
            get_correct_probability_model(self), child=True)
        self.data_probabilities.update() #force an update
        self.inherit_probabilities = inherit_probabilities

        self._based_on_uuid = based_on_uuid if based_on_uuid!=None else ""
        self._based_on_index = based_on_index if based_on_index > -1 else None

    def __str__(self):
        return "<PHASE %s(%s) %s>" % (self.data_name, repr(self), self.data_based_on)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Observer.observe("needs_update", signal=True)
    def notify_needs_update(self, model, prop_name, info):
        self.needs_update.emit() #propagate signal
        
    @Observer.observe("dirty", assign=True)
    def notify_dirty_changed(self, model, prop_name, info):
        if model.dirty: self.dirty = True
        pass

    @Observer.observe("updated", signal=True)
    def notify_updated(self, model, prop_name, info):
        self.dirty = True
        self.needs_update.emit() #propagate signal

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------  
    def resolve_json_references(self):
        #Set the based on and linked with variables:
        if self._based_on_uuid:
            self.data_based_on = pyxrd_object_pool.get_object(self._based_on_uuid)
        elif self._based_on_index != None and self._based_on_index != -1:
            warn("The use of object indeces is deprected since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
            self.data_based_on = self.parent.data_phases.get_user_data_from_index(self._based_on_index)
        del self._based_on_index
        del self._based_on_uuid
        for component in self.data_components._model_data:
            component.resolve_json_references()

    @classmethod
    def save_phases(cls, phases, filename):
        """
            Saves multiple phases to a single file.
        """
        pyxrd_object_pool.stack_uuids()
        for phase in phases:
            phase.export_atom_types = True
            if phase.data_based_on!="" and not phase.data_based_on in phases:
                phase.save_links = False        
        with zipfile.ZipFile(filename, 'w') as zfile:
            for phase in phases:
                zfile.writestr(phase.uuid, phase.dump_object())
        for phase in phases:
            phase.save_links = True
            phase.export_atom_types = False
        pyxrd_object_pool.restore_uuids()
        
    @classmethod
    def load_phases(cls, filename, parent=None):
        """
            Returns multiple phases loaded from a single file.
        """
        if zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename, 'r') as zfile:
                for uuid in zfile.namelist():
                    yield cls.load_object(zfile.open(uuid), parent=parent)
        else:
            yield cls.load_object(filename, parent=parent)

    def save_object(self, export=False, **kwargs):
        self.export_atom_types = export    
        self.save_links = not export
        retval = Storable.save_object(self, **kwargs)
        self.save_links = True
        self.export_atom_types = False
        return retval
    
    def json_properties(self):
        retval = Storable.json_properties(self)
        if not self.save_links:
            for prop in self.__model_intel__:
                if prop.inh_name:
                    retval[prop.inh_name] = False
            retval["based_on_uuid"] = ""
        else:
            retval["based_on_uuid"] = self.data_based_on.uuid if self.data_based_on else ""
        return retval

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------  
    """def get_lorentz_polarisation_factor(self, range_theta, S, S1S2):
        ss = max(self.data_sigma_star, 0.0000000000001)
        Q = S / (sqrt8 * np.sin(range_theta) * ss)
        T = erf(Q) * sqrt2pi / (2.0*ss * S) - 2.0*np.sin(range_theta) * (1.0- np.exp(-(Q**2.0))) / (S**2.0)
        return (1.0 + np.cos(2.0*range_theta)**2) * T / np.sin(range_theta)"""    
    
    __last_Tmean = None
    __last_Tmax = None
    __last_Tmin = None
    __last_Tdistr = None
    __last_Qdistr = None
    def _update_interference_distributions(self):
        Tmean = max(self.data_mean_CSDS, 1)
        Tmax = self.data_max_CSDS
        Tmin = self.data_min_CSDS

        if self.__last_Tmean != Tmean or self.__last_Tmax != Tmax or self.__last_Tmin != Tmin:
            a = 0.9485 * log(Tmean) - 0.017
            b = sqrt(0.1032*log(Tmean) + 0.0034)
            
            steps = int(Tmax - Tmin) + 1
            
            smq = 0
            q_log_distr = []
            TQDistr = dict()
            for i in range(steps):
                T = max(Tmin + i, 1e-50)
                q = lognormal(T, a, b)
                smq += q
                
                TQDistr[int(T)] = q
                
            Rmean = 0
            for T,q in TQDistr.iteritems():
                TQDistr[T] = q / smq
                Rmean += T*q
            Rmean /= smq
            self.__last_Tmean = Tmean
            self.__last_Tmax = Tmax
            self.__last_Tmin = Tmin
            self.__last_Trest = (TQDistr.items(), TQDistr, Rmean)
            
        return self.__last_Trest
       
    def get_CSDS_matrices(self, Q):
        Qn = np.empty((self.data_max_CSDS+1,), dtype=object)
        Qn[1] = np.copy(Q)
        for n in range(2, int(self.data_max_CSDS+1)):
            Qn[n] = mmult(Qn[n-1], Q)
        return Qn

       
    _cached_diffracted_intensities = None
    def get_diffracted_intensity (self, range_theta, range_stl, lpf_callback, quantity, correction_range):
        hsh = get_md5_hash(range_theta)
        if self._dirty:
            self._cached_diffracted_intensities = dict()
        if self.dirty or not hsh in self._cached_diffracted_intensities:
            #print "for specimen %s" % self
            
            stl_dim = range_stl.shape[0]
            repeat_to_stl = lambda arr: np.repeat(arr[np.newaxis,...], stl_dim, axis=0)
            
            #Get interference (log-normal) distribution:
            distr, ddict, real_mean = self._update_interference_distributions()
            
            #Get junction probabilities & weight fractions
            W, P = self.data_probabilities.get_distribution_matrix(), self.data_probabilities.get_probability_matrix()
            
            W = repeat_to_stl(W).astype(np.complex_)
            P = repeat_to_stl(P).astype(np.complex_)
            G = self.data_G

            #get structure factors and phase factors for individual components:
            #        components
            #       .  .  .  .  .  .
            #  stl  .  .  .  .  .  .
            #       .  .  .  .  .  .
            #
            shape = range_stl.shape + (G,)
            SF = np.zeros(shape, dtype=np.complex_)
            PF = np.zeros(shape, dtype=np.complex_)
            for i, component in enumerate(self.data_components._model_data):
                SF[:,i], PF[:,i] = component.get_factors(range_stl)
            intensity = np.zeros(range_stl.size, dtype=np.complex_)
            first = True

            rank = P.shape[1]
            reps = rank / G
                        
            #Create Phi & F matrices:        
            SFa = np.repeat(SF[...,np.newaxis,:], SF.shape[1], axis=1)
            SFb = np.transpose(np.conjugate(SFa), axes=(0,2,1)) #np.conjugate(np.repeat(SF[...,np.newaxis], SF.shape[1], axis=2)) 
                   
            F = np.repeat(np.repeat(np.multiply(SFb, SFa), reps, axis=2), reps, axis=1)

            #Create Q matrices:
            PF = np.repeat(PF[...,np.newaxis,:], reps, axis=1)
            Q = np.multiply(np.repeat(np.repeat(PF, reps, axis=2), reps, axis=1), P)
                              
            #Calculate the intensity:
            method = 0

            Qn = self.get_CSDS_matrices(Q)
                
            if method == 0:
                ################### FIRST WAY ###################                 
                SubTotal = np.zeros(Q.shape, dtype=np.complex)
                CSDS_I = repeat_to_stl(np.identity(rank, dtype=np.complex) * real_mean)
                for n in range(1, int(self.data_max_CSDS)+1):
                    factor = 0
                    for m in range(n+1, int(self.data_max_CSDS)+1):
                        factor += (m-n) * ddict[m]
                    SubTotal += 2 * factor * Qn[n]
                SubTotal = (CSDS_I + SubTotal)
                SubTotal = mmult(mmult(F, W), SubTotal)
                intensity = np.real(np.trace(SubTotal,  axis1=2, axis2=1))
            elif method == 1:
                ################### SCND WAY ################### #FIXME doesn't work for now
                SubTotal = np.zeros(Q.shape, dtype=np.complex_)
                I = repeat_to_stl(np.identity(rank))
                CSDS_I = repeat_to_stl(np.identity(rank, dtype=np.complex_) * real_mean)
                      
                IQ = (I-Q)
                IIQ = solve_division(I, IQ)
                IIQ2 = solve_division(I, mmult(IQ,IQ))
                R = np.zeros(Q.shape, dtype=np.complex_)
                for n in range(1, int(self.data_max_CSDS)):
                    R = (I + 2*Q*IIQ + (2 / n) * (Qn[n+1]-Q) * IIQ2) * ddict[n]
                    intensity += np.real(np.trace(mmult(mmult(F, W), R), axis1=2, axis2=1))
                
            lpf = lpf_callback(range_theta, self.data_sigma_star)
            
            scale = self.get_absolute_scale() * quantity
            self.dirty = False
            self._cached_diffracted_intensities[hsh] = intensity * correction_range * scale * lpf

        return self._cached_diffracted_intensities[hsh]

    def get_absolute_scale(self):
        mean_d001 = 0
        mean_volume = 0
        mean_density = 0
        W = self.data_probabilities.get_distribution_array()
        for wtfraction, component in zip(W, self.data_components._model_data):
            mean_d001 += (component.data_d001 * wtfraction)
            volume = component.get_volume()
            mean_volume += (volume * wtfraction)
            mean_density +=  (component.get_weight() * wtfraction / volume)
        if self.__last_Tmean == None or self.__last_Tmean != self.data_mean_CSDS:
            distr, ddict, real_mean = self._update_interference_distributions()
        else:
            distr, ddict, real_mean = self.__last_Trest
        return mean_d001 / (real_mean *  mean_volume**2 * mean_density)

    pass #end of class
