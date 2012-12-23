# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os
from traceback import format_exc
from math import tan, sin, pi, radians, log, sqrt
from warnings import warn

import gtk
import gobject
from gtkmvc.model import Model, Signal, Observer

import matplotlib
import matplotlib.transforms as transforms
from matplotlib.text import Text

import numpy as np
from scipy import stats

import settings
from generic.utils import interpolate, print_timing, u
from generic.io import Storable
from generic.models import PyXRDLine, ExperimentalLine, CalculatedLine, ChildModel, PropIntel, MultiProperty
from generic.models.mixins import CSVMixin, ObjectListStoreChildMixin, ObjectListStoreParentMixin
from generic.models.metaclasses import pyxrd_object_pool
from generic.models.treemodels import ObjectListStore, XYListStore
from generic.peak_detection import multi_peakdetect, peakdetect

class Specimen(ChildModel, Storable, ObjectListStoreParentMixin, ObjectListStoreChildMixin):
    #MODEL INTEL:
    __parent_alias__ = 'project'
    __model_intel__ = [
        PropIntel(name="name",                 label="Name",                               data_type=str,    is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="sample_name",          label="Sample",                             data_type=str,    is_column=True,  storable=True,   has_widget=True),
        PropIntel(name="label",                label="Label",                              data_type=str,    is_column=True),        
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

    __pctrl__ = None

    #SIGNALS:
    needs_update = None

    #PROPERTIES:
    _sample_name = ""
    _name = ""
    _display_calculated = True
    _display_experimental = True
    _display_vshift = 0.0
    _display_vscale = 1.0
    _display_phases = False
    _display_stats_in_lbl = True
    @Model.getter("sample_name", "name", "display_vshift", "display_vscale",
         "display_phases", "display_stats_in_lbl",
         "display_calculated", "display_experimental")
    def get_name(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @Model.setter("sample_name", "name", "display_vshift", "display_vscale",
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
    @Model.getter("sample_length", "abs_scale", "bg_shift", "absorption")
    def get_sample_length_value(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @Model.setter("sample_length", "abs_scale", "bg_shift", "absorption")
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
    
    def set_transform_factors(self, scale, offset):
        self.experimental_pattern.set_transform_factors(scale, offset)
        self.calculated_pattern.set_transform_factors(scale, offset)
       
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
    def __init__(self, name="", sample_name="", sample_length=0.0, abs_scale=1.0,
                 bg_shift=0.0, absorption = 0.9, display_calculated=True,
                 display_experimental=True, display_phases=False, display_stats_in_lbl=True,
                 display_vshift=0.0, display_vscale=1.0, 
                 experimental_pattern = None, calculated_pattern = None, exclusion_ranges = None, markers = None,
                 phase_indeces=None, phase_uuids=None, calc_color=None, exp_color=None,
                 calc_lw=None, exp_lw=None, inherit_calc_lw=True, inherit_exp_lw=True,
                 inherit_calc_color=True, inherit_exp_color=True, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
               
        self.needs_update = Signal()
               
        self.name = name or self.get_depr(kwargs, "", "data_name")
        self.sample_name = sample_name or self.get_depr(kwargs, "", "data_sample")
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

        calculated_pattern = calculated_pattern or self.get_depr(kwargs, None, "data_calculated_pattern")
        if isinstance(calculated_pattern, dict) and "type" in calculated_pattern and calculated_pattern["type"]=="generic.models/XYData":
            self.calculated_pattern = CalculatedLine.from_json(parent=self, **calculated_pattern["properties"])
        else:
            self.calculated_pattern = self.parse_init_arg(
                calculated_pattern,
                CalculatedLine(label="Calculated Profile", color=self.calc_color, lw=self.calc_lw, parent=self),
                child=True)

        experimental_pattern = experimental_pattern or self.get_depr(kwargs, None, "data_experimental_pattern")
        if isinstance(experimental_pattern, dict) and "type" in experimental_pattern and experimental_pattern["type"]=="generic.models/XYData":
            self.experimental_pattern = ExperimentalLine.from_json(parent=self, **experimental_pattern["properties"])
        else:
            self.experimental_pattern = self.parse_init_arg(
                experimental_pattern, 
                ExperimentalLine(label="Experimental Profile", color=self.exp_color, lw=self.exp_lw, parent=self), 
                child=True)
        
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
        if self.__pctrl__:
            self.__pctrl__.register(item, "on_update_plot", last=True)
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
    def from_experimental_data(parent, format="DAT", filename=""):
        specimens = list()
        specimens.append(Specimen(parent=parent))
        
        if format=="DAT":        
            ays = None
            with open(filename, 'r') as f:
                header = f.readline().replace("\n", "")
                ays = specimens[0].experimental_pattern.load_data(data=f, format=format, has_header=False, clear=True)            
            name = u(os.path.basename(filename))
            specimens[0].sample_name, sep, sample_names = map(unicode, header.partition("- columns: "))
            if ays:
                sample_names = map(unicode, sample_names.split(", ")[1:])
                for i, ay in enumerate(ays):
                    spec = Specimen(parent=parent)
                    spec.experimental_pattern.set_data(ay[:,0],ay[:,1])
                    spec.name = name
                    spec.sample_name = sample_names[i+1]
                    specimens.append(spec)
            specimens[0].name = name
            
        elif format=="BIN":
            import struct
            
            f = open(filename, 'rb')
            f.seek(146)
            specimens[0].sample_name = u(str(f.read(16)).replace("\0", ""))
            specimens[0].name = u(os.path.basename(filename))
            specimens[0].experimental_pattern.load_data(data=f, format=format, clear=True)
            f.close()
        
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
            
    def get_y_min_at_x(self, x):
        """ 
            Get the lowest value for both experimental and calculated data on
            position x (in °2-theta)
        """
        return min(self.experimental_pattern.get_y_at_x(x), 
                   self.calculated_pattern.get_y_at_x(x))
    def get_y_max_at_x(self, x):
        """ 
            Get the highest value for both experimental and calculated data on
            position x (in °2-theta)
        """
        return max(self.experimental_pattern.get_y_at_x(x), 
                   self.calculated_pattern.get_y_at_x(x))
            
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
                *zip(*[ (phase.display_color, phase.name) for phase in phases if phase!=None]))
            
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
    
class ThresholdSelector(ChildModel):
    
    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="pattern",                 data_type=str,    storable=True,    has_widget=True),
        PropIntel(name="max_threshold",           data_type=float,  storable=True,    has_widget=True),
        PropIntel(name="steps",                   data_type=int,    storable=True,    has_widget=True),
        PropIntel(name="sel_threshold",           data_type=float,  storable=True,    has_widget=True),
        PropIntel(name="sel_num_peaks",           data_type=int,    storable=True,    has_widget=True),
        PropIntel(name="threshold_plot_data",     data_type=object, storable=True),
    ]
    
    #PROPERTIES:
    
    pattern = MultiProperty(
        "exp", 
        lambda i: i, 
        lambda self,p,v: self.update_threshold_plot_data(), 
        { "exp": "Experimental Pattern", "calc": "Calculated Pattern" }
    )    
    
    _max_threshold = 0.32
    def get_max_threshold_value(self): return self._max_threshold
    def set_max_threshold_value(self, value):
        value = min(max(0, float(value)), 1) #set some bounds
        if value != self._max_threshold:
            self._max_threshold = value
            self.update_threshold_plot_data()
            
    _steps = 20
    def get_steps_value(self): return self._steps
    def set_steps_value(self, value):
        value = min(max(3, value), 50) #set some bounds
        if value != self._steps:
            self._steps = value
            self.update_threshold_plot_data()
            
    _sel_threshold = 0.1
    sel_num_peaks = 0
    def get_sel_threshold_value(self): return self._sel_threshold
    def set_sel_threshold_value(self, value):
        if value != self._sel_threshold:
            self._sel_threshold = value
            deltas, numpeaks = self.threshold_plot_data
            self.sel_num_peaks = int(interpolate(zip(deltas, numpeaks), self._sel_threshold))
    
    threshold_plot_data = None
   
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------ 
    def __init__(self, max_threshold=None, steps=None, sel_threshold=None, parent=None):
        ChildModel.__init__(self, parent=parent)
        
        self.max_threshold = max_threshold or self.max_threshold
        self.steps = steps or self.steps
        self.sel_threshold = sel_threshold or self.sel_threshold
        
        if self.parent.experimental_pattern.size > 0:
            self.pattern == "exp"
        else:
            self.pattern == "calc"
        
        #self.update_threshold_plot_data()
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_xy(self):
        if self._pattern == "exp":
            data_x, data_y = self.parent.experimental_pattern.xy_store.get_raw_model_data()
        elif self._pattern == "calc":
            data_x, data_y = self.parent.calculated_pattern.xy_store.get_raw_model_data()
        if data_y.size > 0:
            data_y = data_y / np.max(data_y)
        return data_x, data_y
    
    def update_threshold_plot_data(self):
        if self.parent != None:
            data_x, data_y = self.get_xy()
            length = data_x.size
            
            if length > 2:
                resolution = length / (data_x[-1] - data_x[0])
                delta_angle = 0.05
                window = int(delta_angle * resolution)
                window += (window % 2)*2
                
                steps = max(self.steps, 2) - 1
                factor = self.max_threshold / steps

                deltas = [i*factor for i in range(0, self.steps)]
                
                numpeaks = []
                maxtabs, mintabs = multi_peakdetect(data_y, data_x, 5, deltas)
                for maxtab, mintab in zip(maxtabs, mintabs):
                    numpeak = len(maxtab)
                    numpeaks.append(numpeak)
                numpeaks = map(float, numpeaks)
                
                #update plot:
                self.threshold_plot_data = (deltas, numpeaks)
                
                #update auto selected threshold:
                ln = 4
                max_ln = len(deltas)
                stop = False
                while not stop:
                    x = deltas[0:ln]
                    y = numpeaks[0:ln]
                    slope, intercept, R, p_value, std_err = stats.linregress(x,y)
                    ln += 1
                    if abs(R) < 0.95 or ln >= max_ln:
                        stop = True
                    peak_x = -intercept / slope                

                self.sel_threshold = peak_x
    pass #end of class
            
class Marker(ChildModel, Storable, ObjectListStoreChildMixin, CSVMixin):
    
    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="label",         data_type=str,   storable=True, has_widget=True, is_column=True),
        PropIntel(name="visible",       data_type=bool,  storable=True, has_widget=True),
        PropIntel(name="position",      data_type=float, storable=True, has_widget=True),
        PropIntel(name="x_offset",      data_type=float, storable=True, has_widget=True),
        PropIntel(name="y_offset",      data_type=float, storable=True, has_widget=True),
        PropIntel(name="color",         data_type=float, storable=True, has_widget=True),
        PropIntel(name="base",          data_type=float, storable=True, has_widget=True),
        PropIntel(name="angle",         data_type=float, storable=True, has_widget=True, inh_name="inherit_angle"),
        PropIntel(name="inherit_angle", data_type=bool,  storable=True, has_widget=True),
        PropIntel(name="style",         data_type=str,   storable=True, has_widget=True),
        PropIntel(name="needs_update",  data_type=object),
    ]
    __csv_storables__ = [ (prop.name, prop.name) for prop in __model_intel__ ]

    #SIGNALS:
    needs_update = None

    #PROPERTIES:
    _label = ""
    def get_label_value(self): return self._label
    def set_label_value(self, value):
        self._label = value
        self.liststore_item_changed()
        self.needs_update.emit()
    
    _visible = True
    _position = 0.0
    _x_offset = 0.0
    _y_offset = 0.05
    _color = settings.MARKER_COLOR
    @Model.getter("visible", "position", "x_offset", "y_offset", "color")
    def get_plot_value(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @Model.setter("visible", "position", "x_offset", "y_offset", "color")
    def set_plot_value(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        self.needs_update.emit()

    _inherit_angle = True
    def get_inherit_angle_value(self): return self._inherit_angle
    def set_inherit_angle_value(self, value):
        self._inherit_angle = bool(value)
        if self._text!=None:
            self._text.set_rotation(90-self.angle)
        self.needs_update.emit()
            
    _angle = 0.0
    def get_angle_value(self):
        if self.inherit_angle and self.parent!=None and self.parent.parent!=None:
            return self.parent.parent.display_marker_angle
        else:
            return self._angle
    def set_angle_value(self, value):
        self._angle = value
        if self._text!=None:
            self._text.set_rotation(90-self.angle)
        self.needs_update.emit()
     
    def cbb_callback(self, prop_name, value):
        self.needs_update.emit()  
    style = MultiProperty(settings.MARKER_STYLE, lambda i: i, cbb_callback, { 
        "none": "Display at base", "solid": "Solid", 
        "dashed": "Dash", "dotted": "Dotted", 
        "dashdot": "Dash-Dotted", "offset": "Display at Y-offset" 
    })    
    
    _bases = { 0: "X-axis", 1: "Experimental profile" }
    if not settings.VIEW_MODE:
        _bases.update({ 2: "Calculated profile", 3: "Lowest of both", 4: "Highest of both" })
    base = MultiProperty(settings.MARKER_BASE, int, cbb_callback, _bases)
    
    _vline = None
    _text = None
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, label=None, visible=None, position=None, 
             x_offset=None, y_offset=None, 
             color=None, base=None, angle=None,
             inherit_angle=True, style=None, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
        self.needs_update = Signal()
        
        self.label = label or self.get_depr(kwargs, "", "data_label")
        self.visible = visible or self.get_depr(kwargs, True, "data_visible")
        self.position = float(position or self.get_depr(kwargs, 0.0, "data_position"))
        self.x_offset = float(x_offset or self.get_depr(kwargs, 0.0, "data_x_offset"))
        self.y_offset = float(y_offset or self.get_depr(kwargs, 0.05, "data_y_offset"))
        self.color = color or self.get_depr(kwargs, settings.MARKER_COLOR, "data_color")
        self.base = int(base if base!=None else self.get_depr(kwargs, 1, "data_base"))
        self.inherit_angle = inherit_angle
        self.angle = float(angle or self.get_depr(kwargs, 0.0, "data_angle"))
        self.style = style or self.get_depr(kwargs, "none", "data_style")
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_nm_position(self):
        if self.parent != None:
            return self.parent.parent.goniometer.get_nm_from_2t(self.position)
        else:
            return 0.0
        
    def set_nm_position(self, position):
        if self.parent != None:
            self.position = self.parent.parent.goniometer.get_2t_from_nm(position)
        else:
            self.position = 0.0
        
    pass #end of class
        
class Statistics(ChildModel):

    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="points",            data_type=int,   has_widget=True),
        PropIntel(name="residual_pattern",  data_type=object),
        PropIntel(name="Rp",                data_type=float, has_widget=True),
        PropIntel(name="Rwp",               data_type=float, has_widget=True),
        PropIntel(name="Re",                data_type=float, has_widget=True),
        PropIntel(name="chi2",              data_type=float, has_widget=True),
        PropIntel(name="R2",                data_type=float, has_widget=True),
    ]
    
    #PROPERTIES:
    def set_parent_value(self, value):
        ChildModel.set_parent_value(self, value)
        self.update_statistics()
       
    def get_points_value(self):
        try:
            e_ex, e_ey, e_cx, e_cy = self.specimen.get_exclusion_xy()
            return e_ex.size
        except: pass
        return 0

    Rp = None
    Rwp = None
    Re = None
    chi2 = None      
    R2 = None
    residual_pattern = None
         
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    def _get_experimental(self):
        if self.specimen != None:
            x, y = self.specimen.experimental_pattern.xy_store.get_raw_model_data()
            return x.copy(), y.copy()
        else:
            return None, None
    def _get_calculated(self):
        if self.specimen != None:
            x, y = self.specimen.calculated_pattern.xy_store.get_raw_model_data()
            return x.copy(), y.copy()
        else:
            return None, None 
             
    def scale_factor_y(self, offset):
        return self.specimen.scale_factor_y(offset) if self.specimen else (1.0, offset)
      
    def update_statistics(self, num_params=0):
        self.Rp = 0
        self.Rwp = 0
        self.Re = 0
        self.chi2 = 0        
        self.R2 = 0
        if self.residual_pattern == None:
            self.residual_pattern = PyXRDLine(label="Residual Data", color="#000000", parent=self)
        
        exp_x, exp_y = self._get_experimental()
        cal_x, cal_y = self._get_calculated()

        try:
            if cal_y != None and exp_y != None and cal_y.size > 0 and exp_y.size > 0:
                self.residual_pattern.set_data(exp_x, exp_y - cal_y)

                e_ex, e_ey, e_cx, e_cy = self.specimen.get_exclusion_xy()

                #self.chi2 = stats.chisquare(e_ey, e_cy)[0]
                #if exp.size > 0:
                self.R2 = self._calc_R2(e_ey, e_cy)
                self.Rp  = self._calc_Rp(e_ey, e_cy)
                self.Rwp = self._calc_Rwp(e_ey, e_cy)
                self.Re = self._calc_Re(e_ey, e_cy, num_params)                
                self.chi2 = (self.Rwp / self.Re) ** 2
            else:
                self.residual_pattern.clear()                    
        except ValueError, ZeroDivisionError:
            self.residual_pattern.clear()
            print "Error occured when trying to calculate statistics, aborting calculation!"
            print format_exc()
           
       
    @staticmethod
    def _calc_R2(exp, calc):
        avg = sum(exp)/exp.size
        sserr = np.sum((exp - calc)**2)
        sstot = np.sum((exp - avg)**2)
        return 1 - (sserr / sstot)
        
    @staticmethod
    def _calc_Rp(exp, calc):
        return np.sum(np.abs(exp - calc)) / np.sum(np.abs(exp)) * 100

    @staticmethod
    def _calc_Rwp(exp, calc):
        #weighted Rp:   
        # Rwp = Sqrt ( Sum[w * (obs - calc)²] / Sum[w * obs²] )  w = 1 / Iobs
        sm1 = 0
        sm2 = 0
        for i in range(exp.size):
            t = (exp[i] - calc[i])**2 / exp[i]
            if not (np.isnan(t) or np.isinf(t)):
                sm1 += t        
                sm2 += abs(exp[i])
        return sqrt(sm1 / sm2) * 100

    @staticmethod
    def _calc_Re(exp, calc, num_params):
        # R expected:
        # Re = Sqrt( (Points - Params) / Sum[ w * obs² ] )    
        num_points = exp.size
        return np.sqrt( (num_points - num_params) / np.sum(exp**2) ) * 100
    
    pass #end of class
