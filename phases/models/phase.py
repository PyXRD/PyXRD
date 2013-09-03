# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from random import choice
import zipfile
from warnings import warn

from gtkmvc.model import Model, Observer, Signal

import numpy as np

from generic.io import storables, Storable
from generic.models import ChildModel, PropIntel
from generic.models.mixins import ObjectListStoreChildMixin, ObjectListStoreParentMixin
from generic.models.treemodels import ObjectListStore
from generic.models.metaclasses import pyxrd_object_pool
from generic.calculations.phases import get_diffracted_intensity, get_structure_factors
from generic.calculations.data_objects import PhaseData
from generic.refinement.mixins import RefinementGroup

from probabilities.models import get_correct_probability_model
from .CSDS import DritsCSDSDistribution
from .component import Component

@storables.register()
class Phase(ChildModel, Storable, ObjectListStoreParentMixin,
        ObjectListStoreChildMixin, RefinementGroup):

    #MODEL INTEL:
    __parent_alias__ = 'project'
    __model_intel__ = [
        PropIntel(name="name",                      data_type=unicode, label="Name",                is_column=True, has_widget=True, storable=True),
        PropIntel(name="display_color",             data_type=str,     label="Display color",       is_column=True, has_widget=True, widget_type='color', storable=True, inh_name="inherit_display_color", stor_name="_display_color"),
        PropIntel(name="based_on",                  data_type=object,  label="Based on phase",      is_column=True, has_widget=True, widget_type='combo'),
        PropIntel(name="G",                         data_type=int,     label="# of components",     is_column=True, has_widget=True, storable=True),
        PropIntel(name="R",                         data_type=int,     label="Reichweite",          is_column=True, has_widget=True),
        PropIntel(name="CSDS_distribution",         data_type=object,  label="CSDS Distribution",   is_column=True, has_widget=True, storable=True, refinable=True, inh_name="inherit_CSDS_distribution", stor_name="_CSDS_distribution"),
        PropIntel(name="sigma_star",                data_type=float,   label="$\sigma^*$ [°]",      is_column=True, has_widget=True, storable=True, refinable=True, minimum=0.0, maximum=90.0, inh_name="inherit_sigma_star", stor_name="_sigma_star"),
        PropIntel(name="inherit_display_color",     data_type=bool,    label="Inh. display color",  is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_CSDS_distribution", data_type=bool,    label="Inh. mean CSDS",      is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_sigma_star",        data_type=bool,    label="Inh. sigma star",     is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_probabilities",     data_type=bool,    label="Inh. probabilities",  is_column=True, has_widget=True, storable=True),
        PropIntel(name="probabilities",             data_type=object,  label="Probabilities",       is_column=True, has_widget=True, storable=True, refinable=True, inh_name="inherit_probabilities", stor_name="_probabilities"),
        PropIntel(name="components",                data_type=object,  label="Components",          is_column=True, has_widget=True, storable=True, refinable=True),
        PropIntel(name="needs_update",              data_type=object),
    ]
    __store_id__ = "Phase"
    
    _data_object = None
    @property
    def data_object(self):      

        self._data_object.valid_probs = (all(self.probabilities.P_valid) and all(self.probabilities.W_valid))
        
        if self._data_object.valid_probs:    
            self._data_object.sigma_star = self.sigma_star
            self._data_object.CSDS = self.CSDS_distribution.data_object

            self._data_object.G = self.G
            self._data_object.W = self.probabilities.get_distribution_matrix()
            self._data_object.P = self.probabilities.get_probability_matrix()

            self._data_object.components = [None] * len(self.components)
            for i, comp in enumerate(self.components.iter_objects()):
                self._data_object.components[i] = comp.data_object
        else:
            self._data_object.sigma_star = None
            self._data_object.CSDS = None
            self._data_object.G = None
            self._data_object.W = None
            self._data_object.P = None
            self._data_object.components = None
        
        return self._data_object
    
    #SIGNALS:
    needs_update = None
    
    #PROPERTIES:
    name = "Name of this phase"

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
        
        self._data_object = PhaseData()
        
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
    @Observer.observe("updated", signal=True)    
    def notify_needs_update(self, model, prop_name, info):
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
        pyxrd_object_pool.change_all_uuids()
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
        
    @classmethod
    def load_phases(cls, filename, parent=None):
        """
            Returns multiple phases loaded from a single file.
        """
        pyxrd_object_pool.change_all_uuids()
        if zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename, 'r') as zfile:
                for name in zfile.namelist():
                    #i, hs, uuid = name.partition("###")
                    #if uuid=='': uuid = i
                    yield cls.load_object(zfile.open(name), parent=parent)
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
        
    def get_diffracted_intensity(self, range_theta, range_stl, lpf_args, correction_range):
        """
            Calculates the diffracted intensity (relative scale) for a given
            theta-range, a matching sin(theta)/lambda range, phase quantity,
            while employing the passed lorentz-polarization factor callback and
            the passed correction factor.
            
            Will return zeros when the probability of this model is invalid
            
            Reference: X-Ray Diffraction by Disordered Lamellar Structures,
            V. Drits, C. Tchoubar - Springer-Verlag Berlin 1990
        """
        phase = self.data_object
        if phase.valid_probs:
            return get_diffracted_intensity.func(
                range_theta, range_stl, lpf_args, correction_range, phase
            )
        else:
            return get_diffracted_intensity.func(None, None, None, None, phase)


    pass #end of class
