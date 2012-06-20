# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import time

import gtk
from gtkmvc.model import Model, Signal, Observer

import settings

from generic.utils import delayed
from generic.model_mixins import ObjectListStoreParentMixin
from generic.models import PyXRDModel, DefaultSignal, PropIntel, MultiProperty
from generic.treemodels import ObjectListStore, IndexListStore
from generic.io import Storable

from goniometer.models import Goniometer
from specimen.models import Specimen
from mixture.models import Mixture
from phases.models import Phase
from atoms.models import Atom, AtomType

class Project(PyXRDModel, Storable, ObjectListStoreParentMixin):


    #MODEL INTEL:
    __model_intel__ = [ #TODO add labels
        PropIntel(name="data_name",             inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_date",             inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_description",      inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_author",           inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="display_marker_angle",  inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="display_calc_color",    inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="display_exp_color",     inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="display_plot_offset",   inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="display_label_pos",     inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="axes_xscale",           inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=int,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="axes_xmin",             inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="axes_xmax",             inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="axes_xstretch",         inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="axes_yscale",           inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=int,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="axes_yvisible",         inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_specimens",        inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_phases",           inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=True,  observable=True,  has_widget=False),
        PropIntel(name="data_mixtures",         inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=True,  observable=True,  has_widget=False),
        PropIntel(name="data_atom_types",       inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=True,  observable=True,  has_widget=False),
        PropIntel(name="data_goniometer",       inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=True,  observable=True,  has_widget=False),
        PropIntel(name="needs_update",          inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),           
    ]
    
    #SIGNALS:
    needs_update = None

    #PROPERTIES:
    data_name = ""
    data_date = ""
    data_description = None
    data_author = ""
    
    _axes_xmin = 0.0
    _axes_xmax = 70.0
    _axes_xstretch = False
    _axes_yvisible = False
    _display_plot_offset = 0.75
    _display_marker_angle = 0.0
    _display_label_pos = 0.35
    @Model.getter("axes_xmin", "axes_xmax", "axes_xstretch", "axes_yvisible", "display_plot_offset", "display_marker_angle", "display_label_pos")
    def get_axes_value(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @Model.setter("axes_xmin", "axes_xmax", "axes_xstretch", "axes_yvisible", "display_plot_offset", "display_marker_angle", "display_label_pos")
    def set_axes_value(self, prop_name, value):
        if prop_name == "axes_xmin": value = max(value, 0.0)
        setattr(self, "_%s" % prop_name, value)
        self.needs_update.emit()

    def cbb_callback(self, prop_name, value):
        self.needs_update.emit()
    axes_xscale = MultiProperty(0, int, cbb_callback, { 0: "Auto", 1: "Manual" })
    axes_yscale = MultiProperty(0, int, cbb_callback, { 
        0: "Multi normalised",
        1: "Single normalised",
        2: "Unchanged raw counts"
    })
  
    
    _display_calc_color = "#FF0000"
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
            self.needs_update.emit()
    
    _data_specimens = None
    def get_data_specimens_value(self): return self._data_specimens
    
    _data_phases = None
    def get_data_phases_value(self): return self._data_phases
    
    _data_atom_types = None
    def get_data_atom_types_value(self): return self._data_atom_types
    
    _data_mixtures = None
    def get_data_mixtures_value(self): return self._data_mixtures
    
    data_goniometer = None
           
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name = "Project name",
            data_date = time.strftime("%d/%m/%Y"),
            data_description = "Project description",
            data_author = "Project author",
            data_goniometer = None, data_atom_types = None, data_phases = None,
            data_specimens = None, data_mixtures = None,
            display_marker_angle=None, display_plot_offset=None, 
            display_calc_color=None, display_exp_color=None, display_label_pos=None,
            axes_xscale=None, axes_xmin=None, axes_xmax=None, 
            axes_xstretch=None, axes_yscale=None, axes_yvisible=None,
            load_default_data=True):
        PyXRDModel.__init__(self)
        Storable.__init__(self)
        
        self.before_needs_update_lock = False
        self.needs_update = DefaultSignal(before=self.before_needs_update)

        self._data_atom_types = self.parse_liststore_arg(data_atom_types, IndexListStore, AtomType)        
        self._data_phases = self.parse_liststore_arg(data_phases, ObjectListStore, Phase)
        self._data_specimens = self.parse_liststore_arg(data_specimens, ObjectListStore, Specimen)
        self._data_mixtures = self.parse_liststore_arg(data_mixtures, ObjectListStore, Mixture)

        for phase in self._data_phases._model_data:
            phase.resolve_json_references()
            self.observe_model(phase)            
        for specimen in self._data_specimens.iter_objects():
            self.observe_model(specimen)

        self._data_atom_types.connect("item-removed", self.on_atom_type_item_removed)        
        self._data_phases.connect("item-removed", self.on_phase_item_removed)
        self._data_specimens.connect("item-removed", self.on_specimen_item_removed)
        self._data_mixtures.connect("item-removed", self.on_mixture_item_removed)
        
        self._data_atom_types.connect("item-inserted", self.on_atom_type_item_inserted)
        self._data_phases.connect("item-inserted", self.on_phase_item_inserted)
        self._data_specimens.connect("item-inserted", self.on_specimen_item_inserted)
        self._data_mixtures.connect("item-inserted", self.on_mixture_item_inserted)
        
        self.data_description = gtk.TextBuffer()
        
        self.data_name = data_name
        self.data_date = data_date
        self.data_description.set_text(data_description)
        self.data_author = data_author
        
        self.data_goniometer = self.parse_init_arg(data_goniometer, Goniometer(parent=self), child=True)
        
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

        if load_default_data and not settings.VIEW_MODE and \
            len(self._data_atom_types._model_data)==0: self.load_default_data()
        
    def load_default_data(self):
        import os
        AtomType.get_from_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/atomic scattering factors.atl')), self.data_atom_types.append)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    def on_phase_item_inserted(self, model, item, *data):
        if item.parent != self: item.parent = self
        self.observe_model(item)
    def on_atom_type_item_inserted(self, model, item, *data):
        if item.parent != self: item.parent = self
    def on_specimen_item_inserted(self, model, item, *data):
        if item.parent != self: item.parent = self
        self.observe_model(item)
    def on_mixture_item_inserted(self, model, item, *data):
        if item.parent != self: item.parent = self

    def on_phase_item_removed(self, model, item, *data):
        if item.data_based_on != None:
            item.data_based_on = None
        for phase in self._data_phases._model_data:
            if phase.data_based_on == item:
                phase.data_based_on = None
        for mixture in self.data_mixtures._model_data:
            mixture.uncheck_phase(item)
        if not self.before_needs_update_lock:
            self.needs_update.emit() #propagate signal
    def on_atom_type_item_removed(self, model, item, *data):
        if not self.before_needs_update_lock:
            self.needs_update.emit() #propagate signal
    def on_specimen_item_removed(self, model, item, *data):
        self.relieve_model(item)
        for mixture in self.data_mixtures._model_data:
            mixture.del_specimen(item)
        if not self.before_needs_update_lock:
            self.needs_update.emit() #propagate signal
    def on_mixture_item_removed(self, model, item, *data):
        pass

    @Observer.observe("needs_update", signal=True)
    def notify_needs_update(self, model, prop_name, info):
        if not self.before_needs_update_lock:
            self.needs_update.emit() #propagate signal

    @delayed("before_needs_update_lock")
    def before_needs_update(self, after):
        if not self.before_needs_update_lock:
            self.before_needs_update_lock = True
            t1 = time.time()
            for mixture in self.data_mixtures._model_data:
                mixture.apply_result()
            t2 = time.time()
            print '%s took %0.3f ms' % ("before_needs_update", (t2-t1)*1000.0)            
            #for specimen in self.data_specimens._model_data:
            #    specimen.calculate_pattern(self.data_goniometer.get_lorentz_polarisation_factor)
            after()
            self.before_needs_update_lock = False

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------

    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
   
    def get_max_intensity(self):
        max_intensity = 0
        if self.data_specimens:
            for specimen in self.data_specimens._model_data:
                max_intensity = max(specimen.max_intensity, max_intensity)
        return max_intensity
   
    def freeze_updates(self):
        self.before_needs_update_lock = True

    def thaw_updates(self):
        self.before_needs_update_lock = False

    
    pass #TODO: calculate all patterns
    
    
    

