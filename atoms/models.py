# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import time
from warnings import warn

from math import sin, cos, pi, sqrt, exp

import gtk
from gtkmvc.model import Model
from gtkmvc.model import Signal, Observer

import numpy as np


from generic.io import storables, Storable, PyXRDDecoder
from generic.models import ChildModel, PropIntel
from generic.models.mixins import CSVMixin, ObjectListStoreChildMixin
from generic.models.metaclasses import pyxrd_object_pool
from generic.models.treemodels import XYListStore
from generic.calculations.data_objects import AtomTypeData, AtomData
from generic.calculations.atoms import get_structure_factor

@storables.register()
class AtomType(ChildModel, ObjectListStoreChildMixin, Storable, CSVMixin):
    """
        AtomTypes contain all physical & chemical information for one element 
        in a certain state (e.g. Fe3+ & Fe2+ are two different AtomTypes)
    """

    #MODEL INTEL:
    __index_column__ = 'name'
    __parent_alias__ = 'project'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="atom_nr",             is_column=True, data_type=int,     storable=True, has_widget=True),
        PropIntel(name="name",                is_column=True, data_type=unicode, storable=True, has_widget=True),
        PropIntel(name="charge",              is_column=True, data_type=float,   storable=True, has_widget=True),
        PropIntel(name="weight",              is_column=True, data_type=float,   storable=True, has_widget=True),
        PropIntel(name="debye",               is_column=True, data_type=float,   storable=True, has_widget=True),
        PropIntel(name="par_c",               is_column=True, data_type=float,   storable=True, has_widget=True),
        PropIntel(name="parameters_changed"),
    ] + [
        PropIntel(name="par_a%d" % i,         is_column=True, data_type=float, storable=True, has_widget=True) for i in xrange(1,6)
    ] + [
        PropIntel(name="par_b%d" % i,         is_column=True, data_type=float, storable=True, has_widget=True) for i in xrange(1,6)
    ]
    __csv_storables__ = [(prop.name, prop.name) for prop in __model_intel__ if prop.storable]
    __store_id__ = "AtomType"
    
    #SIGNALS:
    parameters_changed = None
    
    #PROPERTIES:
    _name = ""
    def get_name_value(self): return self._name
    def set_name_value(self, value):
        self._name = value
        self.liststore_item_changed()
     
    atom_nr = 0

    _data_object = None
    @property
    def data_object(self):
        return self._data_object
    
    @Model.getter("par_a*", "par_b*", "par_c", "debye", "charge", "weight")
    def get_atom_par(self, prop_name):
        if prop_name.startswith("par_"):
            name = prop_name[4]
            if name == "a":
                index = int(prop_name[-1:])-1
                return self._data_object.par_a[index]
            elif name == "b":
                index = int(prop_name[-1:])-1
                return self._data_object.par_b[index]
            elif name == "c":
                return self._data_object.par_c
        elif prop_name == "debye":
            return self._data_object.debye
        elif prop_name == "charge":
            return self._data_object.charge
        elif prop_name == "weight":
            return self._data_object.weight
        return None
        
    @Model.setter("par_a*", "par_b*", "par_c", "debye", "charge", "weight")
    def set_atom_par(self, prop_name, value):
        if prop_name.startswith("par_"):
            name = prop_name[4]
            if name == "a":
                index = int(prop_name[-1:])-1
                self._data_object.par_a[index] = float(value)
            elif name == "b":
                index = int(prop_name[-1:])-1
                self._data_object.par_b[index] = float(value)
            elif name == "c":
                self._data_object.par_c = value
        elif prop_name == "debye":
            self._data_object.debye = float(value)
        elif prop_name == "charge":
            self._data_object.charge = float(value)
        elif prop_name == "weight":
            self._data_object.weight = float(value)
        self.parameters_changed.emit()            

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    
    def __init__(self, name="", charge=0.0, debye=0.0, weight=0.0, atom_nr=0, par_c=0.0, 
            par_a1=0.0, par_a2=0.0, par_a3=0.0, par_a4=0.0, par_a5=0.0, 
            par_b1=0.0, par_b2=0.0, par_b3=0.0, par_b4=0.0, par_b5=0.0, 
            parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        self.parameters_changed = Signal()
        
        #Set up data object
        self._data_object = AtomTypeData(
            par_a = np.zeros(shape=(5,), dtype=float),
            par_b = np.zeros(shape=(5,), dtype=float),
            par_c = 0.0,
            debye = 0.0,
            charge = 0.0,
            weight = 0.0
        )
               
        #Set attributes:
        self.name = str(name or self.get_depr(kwargs, "", "data_name"))
        self.atom_nr = int(atom_nr or self.get_depr(kwargs, 0, "data_atom_nr") or 0)
        self.weight = float(weight or self.get_depr(kwargs, 0.0, "data_weight") or 0.0)
        self.charge = float(charge or self.get_depr(kwargs, 0.0, "data_charge") or 0.0)
        self.debye = float(debye or self.get_depr(kwargs, 0.0, "data_debye") or 0.0)
        
        for name in ["par_a1", "par_a2", "par_a3", "par_a4", "par_a5", "par_b1", "par_b2", "par_b3", "par_b4", "par_b5", "par_c"]:
            setattr(self, name, float(locals()[name] or self.get_depr(kwargs, 0.0, "data_%s" % name) or 0.0))
        
    def __str__(self):
        return "<AtomType %s (%s)>" % (self.name, id(self))
       
    pass #end of class
       
@storables.register()
class Atom(ChildModel, ObjectListStoreChildMixin, Storable):
    """
        Atoms have an atom type plus structural parameters (position and proportion)
    """
    #MODEL INTEL:
    __parent_alias__ = 'component'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="name",              data_type=unicode, is_column=True, storable=True, has_widget=True),
        PropIntel(name="default_z",         data_type=float,   is_column=True, storable=True, has_widget=True),
        PropIntel(name="z",                 data_type=float,   is_column=True, storable=False, has_widget=True),
        PropIntel(name="pn",                data_type=float,   is_column=True, storable=True, has_widget=True),
        PropIntel(name="atom_type",         data_type=object,  is_column=True, has_widget=True),
        PropIntel(name="stretch_values",    data_type=bool),
    ]    
    __store_id__ = "Atom"
    
    _data_object = None
    @property
    def data_object(self):
        self._data_object.atom_type = self.atom_type.data_object
        return self._data_object
    
    #PROPERTIES:
    name = ""
    
    _sf_array = None
    _atom_array = None
    
    _default_z = None
    def get_default_z_value(self):
        return self._data_object.default_z
    def set_default_z_value(self, value):
        if value != self._data_object.default_z:
            self._data_object.default_z = float(value)
            self.liststore_item_changed()

    _stretch_z = False
    def get_stretch_values_value(self): return bool(self._stretch_z)
    def set_stretch_values_value(self, value):
        if value != self._stretch_z:
            self._stretch_z = bool(value)
            self.liststore_item_changed()
    
    def get_z_value(self):
        if self.stretch_values and self.component!=None:
            lattice_d, factor = self.component.get_interlayer_stretch_factors()
            return float(lattice_d + (self.default_z - lattice_d) * factor)
        return self.default_z
    def set_z_value(self, value):
        warn("The z property can not be set!", DeprecationWarning)
    
    _pn = None
    def get_pn_value(self): return self._data_object.pn
    def set_pn_value(self, value):
        if value != self._data_object.pn:
            self._data_object.pn = float(value)
            self.liststore_item_changed()
    
    @property
    def weight(self):
        if self.atom_type!=None:
            return self.pn * self.atom_type.weight
        else:
            return 0.0
    
    _atom_type_index = None
    _atom_type_uuid = None
    _atom_type = None
    _atom_type_name = None
    def get_atom_type_value(self): return self._atom_type
    def set_atom_type_value(self, value):
        if self._atom_type is not None:
            self.relieve_model(self._atom_type)
        self._atom_type = value
        if self._atom_type is not None:
            self.observe_model(self._atom_type)
        self.liststore_item_changed()
         
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, name="", default_z=0.0, pn=0.0,
            atom_type=None, atom_type_index=-1, atom_type_uuid="", 
            atom_type_name="", stretch_values=False, parent=None, sf_view=None, **kwargs):  
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
              
        #Set up data object
        self._data_object = AtomData(
            default_z = 0.0,
            pn = 0.0
        )
               
        #Set attributes               
        self.name = str(name or self.get_depr(kwargs, "", "data_name"))
        
        self.stretch_values = stretch_values
        self.default_z = float(default_z or self.get_depr(kwargs, 0.0, "data_z", "z"))
        self.pn = float(pn or self.get_depr(kwargs, 0.0, "data_pn"))
        
        self.atom_type = atom_type or self.get_depr(kwargs, None, "data_atom_type")
        self._atom_type_uuid = atom_type_uuid
        self._atom_type_name = atom_type_name
        self._atom_type_index = atom_type_index if atom_type_index > -1 else None
         
    def __str__(self):
        return "<Atom %s(%s)>" % (self.name, repr(self))
    
    def _unattach_parent(self):
        self.atom_type = None
        ChildModel._unattach_parent(self)
         
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Observer.observe("removed", signal=True)
    def on_removed(self, model, prop_name, info):
        """
            This method observes the Atom types 'removed' signal,
            as such, if the AtomType gets removed from the parent project,
            it is also cleared from this Atom
        """
        if model == self.atom_type:
            self.atom_type = None
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------     
    def get_structure_factors(self, stl_range):
        if self.atom_type!=None:
            return float(get_structure_factor(stl_range, self.data_object))
        else:
            return 0.0

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def resolve_json_references(self):    
        if self._atom_type_uuid!="":
            self.atom_type = pyxrd_object_pool.get_object(self._atom_type_uuid)
        elif self._atom_type_name!="" or self._atom_type_index is not None:
            assert(self.component!=None)
            assert(self.component.phase!=None)
            assert(self.component.phase.project!=None)
            if self._atom_type_name!="":
                for atom_type in self.component.phase.project.atom_types.iter_objects():
                    if atom_type.name == self._atom_type_name:
                        self.atom_type = atom_type
            else:
                warn("The use of object indeces is deprected since version 0.4. \
                    Please switch to using object UUIDs.", DeprecationWarning)
                self.atom_type = self.component.phase.project.atom_types.get_user_data_from_path((self._atom_type_index,))
        self._atom_type_name = ""
        self._atom_type_uuid = ""
        self._atom_type_index = None        

    def json_properties(self):
        from phases.models import Phase
        retval = Storable.json_properties(self)
        if self.component==None or self.component.export_atom_types:
            retval["atom_type_name"] = self.atom_type.name if self.atom_type else ""
        else:
            retval["atom_type_uuid"] = self.atom_type.uuid if self.atom_type else ""
        return retval 
   
    @staticmethod
    def get_from_csv(filename, callback = None, parent=None):
        import csv
        atl_reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"') #TODO create csv dialect!
        header = True
        atoms = []
        
        types = dict()
        if parent != None:
            for atom_type in parent.phase.project.atom_types._model_data:
                if not atom_type.name in types:
                    types[atom_type.name] = atom_type
        
        for row in atl_reader:
            if not header and len(row)>=4:
                if len(row)==5:
                    name, z, def_z, pn, atom_type = row[0], float(row[1]), float(row[2]), float(row[3]), types[row[4]] if parent is not None else None
                else:
                    name, z, pn, atom_type = row[0], float(row[1]), float(row[2]), types[row[3]] if parent is not None else None
                    def_z = z
                
                if atom_type in types:
                    atom_type = types[atom_type]
                
                new_atom = Atom(name=name, z=z, default_z=def_z, pn=pn, atom_type=atom_type, parent=parent)
                atoms.append(new_atom)
                if callback is not None and callable(callback):
                    callback(new_atom)
                del new_atom
                
            header = False
        return atoms
        
    @staticmethod
    def save_as_csv(filename, atoms):
        import csv
        atl_writer = csv.writer(open(filename, 'wb'), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        atl_writer.writerow(["Atom","z", "def_z", "pn","Element"])
        for item in atoms:
            if item!=None and item.atom_type!=None:
                atl_writer.writerow([item.name, item.z, item.default_z, item.pn, item.atom_type.name])
            
    pass #end of class

