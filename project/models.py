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
from generic.models import add_cbb_props
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
                        "display_exp_color",
                        "display_plot_offset",
                        "display_label_pos",
                        "axes_xscale",
                        "axes_xmin",
                        "axes_xmax",
                        "axes_xstretch",
                        "axes_yscale",
                        "axes_yvisible" )
    __storables__ = __observables__

    data_name = ""
    data_date = ""
    data_description = None
    data_author = ""

       
    _axes_xscale = 0
    _axes_xscales = { 0: "Auto", 1: "Manual" }
    axes_xmin = 0.0
    axes_xmax = 70.0
    axes_xstretch = False
    
    _axes_yscale = 0
    _axes_yscales = { 0: "Multi normalised", 1: "Single normalised", 2: "Unchanged raw counts"} #, 4: "Custom (per specimen)" }
    axes_yvisible = False
    
    add_cbb_props(("axes_xscale", int, None), ("axes_yscale", int, None))
    
    display_plot_offset = 0.75
    _display_calc_color = "#666666"
    _display_exp_color = "#000000"    
    @Model.getter("display_calc_color", "display_exp_color")
    def get_color(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @Model.setter("display_calc_color", "display_exp_color")
    def set_color(self, prop_name, value):
        if value != getattr(self, "_%s" % prop_name):
            setattr(self, "_%s" % prop_name, value)
            calc = ("calc" in prop_name)
            for specimen in self.data_specimens._model_data:
                if calc:
                    specimen.data_calculated_pattern.color = value
                else:
                    specimen.data_experimental_pattern.color = value
    
    display_marker_angle = 0.0
    display_label_pos = 0.35
    
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
                 data_name = "Project name",
                 data_date = time.strftime("%d/%m/%Y"),
                 data_description = "Project description",
                 data_author = "Project author",
                 data_goniometer = None,
                 data_atom_types = None, data_phases = None, data_specimens = None,
                 display_marker_angle=None, display_calc_color=None, display_exp_color=None, display_plot_offset=None, display_label_pos=None,
                 axes_xscale=None, axes_xmin=None, axes_xmax=None, axes_xstretch=None, axes_yscale=None, axes_yvisible=None,
                 load_default_data=True):
        Model.__init__(self)
        Observable.__init__(self)
        Storable.__init__(self)
        
        self._data_specimens = data_specimens or ObjectListStore(Specimen)
        self._data_phases = data_phases or ObjectListStore(Phase)
        self._data_atom_types = data_atom_types or IndexListStore(AtomType)
        self.data_description = gtk.TextBuffer()
        
        self.specimen_observer = Project.SpecimenObserver(project=self)
        
        self.data_name = data_name
        self.data_date = data_date
        self.data_description.set_text(data_description)
        self.data_author = data_author
        
        self.data_goniometer = data_goniometer or Goniometer()
        
        self.display_marker_angle = display_marker_angle or self.display_marker_angle
        self.display_calc_color = display_calc_color or self.display_calc_color
        self.display_exp_color = display_exp_color or self.display_exp_color
        self.display_plot_offset = display_plot_offset or self.display_plot_offset
        self.display_label_pos = display_label_pos or self.display_label_pos
        
        self.axes_xscale = axes_xscale or self.axes_xscale
        self.axes_xmin = axes_xmin or self.axes_xmin
        self.axes_xmax = axes_xmax or self.axes_xmax
        self.axes_xstretch = axes_xstretch or self.axes_xstretch
        self.axes_yscale = axes_yscale or self.axes_yscale
        self.axes_yvisible = axes_yvisible or self.axes_yvisible

        if load_default_data and not settings.VIEW_MODE: self.load_default_data()
        
    def load_default_data(self):
        import os
        AtomType.get_from_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/atomic scattering factors.atl')), self.add_atom_type)
             
    @staticmethod          
    def from_json(**kwargs): #TODO wraps this in kwargs!!
        
        sargs = dict()
        for key in ("data_atom_types", "data_goniometer", "data_phases", "data_specimens"):
            sargs[key] = kwargs[key]
            del kwargs[key]
             
        data_goniometer = Goniometer.from_json(**sargs["data_goniometer"]['properties'])

        #Setup project   
        project = Project(load_default_data=False, **kwargs)
        
        #Create temporary ObjectListStore to transfer atom types to project
        atom_types = ObjectListStore.from_json(parent=project, **sargs["data_atom_types"]['properties'])
        for atom_type in atom_types._model_data:
            project.add_atom_type(atom_type, silent=True)
        del atom_types
        
        #Create temporary ObjectListStore to transfer phases to project & resolve references
        data_phases = ObjectListStore.from_json(parent=project, **sargs["data_phases"]['properties'])
        for phase in data_phases._model_data:
            project.add_phase(phase, silent=True)
        del data_phases
        for phase in project._data_phases._model_data: #FIXME we could solve this by making this sorted before export (place referenced specimens first)
            phase.resolve_json_references()
            
        #Create temporary ObjectListStore to transfer specimens to project, references to phases can be resolved immediately
        data_specimens = ObjectListStore.from_json(parent=project, **sargs["data_specimens"]['properties'])
        for specimen in data_specimens._model_data:
            project.add_specimen(specimen, silent=True, copy_phases=False)
        del data_specimens
        
        return project
    
    def get_max_intensity(self):
        max_intensity = 0
        for specimen in self.data_specimens._model_data:
            max_intensity = max(specimen.max_intensity, max_intensity)
        return max_intensity
    
    pass #TODO: calculate all patterns
    
    
    

