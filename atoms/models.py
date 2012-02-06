# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk

from gtkmvc.model import Model

import numpy as np

import time
from math import sin, cos, pi, sqrt, exp

from gtkmvc.model import Signal, Observer

from generic.io import Storable, PyXRDDecoder
from generic.models import XYData, ChildModel, CSVMixin
from generic.treemodels import XYListStore

#TODO:
#  - cache calculated values

class AtomType(ChildModel, Storable, CSVMixin):
    __index_column__ = 'data_name'

    __columns__ = [
        ('data_atom_nr', int),
        ('data_name', str),
        ('data_weight', float),
        ('data_par_c', float),
    ]
    __columns__ += [ ('data_par_a%d' % i, float) for i in [1,2,3,4,5] ]
    __columns__ += [ ('data_par_b%d' % i, float) for i in [1,2,3,4,5] ]

    __storables__ = [ key for key, val in __columns__]
    __csv_storables__ = zip(__storables__, __storables__)
    
    __observables__ = ["parameters_changed"] + __storables__
    
    data_name = ""    
    data_atom_nr = None
    data_weight = None
    
    parameters_changed = Signal()
    
    _data_a = None
    _data_b = None
    _data_c = None
    
    @Model.getter("data_par_a*", "data_par_b*", "data_par_c")
    def get_data_atom_type(self, prop_name):
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
    def set_data_atom_type(self, prop_name, value):
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
            
    def get_atomic_scattering_factors(self, stl_range): 
        f = np.zeros(stl_range.shape)
        #if self.cache and self.cache.has_key(stl): #TODO
        #    return self.cache[stl]
        for i in range(0,5):
             f += self._data_a[i] * np.exp(-self._data_b[i]*stl_range**2)
        f += self._data_c
        b = 0.0
        if "-" in self.data_name:
            b = 2.0
        elif "+" in self.data_name:
            b = 1.5
        f = f * np.exp(-b * stl_range**2)
        #if self.cache:
        #    self.cache[stl] = f
        return f

    def __init__(self, data_name, parent=None, data_weight=0, data_atom_nr=0, data_par_c=0, data_par_a1=0, data_par_a2=0, data_par_a3=0, data_par_a4=0, data_par_a5=0, data_par_b1=0, data_par_b2=0, data_par_b3=0, data_par_b4=0, data_par_b5=0):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
        self.data_name = str(data_name) or self.data_name
        self.data_atom_nr = int(data_atom_nr) or self.data_atom_nr
        self.data_weight = float(data_weight) or self.data_weight
        
        self._data_c = float(data_par_c)
        self._data_a = map(float, [data_par_a1, data_par_a2, data_par_a3, data_par_a4, data_par_a5])
        self._data_b = map(float, [data_par_b1, data_par_b2, data_par_b3, data_par_b4, data_par_b5])
        
    def __str__(self):
        return "<AtomType %s(%s)>" % (self.data_name, repr(self))
        
"""
    Atoms have an atom type plus structural parameters (position and proportion)
"""
class Atom(ChildModel, Storable):
    __observables__ = ( "data_*", )
    __columns__ = [
        ('data_name', str),
        ('data_z', float),
        ('data_pn', float),
        ('data_atom_type', AtomType) #rowref from AtomTypes property in project
    ]
    __storables__ = [key for key, val in __columns__ if key is not "data_atom_type"]
    
    data_name = ""
    
    _dirty_cache = False
    _memoize = None
    
    _data_z = 0
    @Model.getter("data_z")
    def get_data_z(self, prop_name):
        return self._data_z
    @Model.setter("data_z")
    def set_data_z(self, prop_name, value):
        if value != self._data_z:
            self._data_z = value
            self._dirty_cache = True
    
    _data_pn = 0
    @Model.getter("data_pn")
    def get_data_pn(self, prop_name):
        return self._data_pn
    @Model.setter("data_pn")
    def set_data_pn(self, prop_name, value):
        if value != self._data_pn:
            self._data_pn = value
            self._dirty_cache = True
    
    atom_type_observer = None
    class AtomTypeObserver(Observer):
        atom = None
        
        def __init__(self, atom, *args, **kwargs):
            self.atom = atom
            Observer.__init__(self, *args, **kwargs)
        
        @Observer.observe("removed", signal=True)
        def notification(self, model, prop_name, info):
            #model      = AtomType that we're observing
            #self.atom  = Atom that is observing the model
            if model == self.atom.data_atom_type: #this check is not 100% neccesary, but it can't hurt either
                self.atom.data_atom_type = None
    
    _atom_type_index = None
    _data_atom_type = None
    @Model.getter("data_atom_type")
    def get_data_atom_type(self, prop_name):
        return self._data_atom_type
    @Model.setter("data_atom_type")
    def set_data_atom_type(self, prop_name, value):
        if value != self._data_atom_type:
            if self.atom_type_observer == None:
                self.atom_type_observer = Atom.AtomTypeObserver(self)
            elif self._data_atom_type is not None:
                self.atom_type_observer.relieve_model(self._data_atom_type)
            self._data_atom_type = value
            self._dirty_cache = True
            if self._data_atom_type is not None:
                self.atom_type_observer.observe_model(self._data_atom_type)
    
    def _unattach_parent(self):
        self.data_atom_type = None
        ChildModel._unattach_parent(self)
      
    def __init__(self, data_name=None, data_z=None, data_pn=None, data_atom_type=None, atom_type_index=None, parent=None):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
        self.data_name = data_name or self.data_name
        
        self.data_z = data_z or self._data_z
        self.data_pn = data_pn or self._data_pn
        self.data_atom_type = data_atom_type
        
        self._atom_type_index = atom_type_index if atom_type_index > -1 else None
        
        self._memoize = dict()
         
    def __str__(self):
        return "<Atom %s(%s)>" % (self.data_name, repr(self))
            
    @staticmethod
    def from_json(**kwargs):
        return Atom(**kwargs)

    def resolve_json_references(self):
        if self._atom_type_index is not None:
            self.data_atom_type = self.parent.data_atom_types.get_user_data_from_index(self._atom_type_index)

    def json_properties(self):
        retval = Storable.json_properties(self)
        retval["atom_type_index"] = self.parent.data_atom_types.index(self.data_atom_type) if self.data_atom_type != None else -1
        return retval 
   
    @staticmethod
    def get_from_csv(filename, callback = None, parent=None):
        import csv
        atl_reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"') #TODO create csv dialect!
        header = True
        atoms = []
        
        types = dict()
        if parent != None:
            for atom_type in parent.data_atom_types._model_data:
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
    
       
    def get_structure_factors(self, stl_range):
        asf = self.data_atom_type.get_atomic_scattering_factors(stl_range)
        fac = 4 * pi * self.data_z * stl_range
        return asf * self.data_pn * np.exp(fac*1j)                      #(2*asf * self.data_pn * np.cos (fac), 2*asf * self.data_pn * np.sin (fac)) #TODO do we need to multiply with 2?
        
