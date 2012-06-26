# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os
#import time
from math import tan, sin, pi, radians, log
from warnings import warn

import gtk
import gobject
from gtkmvc.model import Model, Signal, Observer

import matplotlib
import matplotlib.transforms as transforms
#from matplotlib.transforms import offset_copy
from matplotlib.text import Text

import numpy as np
from scipy import stats

import settings

from generic.metaclasses import pyxrd_object_pool
from generic.utils import interpolate, print_timing, u
from generic.io import Storable
from generic.model_mixins import CSVMixin, ObjectListStoreChildMixin, ObjectListStoreParentMixin
from generic.models import PyXRDLine, ExperimentalLine, CalculatedLine, ChildModel, PropIntel, MultiProperty
from generic.treemodels import ObjectListStore, XYListStore
from generic.peak_detection import multi_peakdetect, peakdetect

class Specimen(ChildModel, Storable, ObjectListStoreParentMixin, ObjectListStoreChildMixin):

    #MODEL INTEL:
    __parent_alias__ = 'project'
    __model_intel__ = [
        PropIntel(name="data_name",                 inh_name=None,  label="Name",                               minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_sample",               inh_name=None,  label="Sample",                             minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_label",                inh_name=None,  label="Label",                              minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=False, observable=True,  has_widget=False),        
        PropIntel(name="data_sample_length",        inh_name=None,  label="Sample length [cm]",                 minimum=0.0,   maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_abs_scale",            inh_name=None,  label="Absolute scale [counts]",            minimum=0.0,   maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_bg_shift",             inh_name=None,  label="Background shift [counts]",          minimum=0.0,   maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="display_calculated",        inh_name=None,  label="Display calculated diffractogram",   minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="display_experimental",      inh_name=None,  label="Display experimental diffractogram", minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="display_phases",            inh_name=None,  label="Display phases seperately",          minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="display_stats_in_lbl",      inh_name=None,  label="Display Rp in label",                minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_calculated_pattern",   inh_name=None,  label="Calculated diffractogram",           minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_experimental_pattern", inh_name=None,  label="Experimental diffractogram",         minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_exclusion_ranges",     inh_name=None,  label="Excluded ranges",                    minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_markers",              inh_name=None,  label="Markers",                            minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=True,  observable=True,  has_widget=False),
        PropIntel(name="statistics",                inh_name=None,  label="Statistics",                         minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="calc_color",                inh_name=None,  label="Calculated color",                   minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_calc_color",        inh_name=None,  label="Use default color",                  minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="exp_color",                 inh_name=None,  label="Experimental color",                 minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_exp_color",         inh_name=None,  label="Use default color",                  minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        
        PropIntel(name="needs_update",              inh_name=None,  label="",                                   minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
    ]

    __pctrl__ = None

    #SIGNALS:
    needs_update = None

    #PROPERTIES:
    _data_sample = ""
    _data_name = ""
    _display_calculated = True
    _display_experimental = True
    _display_phases = False
    _display_stats_in_lbl = True
    @Model.getter("data_sample", "data_name", "display_calculated",
        "display_experimental", "display_phases", "display_stats_in_lbl")
    def get_data_name(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @Model.setter("data_sample", "data_name", "display_calculated", 
        "display_experimental", "display_phases", "display_stats_in_lbl")
    def set_data_name(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        self.liststore_item_changed()
        self.needs_update.emit()
 
    def get_data_label_value(self):
        if self.display_stats_in_lbl:
            return self.data_sample + "\nRp = %.1f%%" % self.statistics.data_Rp
        else:
            return self.data_sample
 
    _data_calculated_pattern = None
    def get_data_calculated_pattern_value(self): return self._data_calculated_pattern
    def set_data_calculated_pattern_value(self, value):
        if self._data_calculated_pattern != None: self.relieve_model(self._data_calculated_pattern)
        self._data_calculated_pattern = value
        if self._data_calculated_pattern != None:
            self.observe_model(self._data_calculated_pattern)
            self.data_calculated_pattern.color = self.calc_color
    _data_experimental_pattern = None
    def get_data_experimental_pattern_value(self): return self._data_experimental_pattern
    def set_data_experimental_pattern_value(self, value):
        if self._data_experimental_pattern != None: self.relieve_model(self._data_experimental_pattern)
        self._data_experimental_pattern = value
        if self._data_experimental_pattern != None: 
            self.observe_model(self._data_experimental_pattern)
            self.data_experimental_pattern.color = self.exp_color
    
    _data_exclusion_ranges = None
    def get_data_exclusion_ranges_value(self): return self._data_exclusion_ranges
    def set_data_exclusion_ranges_value(self, value):
        if value != self._data_exclusion_ranges:
            if self._data_exclusion_ranges!=None:
                pass
            self._data_exclusion_ranges = value
            if self._data_exclusion_ranges!=None:
                pass
    
    _data_sample_length = 3.0
    _data_abs_scale = 1.0
    _data_bg_shift = 0.0
    @Model.getter("data_sample_length", "data_abs_scale", "data_bg_shift")
    def get_data_sample_length_value(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @Model.setter("data_sample_length", "data_abs_scale", "data_bg_shift")
    def set_data_sample_length_value(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        self.needs_update.emit()
    
    statistics = None
    
    _inherit_calc_color = True
    def get_inherit_calc_color_value(self): return self._inherit_calc_color
    def set_inherit_calc_color_value(self, value):
        if value != self._inherit_calc_color:
            self._inherit_calc_color = value
            if self.data_calculated_pattern != None:
                self.data_calculated_pattern.color = self.calc_color
    
    _calc_color = "#666666"
    def get_calc_color_value(self):
        if self.inherit_calc_color and self.parent!=None:
            return self.parent.display_calc_color
        else:
            return self._calc_color
    def set_calc_color_value(self, value):
        if value != self._calc_color:
            self._calc_color = value
            self.data_calculated_pattern.color = self.calc_color
            
    _inherit_exp_color = True
    def get_inherit_exp_color_value(self):
        return self._inherit_exp_color
    def set_inherit_exp_color_value(self, value):
        if value != self._inherit_exp_color:
            self._inherit_exp_color = value
            if self.data_experimental_pattern != None:
                self.data_experimental_pattern.color = self.exp_color
            
    _exp_color = "#000000"
    def get_exp_color_value(self):
        if self.inherit_exp_color and self.parent!=None:
            return self.parent.display_exp_color
        else:
            return self._exp_color
    def set_exp_color_value(self, value):
        if value != self._exp_color:
            self._exp_color = value
            self.data_experimental_pattern.color = value
    
    def set_display_offset(self, new_offset):
        self.data_experimental_pattern.offset = new_offset
        self.data_calculated_pattern.offset = new_offset
    
    #_data_phases = None
    #def get_data_phases_value(self): return self._data_phases
        
    _data_markers = None
    def get_data_markers_value(self): return self._data_markers
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name="", data_sample="", data_sample_length=3.0, data_abs_scale=1.0, data_bg_shift=0.0,
                 display_calculated=True, display_experimental=True, display_phases=False, display_stats_in_lbl=True,
                 data_experimental_pattern = None, data_calculated_pattern = None, data_exclusion_ranges = None, data_markers = None,
                 phase_indeces=None, phase_uuids=None, calc_color=None, exp_color=None, 
                 inherit_calc_color=True, inherit_exp_color=True, parent=None):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
               
        self.needs_update = Signal()
               
        self.data_name = data_name
        self.data_sample = data_sample
        self.data_sample_length = data_sample_length
        self.data_abs_scale  = data_abs_scale
        self.data_bg_shift = data_bg_shift

        self._calc_color = calc_color or self.calc_color
        self._exp_color = exp_color or self.exp_color
        
        self.inherit_calc_color = inherit_calc_color
        self.inherit_exp_color = inherit_exp_color
               
        self.data_phases = []

        if isinstance(data_calculated_pattern, dict) and "type" in data_calculated_pattern and data_calculated_pattern["type"]=="generic.models/XYData":
            self.data_calculated_pattern = CalculatedLine.from_json(parent=self, **data_calculated_pattern["properties"])
        else:
            self.data_calculated_pattern = self.parse_init_arg(
                data_calculated_pattern,
                CalculatedLine(label="Calculated Profile", color=self.calc_color, parent=self),
                child=True)

        if isinstance(data_experimental_pattern, dict) and "type" in data_experimental_pattern and data_experimental_pattern["type"]=="generic.models/XYData":
            self.data_experimental_pattern = ExperimentalLine.from_json(parent=self, **data_experimental_pattern["properties"])
        else:
            self.data_experimental_pattern = self.parse_init_arg(
                data_experimental_pattern, 
                ExperimentalLine(label="Experimental Profile", color=self.exp_color, parent=self), 
                child=True)
        
        self.data_exclusion_ranges = self.parse_init_arg(
            data_exclusion_ranges, XYListStore())
        self.data_exclusion_ranges.connect("item-removed", self.on_exclusion_range_changed)
        self.data_exclusion_ranges.connect("item-inserted", self.on_exclusion_range_changed)
        self.data_exclusion_ranges.connect("row-changed", self.on_exclusion_range_changed)
        
        
        self._data_markers = self.parse_liststore_arg(data_markers, ObjectListStore, Marker)
        for marker in self._data_markers._model_data:
            self.observe_model(marker)
        self.data_markers.connect("item-removed", self.on_marker_removed)
        self.data_markers.connect("item-inserted", self.on_marker_inserted)
        
        self.display_calculated = display_calculated
        self.display_experimental = display_experimental
        self.display_phases = display_phases
        self.display_stats_in_lbl = display_stats_in_lbl
        
        self.statistics = Statistics(parent=self)
    
    def __str__(self):
        return "<Specimen %s(%s)>" % (self.data_name, repr(self))
    
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
        return retval
              
    @staticmethod
    def from_experimental_data(parent, format="DAT", filename=""):
        specimen = Specimen(parent=parent)
        
        if format=="DAT":        
        
            with open(filename, 'r') as f:
                header = f.readline().replace("\n", "")
                specimen.data_experimental_pattern.load_data(data=f, format=format, has_header=False, clear=True)
            
            specimen.data_name = u(os.path.basename(filename))
            specimen.data_sample = u(header)
            
        elif format=="BIN":
            import struct
            
            f = open(filename, 'rb')
            f.seek(146)
            specimen.data_sample = u(str(f.read(16)).replace("\0", ""))
            specimen.data_name = u(os.path.basename(filename))
            specimen.data_experimental_pattern.load_data(data=f, format=format, clear=True)
            f.close()
        
        return specimen
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    #data_phase_xydatas = None
        
    def on_update_plot(self, figure, axes, pctrl):
        axes.add_line(self.data_experimental_pattern)
        axes.add_line(self.data_calculated_pattern)
        pctrl.update_lim()

    _hatches = None        
    def on_update_hatches(self, figure, axes, pctrl): #TODO move this to the controller/view level
        if self._hatches:
            for leftborder, hatch, rightborder in self._hatches:
                try:
                    hatch.remove()
                    leftborder.remove()
                    rightborder.remove()
                except: pass
        self._hatches = list()
                
        scale, offset = self.scale_factor_y(self.data_experimental_pattern.offset)
        ymin, ymax = axes.get_ybound()
        scaler = max(self.max_intensity * scale, 1.0)
        y0 = (offset - ymin) / (ymax - ymin)
        y1 = (offset + scaler - ymin) / (ymax - ymin)
        
        for i, (x0, x1) in enumerate(zip(*self.data_exclusion_ranges.get_raw_model_data())):
            leftborder = axes.axvline(x0, y0, y1, c="#333333")
            hatch = axes.axvspan(x0, x1, y0, y1, fill=True, hatch="/", facecolor='#999999', edgecolor="#333333", linewidth=0)
            rightborder = axes.axvline(x1, y0, y1, c="#333333")
            
            self._hatches.append((leftborder, hatch, rightborder))        
        
    @property
    def max_intensity(self):
        return max(np.max(self.data_experimental_pattern.max_intensity), np.max(self.data_calculated_pattern.max_intensity))

    def scale_factor_y(self, offset):
        yscale = self.parent.axes_yscale if self.parent!=None else 1
        if yscale == 0:
            return (1.0 / (self.parent.get_max_intensity() or 1.0), offset)
        elif yscale == 1:
            return (1.0 / (self.max_intensity or 1.0), offset)
        elif yscale == 2:
            return (1.0, offset * self.parent.get_max_intensity())
        else:
            raise ValueError, "%d" % yscale

    @print_timing
    def update_pattern(self, phases, fractions, lpf_callback, steps=2500):
        num_phases = len(phases)
        if num_phases == 0:
            self.data_calculated_pattern.clear()
            self.statistics.update_statistics()
            return None
        else:
            #Get 2-theta values and phase intensities
            theta_range, intensities = self.get_phase_intensities(phases, lpf_callback, steps=steps)
            theta_range = theta_range * 360.0 / pi
            
            #Apply fractions and absolute scale
            fractions = np.array(fractions)[:,np.newaxis]
            self.data_phase_intensities = fractions*intensities*self.data_abs_scale
            
            self.data_calculated_pattern.update_child_lines(zip(map(lambda p: p.display_color, phases), self.data_phase_intensities))
            
            #Sum the phase intensities and apply the background shift
            total_intensity = np.sum(self.data_phase_intensities, axis=0) + self.data_bg_shift

            #Update the pattern data:            
            self.data_calculated_pattern.set_data(theta_range, total_intensity)
            
            #update stats:
            self.statistics.update_statistics()
            
            #Return what we just calculated for anyone interested
            return (theta_range, self.data_phase_intensities, total_intensity)
        

    def get_phase_intensities(self, phases, lpf_callback, steps=2500):
        if phases!=None:
        
            l = self.parent.data_goniometer.data_lambda
            L_Rta =  self.data_sample_length / (self.parent.data_goniometer.data_radius * tan(radians(self.parent.data_goniometer.data_divergence)))
            theta_range = None
            torad = pi / 180.0
            if self.data_experimental_pattern.xy_store._model_data_x.size <= 1:
                delta_theta = float(max_theta - min_theta) / float(steps-1)
                min_theta = radians(self.parent.data_goniometer.data_min_2theta*0.5)
                max_theta = radians(self.parent.data_goniometer.data_max_2theta*0.5)
                theta_range = min_theta + delta_theta * np.array(range(0,steps-1), dtype=float)
            else:
                theta_range =  self.data_experimental_pattern.xy_store._model_data_x * torad * 0.5
            stl_range = 2 * np.sin(theta_range) / l
            
            correction_range = np.minimum(np.sin(theta_range) * L_Rta, 1)
            
            intensities = np.array([phase.get_diffracted_intensity(theta_range, stl_range, lpf_callback, 1.0, correction_range) if phase else np.zeros(shape=theta_range.shape) for phase in phases], dtype=np.float_)
            
            return (theta_range, intensities)

    data_phase_intensities = None #list with 2D numpy arrays

    """@print_timing
    def calculate_pattern(self, lpf_callback, steps=2500):
        if len(self._data_phases) == 0:
            self.data_calculated_pattern.xy_store.clear()
            return None
        else:   
            theta_range, intensities = self.get_phase_intensities(self._data_phases.keys(), lpf_callback, steps=steps)
            intensity_range = np.zeros(len(intensities[0]))
            
            fractions = np.array(self._data_phases.values())[:,np.newaxis]
            
            intensity_range = np.sum(intensities*fractions*self.data_abs_scale, axis=0) + self.data_bg_shift
            theta_range = theta_range * 360.0 / pi 
            
            self.data_calculated_pattern.set_data(theta_range, intensity_range)

            return (theta_range, intensity_range)"""
        
    def auto_add_peaks(self, tmodel):
    
        threshold = tmodel.sel_threshold
        data_base = 1 if (tmodel.pattern == "exp") else 2
        data_x, data_y = tmodel.get_xy()
        maxtab, mintab = peakdetect(data_y, data_x, 5, threshold)
        
        mpositions = []
        for marker in self.data_markers._model_data:
            mpositions.append(marker.data_position)

        i = 1
        for x, y in maxtab:
            if not x in mpositions:
                nm = 0
                if x != 0:
                    nm = self.parent.data_goniometer.data_lambda / (2.0*sin(radians(x/2.0)))
                new_marker = Marker("%%.%df" % (3 + min(int(log(nm, 10)), 0)) % nm, parent=self, data_position=x, data_base=data_base)
                self.data_markers.append(new_marker)
            i += 1
            
    def get_exclusion_selector(self, x):
        if x != None:
            selector = np.ones(x.shape, dtype=bool)
            for x0,x1 in zip(*np.sort(np.array(self.data_exclusion_ranges.get_raw_model_data()), axis=0)):
                new_selector = ((x < x0) | (x > x1))
                selector = selector & new_selector
            return selector
        return None
        
    def get_exclusion_xy(self):
        ex, ey = self.data_experimental_pattern.xy_store.get_raw_model_data()
        cx, cy = self.data_calculated_pattern.xy_store.get_raw_model_data()
        selector = self.get_exclusion_selector(ex)
        return ex[selector], ey[selector], cx[selector], cy[selector]
    
    pass #end of class
    
class ThresholdSelector(ChildModel):
    
    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="pattern",               inh_name=None,  label="",   minimum=None,  maximum=None,  is_column=False,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="max_threshold",         inh_name=None,  label="",   minimum=None,  maximum=None,  is_column=False,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="steps",                 inh_name=None,  label="",   minimum=None,  maximum=None,  is_column=False,  ctype=int,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="sel_threshold",         inh_name=None,  label="",   minimum=None,  maximum=None,  is_column=False,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="sel_num_peaks",         inh_name=None,  label="",   minimum=None,  maximum=None,  is_column=False,  ctype=int,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="threshold_plot_data",   inh_name=None,  label="",   minimum=None,  maximum=None,  is_column=False,  ctype=object, refinable=False, storable=True,  observable=True,  has_widget=False),
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
        
        self.update_threshold_plot_data()
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_xy(self):
        if self._pattern == "exp":
            data_y = self.parent.data_experimental_pattern.xy_store._model_data_y
            data_y = data_y / np.max(data_y)
            return self.parent.data_experimental_pattern.xy_store._model_data_x, data_y
        elif self._pattern == "calc":
            data_y = self.parent.data_calculated_pattern.xy_store._model_data_y
            data_y = data_y / np.max(data_y)
            return self.parent.data_calculated_pattern.xy_store._model_data_x, data_y
    
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
        PropIntel(name="data_label",            inh_name=None,              label="",   minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_visible",          inh_name=None,              label="",   minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_position",         inh_name=None,              label="",   minimum=None,  maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_x_offset",         inh_name=None,              label="",   minimum=None,  maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_y_offset",         inh_name=None,              label="",   minimum=None,  maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_color",            inh_name=None,              label="",   minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_base",             inh_name=None,              label="",   minimum=None,  maximum=None,  is_column=True,  ctype=int,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_angle",            inh_name="inherit_angle",   label="",   minimum=None,  maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inherit_angle",         inh_name=None,              label="",   minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_style",            inh_name=None,              label="",   minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="needs_update",          inh_name=None,              label="",   minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
    ]
    __csv_storables__ = [ (prop.name, prop.name) for prop in __model_intel__ ]

    #SIGNALS:
    needs_update = None

    #PROPERTIES:
    _data_label = ""
    def get_data_label_value(self): return self._data_label
    def set_data_label_value(self, value):
        self._data_label = value
        self.liststore_item_changed()
        self.needs_update.emit()
    
    _data_visible = True
    _data_position = 0.0
    _data_x_offset = 0.0
    _data_y_offset = 0.05
    _data_color = "#000000"
    @Model.getter("data_visible", "data_position", "data_x_offset", "data_y_offset", "data_color")
    def get_data_plot_value(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @Model.setter("data_visible", "data_position", "data_x_offset", "data_y_offset", "data_color")
    def set_data_plot_value(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        self.needs_update.emit()

    _inherit_angle = True
    def get_inherit_angle_value(self): return self._inherit_angle
    def set_inherit_angle_value(self, value):
        self._inherit_angle = value
        if self._text!=None:
            self._text.set_rotation(90-self.data_angle)
        self.needs_update.emit()
            
    _data_angle = 0.0
    def get_data_angle_value(self):
        if self.inherit_angle and self.parent!=None and self.parent.parent!=None:
            return self.parent.parent.display_marker_angle
        else:
            return self._data_angle
    def set_data_angle_value(self, value):
        self._data_angle = value
        if self._text!=None:
            self._text.set_rotation(90-self.data_angle)
        self.needs_update.emit()

    _data_base = 1
    _data_bases = { 0: "X-axis", 1: "Experimental profile" }
    if not settings.VIEW_MODE:
        _data_bases.update({ 2: "Calculated profile", 3: "Lowest of both", 4: "Highest of both" })

    #_data_style = "none"
    #_data_styles = { "none": "Display at base", "solid": "Solid", "dashed": "Dash", "dotted": "Dotted", "dashdot": "Dash-Dotted", "offset": "Display at Y-offset" }
        
    def cbb_callback(self, prop_name, value):
        self.needs_update.emit()  
    data_style = MultiProperty("none", lambda i: i, cbb_callback, { 
        "none": "Display at base", "solid": "Solid", 
        "dashed": "Dash", "dotted": "Dotted", 
        "dashdot": "Dash-Dotted", "offset": "Display at Y-offset" 
    })    
    _data_bases = { 0: "X-axis", 1: "Experimental profile" }
    if not settings.VIEW_MODE:
        _data_bases.update({ 2: "Calculated profile", 3: "Lowest of both", 4: "Highest of both" })
    data_base = MultiProperty(1, int, cbb_callback, _data_bases)
    
    _vline = None
    _text = None
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_label="", data_visible=True, data_position=0.0, data_x_offset=0.0, data_y_offset=0.05, 
                 data_color="#000000", data_base=1, data_angle=0.0, inherit_angle=True, data_style="none", parent=None):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
        self.needs_update = Signal()
        
        self.data_label = data_label
        self.data_visible = data_visible
        self.data_position = float(data_position)
        self.data_x_offset = float(data_x_offset)
        self.data_y_offset = float(data_y_offset)
        self.data_color = data_color
        self.data_base = int(data_base)
        self.inherit_angle = inherit_angle
        self.data_angle = float(data_angle)
        self.data_style = data_style   
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_ymin(self):
        return min(self.get_y(self.parent.data_experimental_pattern), 
                   self.get_y(self.parent.data_calculated_pattern))
    def get_ymax(self):
        return max(self.get_y(self.parent.data_experimental_pattern), 
                   self.get_y(self.parent.data_calculated_pattern))   
    def get_y(self, line):
        x_data, y_data = line.get_data()
        if len(x_data) > 0:
            return np.interp(self.data_position, x_data, y_data)
        else:
            return 0
    
    def update_text(self, figure, axes): #FIXME this should be part of a view, rather then a model...
        if self.data_style != "offset":
            kws = dict(text=self.data_label,
                       x=float(self.data_position)+float(self.data_x_offset), y=settings.PLOT_TOP,
                       clip_on=False,
                       transform=transforms.blended_transform_factory(axes.transData, figure.transFigure),
                       horizontalalignment="left", verticalalignment="center",
                       rotation=(90-self.data_angle), rotation_mode="anchor",
                       color=self.data_color,
                       weight="heavy")
           
            if self.data_style == "none":
                y = 0
                if int(self.data_base) == 1:
                    y = self.get_y(self.parent.data_experimental_pattern)
                elif self.data_base == 2:
                    y = self.get_y(self.parent.data_calculated_pattern)
                elif self.data_base == 3:
                    y = self.get_ymin()
                elif self.data_base == 4:
                    y = self.get_ymax()
                    
                ymin, ymax = axes.get_ybound()
                trans = axes.transData #transforms.blended_transform_factory(axes.transData, axes.transAxes)
                #y = (y - ymin) / (ymax - ymin) + self.data_y_offset
                y += (self.data_y_offset - ymin) / (ymax - ymin)
                
                kws.update(dict(
                    y=y,
                    transform=trans,
                ))
            
            if self._text == None:
                self._text = Text(**kws)
            else:
                for key in kws:
                    getattr(self._text, "set_%s"%key)(kws[key])
            if not self._text in axes.get_children():
                axes.add_artist(self._text)     
    
    def update_vline(self, figure, axes): #FIXME this should be part of a view, rather then a model...
        y = 0
        if int(self.data_base) == 1:
            y = self.get_y(self.parent.data_experimental_pattern)
        elif self.data_base == 2:
            y = self.get_y(self.parent.data_calculated_pattern)
        elif self.data_base == 3:   
            y = self.get_ymin()
        elif self.data_base == 4:
            y = self.get_ymax()
            
        xmin, xmax = axes.get_xbound()
        ymin, ymax = axes.get_ybound()

        # We need to strip away the units for comparison with
        # non-unitized bounds
        #scalex = (self.data_position<xmin) or (self.data_position>xmax)
        trans = transforms.blended_transform_factory(axes.transData, axes.transAxes)
        y = (y - ymin) / (ymax - ymin)
            
        data_style = self.data_style
        data = [y,1]
        if data_style == "offset":
            data_style = "solid"
            y = (self.parent.data_experimental_pattern.offset - ymin) / (ymax - ymin)
            offset = y + (self.data_y_offset - ymin) / (ymax - ymin)
            
            data = [y,offset]
            
        if self._vline == None:
            self._vline = matplotlib.lines.Line2D([self.data_position,self.data_position], data , transform=trans, color=self.data_color, ls=data_style)
            self._vline.y_isdata = False
        else:
            self._vline.set_xdata(np.array([self.data_position,self.data_position]))
            self._vline.set_ydata(np.array(data))
            self._vline.set_transform(trans)
            self._vline.set_color(self.data_color)
            self._vline.set_linestyle(data_style)
            
        if not self._vline in axes.get_lines():
            axes.add_line(self._vline)
            #axes.autoscale_view(scalex=scalex, scaley=False)
    
    def on_update_plot(self, figure, axes, pctrl): #FIXME this should be part of a view, rather then a model...
        if self.parent!=None:
            self.update_vline(figure, axes)
            self.update_text(figure, axes)
               
    def get_nm_position(self):
        if self.parent != None:
            return self.parent.parent.data_goniometer.get_nm_from_2t(self.data_position)
        else:
            return 0.0
        
    def set_nm_position(self, position):
        if self.parent != None:
            self.data_position = self.parent.parent.data_goniometer.get_2t_from_nm(position)
        #else:
        #    self.data_position = 0.0
        
    pass #end of class
        
class Statistics(ChildModel):

    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="data_points",           inh_name=None, label="", minimum=None,  maximum=None,  is_column=True,  ctype=int,    refinable=False, storable=False, observable=True,  has_widget=True),
        PropIntel(name="data_residual_pattern", inh_name=None, label="", minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="data_chi2",             inh_name=None, label="", minimum=None,  maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=False, observable=True,  has_widget=True),
        PropIntel(name="data_Rp",               inh_name=None, label="", minimum=None,  maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=False, observable=True,  has_widget=True),
        PropIntel(name="data_R2",               inh_name=None, label="", minimum=None,  maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=False, observable=True,  has_widget=True),
    ]
    
    #PROPERTIES:
    def set_parent_value(self, value):
        ChildModel.set_parent_value(self, value)
        self.update_statistics()
       
    def get_data_points_value(self):
        try:
            e_ex, e_ey, e_cx, e_cy = self.specimen.get_exclusion_xy()
            return e_ex.size
        except: pass
        return 0
    
    data_chi2 = None      
    data_R2 = None
    data_Rp = None
    data_residual_pattern = None
         
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    def _get_experimental(self):
        if self.specimen != None:
            x, y = self.specimen.data_experimental_pattern.xy_store.get_raw_model_data()
            return x.copy(), y.copy()
        else:
            return None, None
    def _get_calculated(self):
        if self.specimen != None:
            x, y = self.specimen.data_calculated_pattern.xy_store.get_raw_model_data()
            return x.copy(), y.copy()
        else:
            return None, None 
             
    def scale_factor_y(self, offset):
        return self.specimen.scale_factor_y(offset) if self.specimen else (1.0, offset)
      
    def update_statistics(self):
        self.data_chi2 = 0        
        self.data_Rp = 0
        self.data_R2 = 0
        if self.data_residual_pattern == None:
            self.data_residual_pattern = PyXRDLine(label="Residual Data", color="#000000", parent=self)
        
        self.data_residual_pattern.clear()
        
        exp_x, exp_y = self._get_experimental()
        cal_x, cal_y = self._get_calculated()

        if cal_y != None and exp_y != None and cal_y.size > 0 and exp_y.size > 0:
            try: 
                self.data_residual_pattern.set_data(exp_x, exp_y - cal_y)

                e_ex, e_ey, e_cx, e_cy = self.specimen.get_exclusion_xy()

                self.data_chi2 = stats.chisquare(e_ey, e_cy)[0]
                self.data_Rp, self.data_R2 = self._calc_RpR2(e_ey, e_cy)
            except ValueError, ZeroDivisionError:
                print "Error occured when trying to calculate statistics, aborting calculation!"
           
    @staticmethod
    def _calc_RpR2(o, e):
        if o.size > 0:
            avg = sum(o)/o.size
            sserr = np.sum((o - e)**2)
            sstot = np.sum((o - avg)**2)
            return Statistics._calc_Rp(o, e), 1 - (sserr / sstot)
        else:
            return 0, 0   
        
    @staticmethod
    def _calc_Rp(o, e):
        return np.sum(np.abs(o - e)) / np.sum(np.abs(o)) * 100
        
    pass #end of class
