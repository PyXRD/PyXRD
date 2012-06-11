# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import time
from warnings import warn

from math import sin, cos, pi, sqrt, exp

import gtk
from gtkmvc.model import Model
from gtkmvc.model import Signal, Observer

import numpy as np

from generic.metaclasses import pyxrd_object_pool
from generic.io import Storable, PyXRDDecoder
from generic.model_mixins import CSVMixin, ObjectListStoreChildMixin
from generic.models import XYData, ChildModel, PropIntel
from generic.treemodels import XYListStore

#TODO:
#  - cache calculated values
#  - add 'dirty' signal or something instead of parameters_changed for consistency with the rest of the code

class AtomType(ChildModel, ObjectListStoreChildMixin, Storable, CSVMixin):
    """
        AtomTypes contain all physical & chemical information for one element 
        in a certain state (e.g. Fe3+ & Fe2+ are two different AtomTypes)
    """

    #MODEL INTEL:
    __index_column__ = 'data_name'
    __parent_alias__ = 'project'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="data_atom_nr",      inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=int,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_name",         inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_weight",       inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_debye",        inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_par_c",        inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="parameters_changed",inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
    ] + [
        PropIntel(name="data_par_a%d" % i,  inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True) for i in [1,2,3,4,5]
    ] + [
        PropIntel(name="data_par_b%d" % i,  inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True) for i in [1,2,3,4,5]
    ]
    __csv_storables__ = [(prop.name, prop.name) for prop in __model_intel__ if prop.storable]

    
    #SIGNALS:
    parameters_changed = None
    
    #PROPERTIES:
    _data_name = ""
    def get_data_name_value(self): return self._data_name
    def set_data_name_value(self, value):
        self._data_name = value
        self.liststore_item_changed()
     
    data_atom_nr = 0
    data_weight = 0
    data_debye = 0
    
    _data_a = None
    _data_b = None
    _data_c = 0
    
    @Model.getter("data_par_a*", "data_par_b*", "data_par_c")
    def get_data_atom_par(self, prop_name):
        name = prop_name[9]
        if name == "a":
            index = int(prop_name[-1:])-1
            return self._data_a[index]
        elif name == "b":
            index = int(prop_name[-1:])-1
            return self._data_b[index]
        elif name == "c":
            return self._data_c
        return None
        
    @Model.setter("data_par_a*", "data_par_b*", "data_par_c")
    def set_data_atom_par(self, prop_name, value):
        name = prop_name[-2:-1]
        if name == "a":
            index = int(prop_name[-1:])-1
            self._data_a[index] = value
            self.parameters_changed.emit()
        elif name == "b":
            index = int(prop_name[-1:])-1
            self._data_b[index] = value
            self.parameters_changed.emit()
        elif name == "c":
            self._data_c = value
            self.parameters_changed.emit()            

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name, parent=None, data_debye=0, data_weight=0, data_atom_nr=0, data_par_c=0, data_par_a1=0, data_par_a2=0, data_par_a3=0, data_par_a4=0, data_par_a5=0, data_par_b1=0, data_par_b2=0, data_par_b3=0, data_par_b4=0, data_par_b5=0):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        self.parameters_changed = Signal()
        
        self.data_name = str(data_name) or self.data_name
        self.data_atom_nr = int(data_atom_nr) or self.data_atom_nr
        self.data_weight = float(data_weight) or self.data_weight
        self.data_debye = float(data_debye) or self.data_debye
        
        self._data_c = float(data_par_c)
        self._data_a = map(float, [data_par_a1, data_par_a2, data_par_a3, data_par_a4, data_par_a5])
        self._data_b = map(float, [data_par_b1, data_par_b2, data_par_b3, data_par_b4, data_par_b5])
        
    def __str__(self):
        return "<AtomType %s(%s)>" % (self.data_name, repr(self))
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_atomic_scattering_factors(self, stl_range): 
        f = np.zeros(stl_range.shape)
        #if self.cache and self.cache.has_key(stl): #TODO: check if this would be an improvement or not
        #    return self.cache[stl]
        angstrom_range = stl_range*0.05
        for i in range(0,5):
             f += self._data_a[i] * np.exp(-self._data_b[i]*(angstrom_range)**2)
        f += self._data_c
        b = self.data_debye
        f = f * np.exp(-float(b) * (angstrom_range)**2)
        #if self.cache:
        #    self.cache[stl] = f
        return f
        

