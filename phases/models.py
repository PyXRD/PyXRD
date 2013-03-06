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


from generic.utils import print_timing, get_md5_hash
from generic.custom_math import mmult, mdot, mtim, solve_division
from generic.io import Storable, PyXRDDecoder
from generic.models import ChildModel, PropIntel
from generic.models.mixins import ObjectListStoreChildMixin, ObjectListStoreParentMixin
from generic.models.treemodels import ObjectListStore
from generic.models.metaclasses import pyxrd_object_pool

from atoms.models import Atom
from probabilities.models import get_correct_probability_model
from phases.CSDS_models import DritsCSDSDistribution
from phases.atom_relations import AtomRelation, AtomRatio, AtomContents, ComponentPropMixin
from mixture.refinement import RefinementGroup, RefinementValue

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
    #SIGNALS:
    
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
            retval["prop"] = [retval["prop"][0].uuid if retval["prop"][0] else None, retval["prop"][1]]
        return retval
        
    def resolve_json_references(self):
        if self._temp_prop:
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

UnitCellProperty.register_storable()

class Component(ChildModel, Storable, ObjectListStoreChildMixin,
        ObjectListStoreParentMixin, RefinementGroup):

    #MODEL INTEL:
    __parent_alias__ = "phase"
    __model_intel__ = [
        PropIntel(name="name",                      data_type=unicode,label="Name",                   is_column=True, has_widget=True, storable=True),
        PropIntel(name="linked_with",               data_type=object, label="Linked with",            widget_type='combo', is_column=True, has_widget=True),
        PropIntel(name="d001",                      data_type=float,  label="Cell length c [nm]",     is_column=True, has_widget=True, storable=True, refinable=True, minimum=0.0, maximum=5.0,  inh_name="inherit_d001"),
        PropIntel(name="default_c",                 data_type=float,  label="Default c length [nm]",  is_column=True, has_widget=True, storable=True, minimum=0.0, maximum=5.0,  inh_name="inherit_default_c"),
        PropIntel(name="delta_c",                   data_type=float,  label="C length dev. [nm]",     is_column=True, has_widget=True, storable=True, refinable=True, minimum=0.0, maximum=0.05, inh_name="inherit_delta_c"),
        PropIntel(name="ucp_a",                     data_type=object, label="Cell length a [nm]",     is_column=True, has_widget=True, storable=True, refinable=True, inh_name="inherit_ucp_a"),
        PropIntel(name="ucp_b",                     data_type=object, label="Cell length b [nm]",     is_column=True, has_widget=True, storable=True, refinable=True, inh_name="inherit_ucp_b"),
        PropIntel(name="inherit_d001",              data_type=bool,   label="Inh. cell length c",     is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_ucp_b",             data_type=bool,   label="Inh. cell length b",     is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_ucp_a",             data_type=bool,   label="Inh. cell length a",     is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_default_c",         data_type=bool,   label="Inh. default length c",  is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_delta_c",           data_type=bool,   label="Inh. c length dev.",     is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_layer_atoms",       data_type=bool,   label="Inh. layer atoms",       is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_interlayer_atoms",  data_type=bool,   label="Inh. interlayer atoms",  is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_atom_relations",    data_type=bool,   label="Inh. atom relations",    is_column=True, has_widget=True, storable=True),
        PropIntel(name="atom_relations",            data_type=object, label="Atom relations",         is_column=True, has_widget=True, storable=True, refinable=True, inh_name="inherit_atom_relations"),
        PropIntel(name="layer_atoms",               data_type=object, label="Layer atoms",            is_column=True, has_widget=True, storable=True, inh_name="inherit_layer_atoms"),
        PropIntel(name="interlayer_atoms",          data_type=object, label="Interlayer atoms",       is_column=True, has_widget=True, storable=True, inh_name="inherit_interlayer_atoms"),
        PropIntel(name="needs_update",              data_type=object),
        PropIntel(name="dirty",                     data_type=bool),        
    ]
    __store_id__ = "Component"

    #SIGNALS:
    needs_update = None

    #PROPERTIES:
    name = "Name of this component"
       
    _dirty = True
    def get_dirty_value(self): return (self._dirty)
    def set_dirty_value(self, value):
        if value!=self._dirty: 
            self._dirty = value
            if self._dirty:
                self._cached_factors = dict()
    
    
    @property
    def _inherit_ucp_a(self):
        return self._ucp_a.inherited
    @_inherit_ucp_a.setter
    def _inherit_ucp_a(self, value):
        self._ucp_a.inherited = value
    @property
    def _inherit_ucp_b(self):
        return self._ucp_b.inherited
    @_inherit_ucp_b.setter
    def _inherit_ucp_b(self, value):
        self._ucp_b.inherited = value

    _inherit_d001 = False
    _inherit_default_c = False
    _inherit_delta_c = False
    _inherit_layer_atoms = False
    _inherit_interlayer_atoms = False
    _inherit_atom_relations = False
    @Model.getter(*[prop.inh_name for prop in __model_intel__ if prop.inh_name])
    def get_inherit_prop(self, prop_name): return getattr(self, "_%s" % prop_name)
    @Model.setter(*[prop.inh_name for prop in __model_intel__ if prop.inh_name])
    def set_inherit_prop(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        self.dirty = True
        self.liststore_item_changed()
        self.needs_update.emit()

    _linked_with = None
    _linked_with_index = None
    _linked_with_uuid = None
    def get_linked_with_value(self): return self._linked_with
    def set_linked_with_value(self, value):
        if value != self._linked_with:
            if self._linked_with != None:
                self.relieve_model(self._linked_with)
            self._linked_with = value
            if self._linked_with!=None:
                self.observe_model(self._linked_with)
            else:
                for prop in self.__inheritables__:
                    setattr(self, "inherit_%s" % prop, False)
            self.liststore_item_changed()
            self.dirty = True
            
    #INHERITABLE PROPERTIES:   
    _ucp_a = None
    _ucp_b = None
    _d001 = 1.0
    _default_c = 1.0
    _delta_c = 0.0
    _layer_atoms = None
    _interlayer_atoms = None
    _atom_relations = None
    @Model.getter(*[prop.name for prop in __model_intel__ if prop.inh_name])
    def get_inheritable(self, prop_name):
        inh_name = "inherit_%s" % prop_name
        if self.linked_with != None and getattr(self, inh_name):
            return getattr(self.linked_with, prop_name)
        else:
            return getattr(self, "_%s" % prop_name)
    @Model.setter(*[prop.name for prop in __model_intel__ if prop.inh_name])
    def set_inheritable(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        if prop_name=="default_c":
            setattr(self, "_%s" % prop_name, float(value))
            for atom in self.interlayer_atoms.iter_objects():
                atom.liststore_item_changed()
        self.dirty = True
        self.liststore_item_changed()
        self.needs_update.emit()
    
    #Instance flag indicating wether or not linked_with & inherit flags should be saved
    save_links = True
    #Class flag indicating wether or not atom types in the component should be
    #exported using their name rather then their project-uuid.
    export_atom_types = False
    
    #REFINEMENT GROUP IMPLEMENTATION:
    @property
    def refine_title(self):
        return self.name
        
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, name=None, ucp_a=None, ucp_b=None,
                 d001=None, default_c=None, delta_c=None,
                 layer_atoms=None, interlayer_atoms=None, atom_relations=None,
                 inherit_ucp_a=False, inherit_ucp_b=False, inherit_d001=False,
                 inherit_default_c=False, inherit_delta_c=False,
                 inherit_layer_atoms=False, inherit_interlayer_atoms=False, inherit_atom_relations=False, 
                 linked_with_index = None, linked_with_uuid = None, parent=None, **kwargs):
        super(Component, self).__init__(parent=parent)
        
        self.name = name or self.get_depr(kwargs, self.name, "data_name")

        self.needs_update = Signal()
        self.dirty = True
        self._cached_factors = dict()
        
        layer_atoms = layer_atoms or self.get_depr(kwargs, None, "data_layer_atoms")
        self._layer_atoms = self.parse_liststore_arg(layer_atoms, ObjectListStore, Atom)
        interlayer_atoms = interlayer_atoms or self.get_depr(kwargs, None, "data_interlayer_atoms")        
        self._interlayer_atoms = self.parse_liststore_arg(interlayer_atoms, ObjectListStore, Atom)
                           
        atom_relations = atom_relations or self.get_depr(kwargs, None, "data_atom_relations")
        self._atom_relations = self.parse_liststore_arg(atom_relations, ObjectListStore, AtomRelation)

        atom_ratios = kwargs.get("atom_ratios", kwargs.get("data_atom_ratios", None))
        if atom_ratios!=None:
            decoder = PyXRDDecoder(parent=parent)
            for json_ratio in atom_ratios["properties"]["model_data"]:
                props = json_ratio["properties"]
                
                ratio = AtomRatio(
                    name=props.get("name", props.get("data_name", "")),
                    value=props.get("ratio", props.get("data_ratio", 0.0)),
                    sum=props.get("sum", props.get("data_sum", 0.0)),
                    prop1=props.get("prop1", props.get("data_prop1", None)),
                    prop2=props.get("prop2", props.get("data_prop2", None)),
                    parent=self)
                self._atom_relations.append(ratio)
        
        for atom in self._interlayer_atoms.iter_objects():
            atom.stretch_values = True
            
        for relation in self._atom_relations.iter_objects():
            relation.resolve_relations()
            self.observe_model(relation)

        self._layer_atoms.connect("item-inserted", self.on_layer_atom_inserted)
        self._layer_atoms.connect("item-removed", self.on_layer_atom_removed)
        self._layer_atoms.connect("row-changed", self.on_layer_atom_changed)
        
        self._interlayer_atoms.connect("item-inserted", self.on_interlayer_atom_inserted)
        self._interlayer_atoms.connect("item-removed", self.on_child_item_removed)
        self._interlayer_atoms.connect("row-changed", self.on_item_changed)
        
        self._atom_relations.connect("item-removed", self.on_atom_relation_removed)
        self._atom_relations.connect("item-inserted", self.on_atom_relation_inserted)
    
        self._d001 = d001 or self.get_depr(kwargs, self.d001, "data_d001")
        
        self._default_c = float(default_c or self.get_depr(kwargs, self._d001, "data_default_c"))
        self._delta_c = delta_c or self.get_depr(kwargs, self._delta_c, "data_delta_c")
        self._update_lattice_d()
        
        ucp_a = ucp_a or self.get_depr(kwargs, None, "data_ucp_a", "data_cell_a")
        if isinstance(ucp_a, float):
            ucp_a = UnitCellProperty(name="cell length a", value=ucp_a, parent=self)
            inherit_ucp_a = kwargs.pop("inherit_cell_a", inherit_ucp_a)
        self._ucp_a = self.parse_init_arg(ucp_a, UnitCellProperty(parent=self, name="Cell length a [nm]"), child=True, name="Cell length a [nm]")
                
        ucp_b = ucp_b or self.get_depr(kwargs, None, "data_ucp_b", "data_cell_b")
        if isinstance(ucp_b, float):
            ucp_b = UnitCellProperty(name="cell length b", value=ucp_b, parent=self)
            inherit_ucp_b = kwargs.pop("inherit_cell_b", inherit_ucp_b)
        self._ucp_b = self.parse_init_arg(ucp_b, UnitCellProperty(parent=self, name="Cell length b [nm]"), child=True, name="Cell length b [nm]")
               
        self._linked_with_uuid = linked_with_uuid if linked_with_uuid!=None else ""
        self._linked_with_index = linked_with_index if linked_with_index > -1 else None
        
        self._inherit_d001 = inherit_d001
        self._inherit_ucp_a = inherit_ucp_a
        self._inherit_ucp_b = inherit_ucp_b
        self._inherit_default_c = inherit_default_c
        self._inherit_delta_c = inherit_delta_c        
        self._inherit_layer_atoms = inherit_layer_atoms          
        self._inherit_interlayer_atoms = inherit_interlayer_atoms
        self._inherit_atom_relations = inherit_atom_relations

    def __str__(self):
        return ("<Component %s" % self.name) + \
            (" linked with %s>" % self.linked_with if self.linked_with else ">")

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Observer.observe("dirty", assign=True)
    def notify_dirty_changed(self, model, prop_name, info):
        if model.dirty: self.dirty = True
        pass
        
    @Observer.observe("changed", signal=True)
    def notify_emit_changed(self, model, prop_name, info):
        if isinstance(model, AtomRelation) or isinstance(model, Atom):
            self._apply_atom_relations()
        self.dirty = True
        self.needs_update.emit()
        
    @Observer.observe("removed", signal=True)
    def notify_emit_removed(self, model, prop_name, info):
        if model!=self and self.linked_with!=None and self.linked_with==model:
            self.linked_with=None
            self.dirty = True
            self.needs_update.emit()
    
    def on_item_changed(self, *args):
        self.dirty = True
        self.needs_update.emit()
    
    def on_layer_atom_changed(self, *args):
        self._update_lattice_d()
        self.on_item_changed(*args)
    def on_layer_atom_inserted(self, model, atom):
        atom.parent = self
        self.on_layer_atom_changed(model, atom)
    def on_layer_atom_removed(self, model, atom):
        atom.parent = None
        self.on_layer_atom_changed(model, atom)
    
    def on_interlayer_atom_inserted(self, model, atom):
        atom.stretch_values = True
        atom.parent = self
        self.on_item_changed(model, atom)
    
    def on_atom_relation_inserted(self, model, item):
        self.observe_model(item)
        self._apply_atom_relations()
        self.on_child_item_inserted(model, item)
        
    def on_atom_relation_removed(self, model, item):
        self.relieve_model(item)
        self._apply_atom_relations()
        self.on_child_item_removed(model, item)
    
    def on_child_item_inserted(self, model, item):
        item.parent = self
        self.on_item_changed(model, item)
    def on_child_item_removed(self, model, item):
        item.parent = None
        self.on_item_changed(model, item)
    
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------  
    def resolve_json_references(self):
        for atom in self._layer_atoms._model_data:
            atom.resolve_json_references()
        for atom in self._interlayer_atoms._model_data:
            atom.resolve_json_references()
        
        self._ucp_a.resolve_json_references()
        self._ucp_a.update_value()
        self._ucp_b.resolve_json_references()        
        self._ucp_b.update_value()
        
        if self._linked_with_uuid:
            self.linked_with = pyxrd_object_pool.get_object(self._linked_with_uuid)
        elif self._linked_with_index != None and self._linked_with_index != -1:
            warn("The use of object indeces is deprected since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
            self.linked_with = self.parent.based_on.components.get_user_from_index(self._linked_with_index)
        del self._linked_with_uuid
        del self._linked_with_index
             
    @classmethod
    def save_components(cls, components, filename):
        """
            Saves multiple components to a single file.
        """
        pyxrd_object_pool.stack_uuids()
        Component.export_atom_types = True
        for comp in components:
            comp.save_links = False
        with zipfile.ZipFile(filename, 'w') as zfile:
            for component in components:
                zfile.writestr(component.uuid, component.dump_object())
        for comp in components:
            comp.save_links = True
        Component.export_atom_types = False
        pyxrd_object_pool.restore_uuids()
        
    @classmethod
    def load_components(cls, filename, parent=None):
        """
            Returns multiple components loaded from a single file.
        """
        if zipfile.is_zipfile(filename):
            pyxrd_object_pool.stack_uuids()
            with zipfile.ZipFile(filename, 'r') as zfile:
                for uuid in zfile.namelist():
                    yield cls.load_object(zfile.open(uuid), parent=parent)
            pyxrd_object_pool.restore_uuids()
        else:
            yield cls.load_object(filename, parent=parent)
                        
    def json_properties(self):
        retval = Storable.json_properties(self)
        if self.phase==None or not self.save_links:
            for prop in self.__model_intel__:
                if prop.inh_name:
                    retval[prop.inh_name] = False
        else:
            retval = Storable.json_properties(self)
            retval["linked_with_uuid"] = self.linked_with.uuid if self.linked_with!=None else ""
        return retval
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------  
    def get_factors(self, range_stl):
        hsh = get_md5_hash(range_stl)
        if self.dirty or not hsh in self._cached_factors:
            sf_tot = np.zeros(range_stl.shape, dtype=np.complex_)
            for atom in self.layer_atoms._model_data:
                sf_tot += atom.get_structure_factors(range_stl)
            for atom in self.interlayer_atoms._model_data:
                sf_tot += atom.get_structure_factors(range_stl)
            self._cached_factors[hsh] = sf_tot, np.exp(2*pi*range_stl * (self.d001*1j - pi*self.delta_c*range_stl))
            self.dirty = False
        return self._cached_factors[hsh]

    def _update_lattice_d(self):
        self._lattice_d = 0.0
        for atom in self.layer_atoms.iter_objects():
            self._lattice_d = max(self._lattice_d, atom.default_z)

    def _apply_atom_relations(self):
        for relation in self.atom_relations.iter_objects():
            relation.apply_relation()

    def get_interlayer_stretch_factors(self):
        try:
            return self._lattice_d, (self.cell_c - self._lattice_d) / (self.default_c - self._lattice_d)
        except:
            raise
            return None
    
    @property
    def cell_a(self):
        return self._ucp_a.value
    @property
    def cell_b(self):
        return self._ucp_b.value
    @property
    def cell_c(self):
        return self.d001

    def get_volume(self):
        return max(self.cell_a * self.cell_b * self.cell_c, 1e-25)

    def get_weight(self):
        weight = 0
        for atom in (self.layer_atoms._model_data + self.interlayer_atoms._model_data):
            weight += atom.weight
        return weight

Component.register_storable()

class Phase(ChildModel, Storable, ObjectListStoreParentMixin,
        ObjectListStoreChildMixin, RefinementGroup):

    #MODEL INTEL:
    __parent_alias__ = 'project'
    __model_intel__ = [
        PropIntel(name="name",                      data_type=unicode, label="Name",                is_column=True, has_widget=True, storable=True),
        PropIntel(name="display_color",             data_type=str,     label="Display color",       is_column=True, has_widget=True, widget_type='color', storable=True, inh_name="inherit_display_color"),
        PropIntel(name="based_on",                  data_type=object,  label="Based on phase",      is_column=True, has_widget=True, widget_type='combo'),
        PropIntel(name="G",                         data_type=int,     label="# of components",     is_column=True, has_widget=True, storable=True),
        PropIntel(name="R",                         data_type=int,     label="Reichweite",          is_column=True, has_widget=True),
        PropIntel(name="CSDS_distribution",         data_type=object,  label="CSDS Distribution",   is_column=True, has_widget=True, storable=True, refinable=True, inh_name="inherit_CSDS_distribution"),
        PropIntel(name="sigma_star",                data_type=float,   label="$\sigma^*$ [°]",      is_column=True, has_widget=True, storable=True, refinable=True, minimum=0.0,   maximum=90.0, inh_name="inherit_sigma_star"),
        PropIntel(name="inherit_display_color",     data_type=bool,    label="Inh. display color",  is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_CSDS_distribution", data_type=bool,    label="Inh. mean CSDS",      is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_sigma_star",        data_type=bool,    label="Inh. sigma star",     is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_probabilities",     data_type=bool,    label="Inh. probabilities",  is_column=True, has_widget=True, storable=True),
        PropIntel(name="probabilities",             data_type=object,  label="Probabilities",       is_column=True, has_widget=True, storable=True, refinable=True, inh_name="inherit_probabilities",),
        PropIntel(name="components",                data_type=object,  label="Components",          is_column=True, has_widget=True, storable=True, refinable=True),
        PropIntel(name="needs_update",              data_type=object),
        PropIntel(name="dirty",                     data_type=bool),
    ]
    __store_id__ = "Phase"
    
    #SIGNALS:
    needs_update = None
    
    #PROPERTIES:
    name = "Name of this phase"
    
    _dirty = True
    def get_dirty_value(self): return self._dirty
    def set_dirty_value(self, value):
        if value!=self._dirty:
            self._dirty = value

    @property
    def _inherit_CSDS_distribution(self):
        return self._CSDS_distribution.inherited
    @_inherit_CSDS_distribution.setter
    def _inherit_CSDS_distribution(self, value):
        self._CSDS_distribution.inherited = value
    _inherit_display_color = False
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
    _based_on = None
    def get_based_on_value(self): return self._based_on
    def set_based_on_value(self, value):
        if self._based_on!=None:
            self.relieve_model(self._based_on)
        if value == None or value.get_based_on_root() == self or value.parent != self.parent:
            value = None
        if value != self._based_on:
            self._based_on = value
            for component in self.components._model_data:
                component.linked_with = None
        if self._based_on!=None:
            self.observe_model(self._based_on)
        else:
            for prop in self.__model_intel__:
                if prop.inh_name: setattr(self, prop.inh_name, False)
        self.dirty = True
        self.needs_update.emit()
        self.liststore_item_changed()
    def get_based_on_root(self):
        if self.based_on != None:
            return self.based_on.get_based_on_root()
        else:
            return self
                
    #INHERITABLE PROPERTIES:
    _sigma_star = 3.0
    sigma_star_range = [0,90]
    _CSDS_distribution = None
    _probabilities = None
    _display_color = "#FFB600"
    @Model.getter(*[prop.name for prop in __model_intel__ if prop.inh_name])
    def get_inheritable(self, prop_name):
        inh_name = "inherit_%s" % prop_name
        if self.based_on is not None and getattr(self, inh_name):
            return getattr(self.based_on, prop_name)
        else:
            return getattr(self, "_%s" % prop_name)
            
    def set_probabilities_value(self, value):
        if self._probabilities:
            self.relieve_model(self._probabilities)
            self._probabilities.parent = None
        self._probabilities = value
        if self._probabilities:
            self._probabilities.update()
            self._probabilities.parent = self
            self.observe_model(self._probabilities)
        self.dirty = True
        self.needs_update.emit()
        self.liststore_item_changed()
            
    def set_CSDS_distribution_value(self, value):
        if self._CSDS_distribution:
            self.relieve_model(self._CSDS_distribution)
            self._CSDS_distribution.parent = None
        self._CSDS_distribution = value
        if self._CSDS_distribution:
            self._CSDS_distribution.parent = self
            self.observe_model(self._CSDS_distribution)
        self.dirty = True
        self.needs_update.emit()
        self.liststore_item_changed()
            
    def set_display_color_value(self, value):
        if self._display_color != value:
            self._display_color = value
            self.needs_update.emit()
            self.liststore_item_changed()
        
    def set_sigma_star_value(self, value):
        value = float(value)
        if self._sigma_star != value:
            self._sigma_star = value
            self.dirty = True
            self.needs_update.emit()
            self.liststore_item_changed()
    
    _components = None    
    def get_components_value(self): return self._components
    def set_components_value(self, value):
        if self._components != None:
            for comp in self._components._model_data: self.relieve_model(comp)
        self._components = value
        if self._components != None:
            for comp in self._components._model_data: self.observe_model(comp)
        self.dirty = True
        self.liststore_item_changed()
    def get_G_value(self):
        if self.components != None:
            return len(self.components._model_data)
        else:
            return 0
            
    _R = 0
    def get_R_value(self):
        if self.probabilities:
            return self.probabilities.R
    
    #Flag indicating wether or not the links (based_on and linked_with) should
    #be saved as well.
    save_links = True
    
    line_colors = [
        "#004488",
        "#FF4400",
        "#559911",
        "#770022",
        "#AACC00",
        "#441177",
    ]
    
    #REFINEMENT GROUP IMPLEMENTATION:
    @property
    def refine_title(self):
        return self.name
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, name=None, display_color=None, sigma_star=None, 
                 G=None, R=None, based_on_index = None, based_on_uuid = None,
                 CSDS_distribution=None, mean_CSDS=None,
                 probabilities=None, components=None,
                 inherit_display_color=False, inherit_sigma_star=False,
                 inherit_CSDS_distribution=False, inherit_probabilities=False, 
                 parent=None, **kwargs):
        super(Phase, self).__init__(parent=parent)
        
        self._dirty = True
        self._cached_diffracted_intensities = dict()  
        
        self.needs_update = Signal()
        
        self.name = name or self.get_depr(kwargs, self.name, "data_name")
        
        mean_CSDS = mean_CSDS or self.get_depr(kwargs, 10, "data_mean_CSDS")
        
        CSDS_distribution = CSDS_distribution or self.get_depr(kwargs, None, "data_CSDS_distribution")
        self.CSDS_distribution = self.parse_init_arg(
            CSDS_distribution, DritsCSDSDistribution(parent=self, average=mean_CSDS), child=True)
        self.inherit_CSDS_distribution = inherit_CSDS_distribution
            
        self._display_color = display_color or choice(self.line_colors)
        self._sigma_star = sigma_star or self.get_depr(kwargs, self.sigma_star, "data_sigma_star")
        
        self.inherit_display_color = inherit_display_color       
        self.inherit_sigma_star = inherit_sigma_star

        components = components or self.get_depr(kwargs, None, "data_components")
        self.components = self.parse_liststore_arg(
            components, ObjectListStore, Component)
        G = G or self.get_depr(kwargs, 0, "data_G")
        R = R or self.get_depr(kwargs, 0, "data_R")
        if G != None and G > 0:
            for i in range(len(self.components._model_data), G):
                new_comp = Component("Component %d" % (i+1), parent=self)
                self.components.append(new_comp)
                self.observe_model(new_comp)
        
        probabilities = probabilities or self.get_depr(kwargs, None, "data_probabilities")
        self.probabilities = self.parse_init_arg(probabilities,
            get_correct_probability_model(self, R, G), child=True)
        self.probabilities.update() #force an update
        self.inherit_probabilities = inherit_probabilities

        self._based_on_uuid = based_on_uuid if based_on_uuid!=None else ""
        self._based_on_index = based_on_index if based_on_index > -1 else None

    def __str__(self):
        return ("<Phase %s" % self.name) + \
            (" based on %s>" % self.based_on if self.based_on else ">")

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
            self.based_on = pyxrd_object_pool.get_object(self._based_on_uuid)
        elif self._based_on_index != None and self._based_on_index != -1:
            warn("The use of object indeces is deprected since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
            self.based_on = self.parent.phases.get_user_from_index(self._based_on_index)
        del self._based_on_index
        del self._based_on_uuid
        for component in self.components._model_data:
            component.resolve_json_references()

    @classmethod
    def save_phases(cls, phases, filename):
        """
            Saves multiple phases to a single file.
        """
        pyxrd_object_pool.stack_uuids()
        for phase in phases:
            if phase.based_on!="" and not phase.based_on in phases:
                phase.save_links = False
            Component.export_atom_types = True
            for component in phase.components.iter_objects():
                component.save_links = phase.save_links
                
        ordered_phases = list(phases) # make a copy               
        if len(phases) > 1:
            for phase in phases:
                if phase.based_on in phases:
                    index = ordered_phases.index(phase)
                    index2 = ordered_phases.index(phase.based_on)
                    if index < index2:
                        ordered_phases.remove(phase.based_on)
                        ordered_phases.insert(index, phase.based_on)
                
        with zipfile.ZipFile(filename, 'w') as zfile:
            for i, phase in enumerate(ordered_phases):
                zfile.writestr("%d###%s" % (i, phase.uuid), phase.dump_object())
        for phase in ordered_phases:
            phase.save_links = True
            for component in phase.components.iter_objects():
                component.save_links = True
            Component.export_atom_types = False
        pyxrd_object_pool.restore_uuids()
        
    @classmethod
    def load_phases(cls, filename, parent=None):
        """
            Returns multiple phases loaded from a single file.
        """
        if zipfile.is_zipfile(filename):
            pyxrd_object_pool.stack_uuids()
            with zipfile.ZipFile(filename, 'r') as zfile:
                for name in zfile.namelist():
                    #i, hs, uuid = name.partition("###")
                    #if uuid=='': uuid = i
                    yield cls.load_object(zfile.open(name), parent=parent)
            pyxrd_object_pool.restore_uuids()
        else:
            yield cls.load_object(filename, parent=parent)

    def save_object(self, export=False, **kwargs):
        for component in self.components:
            component.export_atom_types = export
            component.save_links = not export
        self.save_links = not export
        retval = Storable.save_object(self, **kwargs)
        self.save_links = True
        for component in self.components:
            component.export_atom_types = False
            component.save_links = True
        return retval
    
    def json_properties(self):
        retval = Storable.json_properties(self)
        if not self.save_links:
            for prop in self.__model_intel__:
                if prop.inh_name:
                    retval[prop.inh_name] = False
            retval["based_on_uuid"] = ""
        else:
            retval["based_on_uuid"] = self.based_on.uuid if self.based_on else ""
        return retval

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------  
    def _update_interference_distributions(self):
        return self.CSDS_distribution.distrib
       
    def get_Q_matrices(self, Q):
        Qn = np.empty((self.CSDS_distribution.maximum+1,), dtype=object)
        Qn[1] = np.copy(Q)
        for n in range(2, int(self.CSDS_distribution.maximum+1)):
            Qn[n] = mmult(Qn[n-1], Q)
        return Qn
       
    _cached_diffracted_intensities = None
    def get_diffracted_intensity(self, range_theta, range_stl, lpf_callback, quantity, correction_range):
        """
            Calculates the diffracted intensity (relative scale) for a given
            theta-range, a matching sin(theta)/lambda range, phase quantity,
            while employing the passed lorentz-polarization factor callback and
            the passed correction factor.
            
            Will return zeros when the probability of this model is invalid
            
            Caches the result to improve speed, to force an update, set the 
            dirty flag of this phase to True.
            
            Reference: X-Ray Diffraction by Disordered Lamellar Structures,
            V. Drits, C. Tchoubar - Springer-Verlag Berlin 1990
        """
        hsh = get_md5_hash(range_theta)
        if self.dirty:
            self._cached_diffracted_intensities = dict()
        if not hsh in self._cached_diffracted_intensities:
            #Check probability model, if invalid return zeros instead of the actual pattern:
            if not (all(self.probabilities.P_valid) and all(self.probabilities.W_valid)):
                self._cached_diffracted_intensities[hsh] = np.zeros_like(range_theta)
            else:
                #Create a helper function to 'expand' certain arrays, for 
                # results which are independent of the 2-theta range
                stl_dim = range_stl.shape[0]
                repeat_to_stl = lambda arr: np.repeat(arr[np.newaxis,...], stl_dim, axis=0)
                
                #Get interference (log-normal) distribution:
                distr, ddict, real_mean = self._update_interference_distributions()
                
                #Get junction probabilities & weight fractions
                W, P = self.probabilities.get_distribution_matrix(), self.probabilities.get_probability_matrix()
                
                W = repeat_to_stl(W).astype(np.complex_)
                P = repeat_to_stl(P).astype(np.complex_)
                G = self.G

                #get structure factors and phase factors for individual components:
                #        components
                #       .  .  .  .  .  .
                #  stl  .  .  .  .  .  .
                #       .  .  .  .  .  .
                #
                shape = range_stl.shape + (G,)
                SF = np.zeros(shape, dtype=np.complex_)
                PF = np.zeros(shape, dtype=np.complex_)
                for i, component in enumerate(self.components._model_data):
                    SF[:,i], PF[:,i] = component.get_factors(range_stl)
                intensity = np.zeros(range_stl.size, dtype=np.complex_)
                first = True

                rank = P.shape[1]
                reps = rank / G
                            
                #Create Phi & F matrices:        
                SFa = np.repeat(SF[...,np.newaxis,:], SF.shape[1], axis=1)
                SFb = np.transpose(np.conjugate(SFa), axes=(0,2,1))
                       
                F = np.repeat(np.repeat(np.multiply(SFb, SFa), reps, axis=2), reps, axis=1)

                #Create Q matrices:
                PF = np.repeat(PF[...,np.newaxis,:], reps, axis=1)
                Q = np.multiply(np.repeat(np.repeat(PF, reps, axis=2), reps, axis=1), P)
                                  
                #Calculate the intensity:
                Qn = self.get_Q_matrices(Q)
                sub_total = np.zeros(Q.shape, dtype=np.complex)
                CSDS_I = repeat_to_stl(np.identity(rank, dtype=np.complex) * real_mean)
                for n in range(self.CSDS_distribution.minimum, int(self.CSDS_distribution.maximum)+1):
                    progression_factor = 0
                    for m in range(n+1, int(self.CSDS_distribution.maximum)+1):
                        progression_factor += (m-n) * ddict[m]
                    sub_total += 2 * progression_factor * Qn[n]
                sub_total = (CSDS_I + sub_total)
                sub_total = mmult(mmult(F, W), sub_total)
                intensity = np.real(np.trace(sub_total,  axis1=2, axis2=1))
                    
                lpf = lpf_callback(range_theta, self.sigma_star)
                
                scale = self.get_absolute_scale() * quantity
                self.dirty = False
                self._cached_diffracted_intensities[hsh] = intensity * correction_range * scale * lpf

        return self._cached_diffracted_intensities[hsh]

    def get_absolute_scale(self):
        mean_d001 = 0
        mean_volume = 0
        mean_density = 0
        W = self.probabilities.get_distribution_array()
        for wtfraction, component in zip(W, self.components._model_data):
            mean_d001 += (component.d001 * wtfraction)
            volume = component.get_volume()
            mean_volume += (volume * wtfraction)
            mean_density +=  (component.get_weight() * wtfraction / volume)
        distr, ddict, real_mean = self._update_interference_distributions()
        return mean_d001 / (real_mean *  mean_volume**2 * mean_density)

    pass #end of class
    
Phase.register_storable()
