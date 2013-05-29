# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os
from math import pi, log

from gtkmvc.model import Signal, Observer

import numpy as np

import settings
from generic.utils import print_timing, u
from generic.io import storables, Storable
from generic.models import ExperimentalLine, CalculatedLine, ChildModel, PropIntel
from generic.models.mixins import ObjectListStoreChildMixin, ObjectListStoreParentMixin
from generic.models.treemodels import ObjectListStore, XYListStore
from generic.peak_detection import peakdetect

from markers import Marker
from statistics import Statistics

@storables.register()
class Specimen(ChildModel, Storable, ObjectListStoreParentMixin, ObjectListStoreChildMixin):
    #MODEL INTEL:
    __parent_alias__ = 'project'
    __model_intel__ = [
        PropIntel(name="name",                 label="Name",                               data_type=unicode,    is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="sample_name",          label="Sample",                             data_type=unicode,    is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="label",                label="Label",                              data_type=unicode,    is_column=True),        
        PropIntel(name="sample_length",        label="Sample length [cm]",                 data_type=float,  minimum=0.0,     is_column=True,  storable=True,    has_widget=True),
        PropIntel(name="abs_scale",            label="Absolute scale [counts]",            data_type=float,  minimum=0.0,     is_column=True,  storable=True,    has_widget=True),
        PropIntel(name="bg_shift",             label="Background shift [counts]",          data_type=float,  minimum=0.0,     is_column=True,  storable=True,    has_widget=True),
        PropIntel(name="absorption",           label="Absorption coeff. (µ*g)",            data_type=float,  minimum=0.0,     is_column=True,  storable=True,    has_widget=True),
        PropIntel(name="display_calculated",   label="Display calculated diffractogram",   data_type=bool,   is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="display_experimental", label="Display experimental diffractogram", data_type=bool,   is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="display_phases",       label="Display phases seperately",          data_type=bool,   is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="display_stats_in_lbl", label="Display Rp in label",                data_type=bool,   is_column=True,  storable=True,   has_widget=True),       
        PropIntel(name="display_vshift",       label="Vertical shift of the plot",         data_type=float,  is_column=True,  storable=True,   has_widget=True),        
        PropIntel(name="display_vscale",       label="Vertical scale of the plot",         data_type=float,  is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="calculated_pattern",   label="Calculated diffractogram",           data_type=object, is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="experimental_pattern", label="Experimental diffractogram",         data_type=object, is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="exclusion_ranges",     label="Excluded ranges",                    data_type=object, is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="markers",              label="Markers",                            data_type=object, is_column=True,  storable=True),
        PropIntel(name="statistics",           label="Statistics",                         data_type=object, is_column=True),
        PropIntel(name="exp_cap_value",        label="Cut-off value",                      data_type=float,   is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="calc_color",           label="Calculated color",                   data_type=str,    is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="inherit_calc_color",   label="Use default color",                  data_type=bool,   is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="exp_color",            label="Experimental color",                 data_type=str,    is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="inherit_exp_color",    label="Use default color",                  data_type=bool,   is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="calc_lw",              label="Linewidth for calculated lines",     data_type=float,  is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="inherit_calc_lw",      label="Use default linewidth",              data_type=bool,   is_column=True,  storable=True,   has_widget=True),        
        PropIntel(name="exp_lw",               label="Linewidth for experimental lines",   data_type=float,  is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="inherit_exp_lw",       label="Use default linewidth",              data_type=bool,   is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="needs_update",                                                     data_type=object),
    ]
    __store_id__ = "Specimen"

    #SIGNALS:
    needs_update = None

    #PROPERTIES:
    _sample_name = u""
    _name = u""
    _display_calculated = True
    _display_experimental = True
    _display_vshift = 0.0
    _display_vscale = 1.0
    _display_phases = False
    _display_stats_in_lbl = True
    @ChildModel.getter("sample_name", "name", "display_vshift", "display_vscale",
         "display_phases", "display_stats_in_lbl",
         "display_calculated", "display_experimental")
    def get_name(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @ChildModel.setter("sample_name", "name", "display_vshift", "display_vscale",
        "display_phases", "display_stats_in_lbl",
        "display_calculated", "display_experimental")
    def set_name(self, prop_name, value):
        if self.get_prop_intel_by_name(prop_name).data_type==float:
            try: value = float(value)
            except ValueError: return
        setattr(self, "_%s" % prop_name, value)
        self.liststore_item_changed()
        self.needs_update.emit()
 
    def get_label_value(self):
        if not settings.VIEW_MODE and self.display_stats_in_lbl:
            return self.sample_name + "\nRp = %.1f%%" % self.statistics.Rp
        else:
            return self.sample_name
 
    _calculated_pattern = None
    def get_calculated_pattern_value(self): return self._calculated_pattern
    def set_calculated_pattern_value(self, value):
        if self._calculated_pattern != None: self.relieve_model(self._calculated_pattern)
        self._calculated_pattern = value
        if self._calculated_pattern != None:
            self.observe_model(self._calculated_pattern)
            self.calculated_pattern.color = self.calc_color
    _experimental_pattern = None
    def get_experimental_pattern_value(self): return self._experimental_pattern
    def set_experimental_pattern_value(self, value):
        if self._experimental_pattern != None: self.relieve_model(self._experimental_pattern)
        self._experimental_pattern = value
        if self._experimental_pattern != None: 
            self.observe_model(self._experimental_pattern)
            self.experimental_pattern.color = self.exp_color
    
    _exclusion_ranges = None
    def get_exclusion_ranges_value(self): return self._exclusion_ranges
    def set_exclusion_ranges_value(self, value):
        if value != self._exclusion_ranges:
            if self._exclusion_ranges!=None:
                pass
            self._exclusion_ranges = value
            if self._exclusion_ranges!=None:
                pass
    
    _sample_length = 1.25
    _abs_scale = 1.0
    _bg_shift = 0.0
    _absorption = 0.9
    @ChildModel.getter("sample_length", "abs_scale", "bg_shift", "absorption")
    def get_sample_length_value(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @ChildModel.setter("sample_length", "abs_scale", "bg_shift", "absorption")
    def set_sample_length_value(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        if self.parent:
            for phase in self.parent.phases.iter_objects():
                phase.dirty=True
        self.needs_update.emit()
    
    statistics = None
    
    _inherit_calc_lw = True
    def get_inherit_calc_lw_value(self):
        return self._inherit_calc_lw
    def set_inherit_calc_lw_value(self, value):
        if value != self._inherit_calc_lw:
            self._inherit_calc_lw = value
            if self.calculated_pattern != None:
                self.calculated_pattern.lw = float(self.calc_lw)
           
    _calc_lw = 2.0
    def get_calc_lw_value(self):
        if self.inherit_calc_lw and self.parent!=None:
            return self.parent.display_calc_lw
        else:
            return self._calc_lw
    def set_calc_lw_value(self, value):
        if value != self._calc_lw:
            self._calc_lw = float(value)
            self.calculated_pattern.lw = float(self.calc_lw)

    _inherit_exp_lw = True
    def get_inherit_exp_lw_value(self):
        return self._inherit_exp_lw
    def set_inherit_exp_lw_value(self, value):
        if value != self._inherit_exp_lw:
            self._inherit_exp_lw = value
            if self.experimental_pattern != None:
                self.experimental_pattern.lw = float(self.exp_lw)

    _exp_lw = 2.0
    def get_exp_lw_value(self):
        if self.inherit_exp_lw and self.parent!=None:
            return self.parent.display_exp_lw
        else:
            return self._exp_lw
    def set_exp_lw_value(self, value):
        if value != self._exp_lw:
            self._exp_lw = float(value)
            self.experimental_pattern.lw = float(self.exp_lw)
    
    _inherit_calc_color = True
    def get_inherit_calc_color_value(self): return self._inherit_calc_color
    def set_inherit_calc_color_value(self, value):
        if value != self._inherit_calc_color:
            self._inherit_calc_color = value
            if self.calculated_pattern != None:
                self.calculated_pattern.color = self.calc_color
    
    _calc_color = "#666666"
    def get_calc_color_value(self):
        if self.inherit_calc_color and self.parent!=None:
            return self.parent.display_calc_color
        else:
            return self._calc_color
    def set_calc_color_value(self, value):
        if value != self._calc_color:
            self._calc_color = value
            self.calculated_pattern.color = self.calc_color
            
    _inherit_exp_color = True
    def get_inherit_exp_color_value(self):
        return self._inherit_exp_color
    def set_inherit_exp_color_value(self, value):
        if value != self._inherit_exp_color:
            self._inherit_exp_color = value
            if self.experimental_pattern != None:
                self.experimental_pattern.color = self.exp_color
            
    _exp_color = "#000000"
    def get_exp_color_value(self):
        if self.inherit_exp_color and self.parent!=None:
            return self.parent.display_exp_color
        else:
            return self._exp_color
    def set_exp_color_value(self, value):
        if value != self._exp_color:
            self._exp_color = value
            self.experimental_pattern.color = value      
     
    @property
    def exp_cap_value(self):
        """The value used to cut-off experimental data"""
        return self.experimental_pattern.cap_value
    @exp_cap_value.setter
    def exp_cap_value(self, value):
        self.experimental_pattern.cap_value = value
       
    _markers = None
    def get_markers_value(self): return self._markers
    
    @property
    def max_intensity(self):
        """The maximum intensity of the current profile (both calculated and observed"""
        if self.experimental_pattern and self.calculated_pattern:
            return max(np.max(self.experimental_pattern.max_intensity), np.max(self.calculated_pattern.max_intensity))
        else:
            return 0.0
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, name=u"", sample_name=u"", sample_length=0.0, abs_scale=1.0,
                 bg_shift=0.0, absorption = 0.9, display_calculated=True,
                 display_experimental=True, display_phases=False, display_stats_in_lbl=True,
                 display_vshift=0.0, display_vscale=1.0, 
                 experimental_pattern = None, calculated_pattern = None, exclusion_ranges = None, markers = None,
                 phase_indeces=None, phase_uuids=None, calc_color=None, exp_color=None, exp_cap_value=None,
                 calc_lw=None, exp_lw=None, inherit_calc_lw=True, inherit_exp_lw=True,
                 inherit_calc_color=True, inherit_exp_color=True, parent=None, **kwargs):
        super(Specimen, self).__init__(parent=parent)
               
        self.needs_update = Signal()
               
        self.name = name or self.get_depr(kwargs, u"", "data_name")
        self.sample_name = sample_name or self.get_depr(kwargs, u"", "data_sample")
        self.sample_length = float(sample_length or self.get_depr(kwargs, 1.25, "data_sample_length"))
        self.absorption = float(absorption)
        self.abs_scale  = float(abs_scale or self.get_depr(kwargs, 1.0, "data_abs_scale"))
        self.bg_shift = float(bg_shift or self.get_depr(kwargs, 0.0, "data_bg_shift"))

        self.inherit_calc_color = inherit_calc_color
        self.inherit_exp_color = inherit_exp_color
        self.inherit_calc_lw = inherit_calc_lw
        self.inherit_exp_lw = inherit_exp_lw

        self._calc_color = calc_color or self.calc_color
        self._exp_color = exp_color or self.exp_color          
        self._calc_lw = calc_lw or self.calc_lw
        self._exp_lw = exp_lw or self.exp_lw  

        ##
        ## This is terrible: linewidth and color should ideally be stored in the pattern object itself...
        ##

        calculated_pattern = calculated_pattern or self.get_depr(kwargs, None, "data_calculated_pattern")
        if isinstance(calculated_pattern, dict) and "type" in calculated_pattern and calculated_pattern["type"]=="generic.models/XYData":
            calculated_pattern["properties"]["lw"] = self.calc_lw
            calculated_pattern["properties"]["color"] = self.calc_color
            self.calculated_pattern = CalculatedLine.from_json(parent=self, **calculated_pattern["properties"])
        else:
            initkwargs = dict(label="Calculated Profile",
                color=self.calc_color, lw=self.calc_lw, parent=self)
            self.calculated_pattern = self.parse_init_arg(
                calculated_pattern,
                CalculatedLine(**initkwargs),
                child=True, **initkwargs)

        experimental_pattern = experimental_pattern or self.get_depr(kwargs, None, "data_experimental_pattern")
        if isinstance(experimental_pattern, dict) and "type" in experimental_pattern and experimental_pattern["type"]=="generic.models/XYData":
            experimental_pattern["properties"]["lw"] = self.exp_lw
            experimental_pattern["properties"]["color"] = self.exp_color
            self.experimental_pattern = ExperimentalLine.from_json(parent=self, **experimental_pattern["properties"])
        else:
            initkwargs = dict(label="Experimental Profile",
                color=self.exp_color, lw=self.exp_lw, parent=self)
            self.experimental_pattern = self.parse_init_arg(
                experimental_pattern, 
                ExperimentalLine(**initkwargs), 
                child=True, **initkwargs)

        self.exp_cap_value = exp_cap_value or 0.0
        
        exclusion_ranges = exclusion_ranges or self.get_depr(kwargs, None, "data_exclusion_ranges")
        self.exclusion_ranges = self.parse_init_arg(exclusion_ranges, XYListStore())
        self.exclusion_ranges.connect("item-removed", self.on_exclusion_range_changed)
        self.exclusion_ranges.connect("item-inserted", self.on_exclusion_range_changed)
        self.exclusion_ranges.connect("row-changed", self.on_exclusion_range_changed)
        
        
        markers = markers or self.get_depr(kwargs, None, "data_markers")
        self._markers = self.parse_liststore_arg(markers, ObjectListStore, Marker)
        for marker in self._markers._model_data:
            self.observe_model(marker)
        self.markers.connect("item-removed", self.on_marker_removed)
        self.markers.connect("item-inserted", self.on_marker_inserted)
        
        self.display_vshift = float(display_vshift)
        self.display_vscale = float(display_vscale)
        self.display_calculated = bool(display_calculated)
        self.display_experimental = bool(display_experimental)
        self.display_phases = bool(display_phases)
        self.display_stats_in_lbl = bool(display_stats_in_lbl)
        
        self.statistics = Statistics(parent=self)
    
    def __str__(self):
        return "<Specimen %s(%s)>" % (self.name, repr(self))
    
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Observer.observe("needs_update", signal=True)
    def notify_needs_update(self, model, prop_name, info):
        self.needs_update.emit() #propagate signal
        
    def on_exclusion_range_changed(self, model, item, *args):
        self.needs_update.emit() #propagate signal
        
    def on_marker_removed(self, model, item):
        self.relieve_model(item)
        item.parent = None
        self.needs_update.emit() #propagate signal
        
    def on_marker_inserted(self, model, item):
        self.observe_model(item)
        item.parent = self
        self.needs_update.emit() #propagate signal
                  
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------   
    def json_properties(self):
        retval = Storable.json_properties(self)
        retval["calc_color"] = self._calc_color
        retval["exp_color"] = self._exp_color
        retval["calc_lw"] = self._calc_lw
        retval["exp_lw"] = self._exp_lw
        return retval
              
    @staticmethod
    def from_experimental_data(filename, parent, parser):
        specimens = list()
        xrdfiles = parser.parse(filename)
        for xrdfile in xrdfiles:
            name, sample, generator = xrdfile.filename, xrdfile.name, xrdfile.data
            specimen = Specimen(parent=parent, name=name, sample_name=sample)
            specimen.experimental_pattern.xy_store.load_data_from_generator(generator, clear=True)        
            specimens.append(specimen)
        
        return specimens
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def auto_add_peaks(self, tmodel):
        """
        Automagically add peak markers
        
        *tmodel* a :class:`~specimen.models.ThresholdSelector` model
        """
        threshold = tmodel.sel_threshold
        base = 1 if (tmodel.pattern == "exp") else 2
        data_x, data_y = tmodel.get_xy()
        maxtab, mintab = peakdetect(data_y, data_x, 5, threshold)
        
        mpositions = []
        for marker in self.markers._model_data:
            mpositions.append(marker.position)

        i = 1
        for x, y in maxtab:
            if not x in mpositions:
                nm = self.parent.goniometer.get_nm_from_2t(x) if x != 0 else 0
                new_marker = Marker("%%.%df" % (3 + min(int(log(nm, 10)), 0)) % nm, parent=self, position=x, base=base)
                self.markers.append(new_marker)
            i += 1
               
    def get_exclusion_selector(self, x):
        """
        Get the numpy selector array for non-excluded data
        
        *x* a numpy ndarray containing the 2-theta values
        
        :rtype: a numpy ndarray
        """
        if x != None:
            selector = np.ones(x.shape, dtype=bool)
            for x0,x1 in zip(*np.sort(np.array(self.exclusion_ranges.get_raw_model_data()), axis=0)):
                new_selector = ((x < x0) | (x > x1))
                selector = selector & new_selector
            return selector
        return None
        
    def get_exclusion_xy(self):
        """
        Get an numpy array containing only non-excluded data X and Y data
                
        :rtype: a tuple containing 4 numpy ndarray's: the experimental X and Y
        data and the calculated X and Y data
        """
        ex, ey = self.experimental_pattern.xy_store.get_raw_model_data()
        cx, cy = self.calculated_pattern.xy_store.get_raw_model_data()
        selector = self.get_exclusion_selector(ex)
        return ex[selector], ey[selector], cx[selector], cy[selector]

    # ------------------------------------------------------------
    #      Intensity calculations:
    # ------------------------------------------------------------
    @print_timing
    def update_pattern(self, phases, fractions, lpf_callback, steps=2500):
        """
        Recalculate pattern intensities using the provided phases
        and their relative fractions
        
        *phases* a list of phases with length N
        
        *fractions* a list with phase fractions, also length N
        
        *lpf_callback* a callback providing the Lorentz polarisation factor
        
        :rtype: a 3-tuple containing 2-theta values, phase intensities and the
        total intensity, or None if the length of *phases* is 0
        """
        if len(phases) == 0:
            self.calculated_pattern.clear()
            self.statistics.update_statistics()
            return None
        else:
            #Get 2-theta values and phase intensities
            theta_range, intensities = self.get_phase_intensities(phases, lpf_callback, steps=steps)
            theta_range = theta_range * 360.0 / pi
            
            #Apply fractions and absolute scale
            fractions = np.array(fractions)[:,np.newaxis]
            phase_intensities = fractions*intensities*self.abs_scale
                        
            #Sum the phase intensities and apply the background shift
            total_intensity = np.sum(phase_intensities, axis=0) + self.bg_shift
            phase_intensities += self.bg_shift

            #Update the pattern data:            
            self.calculated_pattern.set_data(
                theta_range,
                total_intensity,
                phase_intensities, 
                phases)
            
            #update stats:
            self.statistics.update_statistics()
            
            #Return what we just calculated for anyone interested
            return (theta_range, phase_intensities, total_intensity)
        
    #@print_timing
    def get_phase_intensities(self, phases, lpf_callback, steps=2500):
        """
        Gets phase intensities for the provided phases
        
        *phases* a list of phases with length N
        
        *lpf_callback* a callback providing the Lorentz polarisation factor
        
        *steps* the number of data points to calculate in the range specified 
        in the project's :class:`~goniometer.models.Goniometer` object. This is
        used only if no experimental data is loaded in the specimen
        
        :rtype: a 2-tuple containing 2-theta values and phase intensities or
        None if the length of *phases* is 0
        """
        if phases!=None: #TODO cache correction range!
        
            l = self.parent.goniometer.wavelength
            theta_range = None
            if self.experimental_pattern.xy_store._model_data_x.size <= 1:
                theta_range = self.parent.goniometer.get_default_theta_range()
            else:
                theta_range = np.radians(self.experimental_pattern.xy_store._model_data_x * 0.5)
            sin_range = np.sin(theta_range)
            stl_range = 2 * sin_range / l
            
            correction_range = self.parent.goniometer.get_machine_correction_range(
                theta_range, self.sample_length, self.absorption)            
            #absorption = float(self.absorption)
            #if absorption > 0.0:
            #    correction_range *= (1.0 - np.exp(-2.0*absorption / sin_range))
            
            intensities = np.array([
                   phase.get_diffracted_intensity(
                        theta_range,
                        stl_range,
                        lpf_callback,
                        1.0,
                        correction_range
                    ) if phase else
                    np.zeros(shape=theta_range.shape) for phase in phases],
                dtype=np.float_)
            
            return (theta_range, intensities)
    
    def __str__(self):
        return "<'%s' Specimen>" % self.name
    
    pass #end of class