class Atom(ChildModel, ObjectListStoreChildMixin, Storable):
    """
        Atoms have an atom type plus structural parameters (position and proportion)
    """
    #MODEL INTEL:
    __parent_alias__ = 'component'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="data_name",         inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_z",            inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_pn",           inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_atom_type",    inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=object, refinable=False, storable=False, observable=True,  has_widget=True),
    ]    
    
    #PROPERTIES:
    data_name = ""
    
    _data_z = 0
    def get_data_z_value(self): return self._data_z
    def set_data_z_value(self, value):
        if value != self._data_z:
            self._data_z = value
    
    _data_pn = 0
    def get_data_pn_value(self): return self._data_pn
    def set_data_pn_value(self, value):
        if value != self._data_pn:
            self._data_pn = value
    
    _atom_type_index = None
    _atom_type_uuid = None
    _data_atom_type = None
    _atom_type_name = None
    def get_data_atom_type_value(self): return self._data_atom_type
    def set_data_atom_type_value(self, value):
        if self._data_atom_type is not None:
            self.relieve_model(self._data_atom_type)
        self._data_atom_type = value
        if self._data_atom_type is not None:
            self.observe_model(self._data_atom_type)
         
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name=None, data_z=None, data_pn=None, data_atom_type=None, atom_type_index=None, atom_type_uuid=None, atom_type_name=None, parent=None):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
        self.data_name = data_name or self.data_name
        
        self.data_z = data_z or self._data_z
        self.data_pn = data_pn or self._data_pn
        self.data_atom_type = data_atom_type
        
        self._atom_type_uuid = atom_type_uuid or ""
        self._atom_type_name = atom_type_name or ""
        self._atom_type_index = atom_type_index if atom_type_index > -1 else None
         
    def __str__(self):
        return "<Atom %s(%s)>" % (self.data_name, repr(self))
    
    def _unattach_parent(self):
        self.data_atom_type = None
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
        if model == self.data_atom_type:
            self.data_atom_type = None
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------    
    def get_structure_factors(self, stl_range):
        asf = self.data_atom_type.get_atomic_scattering_factors(stl_range)
        return asf * self.data_pn * np.exp(2 * pi * self.data_z * stl_range * 1j)
    
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def resolve_json_references(self):
        if self._atom_type_uuid:
            self.data_atom_type = pyxrd_object_pool.get_object(self._atom_type_uuid)
        elif self._atom_type_name:
            for atom_type in self.component.phase.project.data_atom_types.iter_objects():
                if atom_type.data_name == self._atom_type_name:
                    self.data_atom_type = atom_type
        elif self._atom_type_index is not None:
            warn("The use of object indeces is deprected since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)        
            self.data_atom_type = self.component.phase.project.data_atom_types.get_user_data_from_index(self._atom_type_index)
        del self._atom_type_name
        del self._atom_type_uuid
        del self._atom_type_index        

    def json_properties(self):
        retval = Storable.json_properties(self)
        if self.component.phase.export_mode:
            retval["atom_type_name"] = self.data_atom_type.data_name if self.data_atom_type else ""
        else:
            retval["atom_type_uuid"] = self.data_atom_type.uuid if self.data_atom_type else ""
        return retval 
   
    @staticmethod
    def get_from_csv(filename, callback = None, parent=None):
        import csv
        atl_reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"') #TODO create csv dialect!
        header = True
        atoms = []
        
        types = dict()
        if parent != None:
            for atom_type in parent.phase.project.data_atom_types._model_data:
                if not atom_type.data_name in types:
                    types[atom_type.data_name] = atom_type
        
        for row in atl_reader:
            if not header and len(row)==4:
                name = row[0]
                z = float(row[1])
                pn = float(row[2])
                atom_type = types[row[3]] if parent is not None else None
                
                new_atom = Atom(data_name=name, data_z=z, data_pn=pn, data_atom_type=atom_type, parent=parent)
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
        atl_writer.writerow(["Atom","z","pn","Element"])
        for item in atoms:
            atl_writer.writerow([item.data_name, item.data_z, item.data_pn, item.data_atom_type.data_name])
            
    pass #end of class
        
