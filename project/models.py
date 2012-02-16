# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.
import gtk

from gtkmvc import Observable
from gtkmvc.model import ListStoreModel, Model, Signal, Observer

import json
import time
from math import sin, cos, pi, sqrt

import settings

from generic.utils import interpolate
from generic.treemodels import ObjectListStore, IndexListStore
from generic.io import Storable

from goniometer.models import Goniometer
from specimen.models import Specimen
from phases.models import Phase
from atoms.models import Atom, AtomType

class Project(Model, Observable, Storable): 
    __observables__ = ( "data_name", "data_date", "data_description", "data_author", 
                        "data_goniometer",
                        "data_phases",
                        "data_specimens",
                        "data_atom_types",
                        "display_marker_angle",
                        "display_calc_color",
                        "display_exp_color" )
    __storables__ = __observables__

    data_name = ""
    data_date = ""
    data_description = None
    data_author = ""
    
    display_marker_angle = 0.0
    
    _display_calc_color = "#666666"
    @Model.getter("display_calc_color")
    def get_calc_color(self, prop_name):
            return self._display_calc_color
    @Model.setter("display_calc_color")
    def set_calc_color(self, prop_name, value):
        if value != self._display_calc_color:
            self._display_calc_color = value
            for specimen in self.data_specimens._model_data:
                specimen.data_calculated_pattern.color = value
    
    _display_exp_color = "#000000"
    @Model.getter("display_exp_color")
    def get_exp_color(self, prop_name):
            return self._display_exp_color
    @Model.setter("display_exp_color")
    def set_exp_color(self, prop_name, value):
        if value != self._display_exp_color:
            self._display_exp_color = value
            for specimen in self.data_specimens._model_data:
                specimen.data_experimental_pattern.color = value
    
    _data_specimens = None
    @Model.getter("data_specimens")
    def get_data_specimens(self, prop_name):
        return self._data_specimens
    
    _data_phases = None
    @Model.getter("data_phases")
    def get_data_phases(self, prop_name):
        return self._data_phases
    
    _data_atom_types = None
    @Model.getter("data_atom_types")
    def get_data_atom_types(self, prop_name):
        return self._data_atom_types
    
    data_goniometer = None
    
    specimen_observer = None
    class SpecimenObserver(Observer):
        project = None
        
        def __init__(self, project, *args, **kwargs):
            self.project = project
            Observer.__init__(self, *args, **kwargs)
        
        @Observer.observe("data_phase_added", signal=True)
        def notification(self, model, prop_name, info):
            self.project.add_phase(info["arg"])
    
    data_specimen_added = Signal()
    def add_specimen(self, specimen, silent=False, copy_phases=True):
        def copy_and_setup_observer(store, specimen, silent=False):
            if copy_phases:
                for phase in specimen.data_phases: self.add_phase(phase) 
            self.specimen_observer.observe_model(specimen)
        return self._add_item_to_store(self._data_specimens, specimen, 
                                       signal=self.data_specimen_added,
                                       callback=copy_and_setup_observer,
                                       silent=silent)
    data_specimen_removed = Signal()
    def del_specimen(self, specimen, silent=False):
        def detach_observer(store, specimen, silent=False):
            self.specimen_observer.relieve_model(specimen)
        return self._del_item_from_store(self._data_specimens, specimen, 
                                         signal=self.data_specimen_removed,
                                         callback=detach_observer,
                                         silent=silent)
    
    data_phase_added = Signal()
    def add_phase(self, phase, silent=False):
        return self._add_item_to_store(self._data_phases, phase, 
                                       signal=self.data_phase_added,
                                       silent=silent)
    data_phase_removed = Signal()
    def del_phase(self, phase, silent=False):
        def break_links(store, phase, silent=False):
            if phase.data_based_on != None:
                phase.data_based_on = None
        return self._del_item_from_store(self._data_phases, phase, 
                                         signal=self.data_phase_removed,
                                         callback=break_links,
                                         silent=silent)

    data_atom_type_added = Signal()
    def add_atom_type(self, atom_type, silent=False):
        atom_type.parent = self
        return self._add_item_to_store(self._data_atom_types, atom_type, 
                                       signal=self.data_atom_type_added,
                                       silent=silent)
    data_atom_type_removed = Signal()
    def del_atom_type(self, atom_type, silent=False):
        return self._del_item_from_store(self._data_atom_types, atom_type, 
                                         signal=self.data_atom_type_removed,
                                         silent=silent)

    #generic methods:
    def _add_item_to_store(self, store, item, signal=None, callback=None, silent=False):
        if not store.item_in_model(item):
            path = store.append(item)
            if callback != None and callable(callback):
                callback(store, item, silent)
            if item.parent != self:
                item.parent = self
            if signal != None and not silent:
                signal.emit(item)
            return path
        return None
   
    def _del_item_from_store(self, store, item, signal=None, callback=None, silent=False):
        if store.item_in_model(item):
            store.remove_item(item)
            if callback != None and callable(callback):
                callback(store, item, silent)
            if item.parent != None:
                item.parent = None
            if signal != None and not silent:
                signal.emit(item)
    
    def __init__(self, 
                 name = "Project name",
                 date = time.strftime("%d/%m/%Y"),
                 description = "Project description",
                 author = "Project author",
                 goniometer = None,
                 atom_types = None, data_phases = None, data_specimens = None,
                 display_marker_angle=None, display_calc_color=None, display_exp_color=None,
                 load_default_data=True):
        Model.__init__(self)
        Observable.__init__(self)
        Storable.__init__(self)
        
        self._data_specimens = data_specimens or ObjectListStore(Specimen)
        self._data_phases = data_phases or ObjectListStore(Phase)
        self._data_atom_types = atom_types or IndexListStore(AtomType)
        self.data_description = gtk.TextBuffer()
        
        self.specimen_observer = Project.SpecimenObserver(project=self)
        
        self.data_name = name
        self.data_date = date
        self.data_description.set_text(description)
        self.data_author = author
        
        self.data_goniometer = goniometer or Goniometer()
        
        self.display_marker_angle = display_marker_angle or self.display_marker_angle
        self.display_calc_color = display_calc_color or self.display_calc_color
        self.display_exp_color = display_exp_color or self.display_exp_color

        if load_default_data and not settings.VIEW_MODE: self.load_default_data()        
        
        #self.default_atom_type = AtomType("Oxygen", None)
        #FIXME self.data_atom_types.append(self.default_atom_type)
        
    def load_default_data(self):
        import os
        AtomType.get_from_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/atomic scattering factors.atl')), self.add_atom_type)
             
    @staticmethod          
    def from_json(data_name=None, data_date=None, data_description=None, data_author=None, 
                 data_goniometer=None, data_phases=None, data_specimens=None, data_atom_types=None,
                 display_marker_angle=None, display_calc_color=None, display_exp_color=None, **kwargs):
             
        data_goniometer = Goniometer.from_json(**data_goniometer['properties'])
              
        #Setup project   
        project = Project(name=data_name, date=data_date, description=data_description, author=data_author,
                          goniometer=data_goniometer, 
                          display_marker_angle=display_marker_angle, display_calc_color=display_calc_color, display_exp_color=display_exp_color,
                          load_default_data=False)
        
        #Create temporary ObjectListStore to transfer atom types to project
        atom_types = ObjectListStore.from_json(parent=project, **data_atom_types['properties'])
        for atom_type in atom_types._model_data:
            project.add_atom_type(atom_type, silent=True)
        
        #Create temporary ObjectListStore to transfer phases to project & resolve references
        data_phases = ObjectListStore.from_json(parent=project, **data_phases['properties'])
        for phase in data_phases._model_data:
            project.add_phase(phase, silent=True)
        for phase in project._data_phases._model_data: #FIXME we could solve this by making this sorted before export (place referenced specimens first)
            phase.resolve_json_references()
            
        #Create temporary ObjectListStore to transfer specimens to project, references to phases can be resolved immediately
        data_specimens = ObjectListStore.from_json(parent=project, **data_specimens['properties'])
        for specimen in data_specimens._model_data:
            project.add_specimen(specimen, silent=True, copy_phases=False)
        
        return project
    
    pass #TODO: calculate all patterns
    
    
    

