# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import matplotlib
from matplotlib.lines import Line2D
import matplotlib.transforms as transforms

import numpy as np

from gtkmvc.model import Signal

from generic.io import Storable, PyXRDDecoder
from generic.utils import smooth

from properties import PropIntel, MultiProperty
from treemodels import XYListStore

from base import ChildModel

class PyXRDLine(ChildModel, Storable):

    #MODEL INTEL:
    __model_intel__ = [
        PropIntel(name="label",           data_type=unicode, storable=True),
        PropIntel(name="xy_store",        data_type=object,  storable=True),
        PropIntel(name="color",           data_type=str,     observable=False),
        PropIntel(name="lw",              data_type=float,   observable=False),
        PropIntel(name="needs_update",    data_type=object),
    ]
    __store_id__ = "PyXRDLine"

    #PROPERTIES:
    _xy_store = None
    def get_xy_store_value(self): return self._xy_store
    needs_update = None
    
    _label = ""
    def get_label_value(self): return self._label
    def set_label_value(self, value): self._label = value

    _color = "#000000"
    @property
    def color(self): return self._color
    @color.setter
    def color(self, value):
        self._color = value
        self.needs_update.emit()

    _lw = 2.0
    @property
    def lw(self): return self._lw
    @lw.setter
    def lw(self, value):
        self._lw = value
        self.needs_update.emit()

    @property
    def size(self):
        return len(self.xy_store._model_data_x)
    
    @property
    def max_intensity(self):
        if len(self.xy_store._model_data_x) > 1:
            return np.max(self.xy_store._model_data_y)
        else:
            return 0
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, xy_store=None, label=None, color=None, lw=None, *args, **kwargs):
        self.init_xy_store(xy_store=xy_store)
        self.xy_store.connect('row-deleted', self.on_treestore_changed)
        self.xy_store.connect('row-inserted', self.on_treestore_changed)
        self.xy_store.connect('row-changed', self.on_treestore_changed)
        super(PyXRDLine, self).__init__(*args, **kwargs)
        
        self.needs_update = Signal()
        
        self.color = color if color!=None else self.color
        self.label = label if label!=None else self.label
        self.lw = lw if lw != None else self.lw

    def init_xy_store(self, xy_store=None):
        self._xy_store = xy_store or XYListStore()
    
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------    
    @classmethod
    def from_json(type, **kwargs):
        if "xy_store" in kwargs:
            kwargs["xy_store"] = PyXRDDecoder().__pyxrd_decode__(kwargs["xy_store"])        
        elif "xy_data" in kwargs:
            kwargs["xy_store"] = PyXRDDecoder().__pyxrd_decode__(kwargs["xy_data"])
            kwargs["label"] = kwargs["data_label"]
            del kwargs["data_name"]
            del kwargs["data_label"]
            del kwargs["xy_data"]
        return type(**kwargs)
            
    def save_data(self, filename):
        self.xy_store.save_data("%s %s" % (self.parent.name, self.parent.sample_name), filename)
        
    def load_data(self, *args, **kwargs):   
        """
            Loads data using passed args & kwargs, which are passed on to the
            internal XYListStore's load_data method.
            If the file contains additional y-value columns, they are returned
            as a list of numpy 2D lists (X & Y columns).
        """ 
        return self.xy_store.load_data(*args, **kwargs)
            
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------                  
    def on_treestore_changed(self, treemodel, path, *args):
        self.needs_update.emit()
    
    def set_data(self, x, *y, **kwargs):
        self.xy_store.update_from_data(x, *y, **kwargs)
               
    def clear(self):
        self.xy_store.clear()

            
    pass #end of class

PyXRDLine.register_storable()

class CalculatedLine(PyXRDLine):

    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [ ]
    __store_id__ = "CalculatedLine"
    __gtype_name__ = "PyXRDCalculatedLine"
    
    #PROPERTIES:
    phases = None
        
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.phases = []
        super(CalculatedLine, self).__init__(*args, **kwargs)
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------  
    def set_data(self, x, y, phase_patterns=None, phases=None):
        self.phases = phases
        super(CalculatedLine, self).set_data(x, y, *phase_patterns, names=[phase.name if phase!=None else "NOT SET" for phase in phases])

    pass #end of class
    
CalculatedLine.register_storable()

class ExperimentalLine(PyXRDLine):

    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [
        PropIntel(name="bg_position",       data_type=float),
        PropIntel(name="bg_scale",          data_type=float),
        PropIntel(name="bg_pattern",        data_type=object),
        PropIntel(name="bg_type",           data_type=int),
        PropIntel(name="smooth_degree",     data_type=int),
        PropIntel(name="smooth_type",       data_type=int),
        PropIntel(name="shift_value",       data_type=float),
        PropIntel(name="shift_position",    data_type=float),
        PropIntel(name="cap_value",         data_type=float),
    ]
    __store_id__ = "ExperimentalLine"
    __gtype_name__ = "PyXRDExperimentalLine"
    
    #PROPERTIES:
    @property
    def child_lines(self):
        return [self.bg_line, self.smooth_line, self.shifted_line, self.reference_line]

    _cap_value = 0.0
    def get_cap_value_value(self): return self._cap_value
    def set_cap_value_value(self, value):
        try:
            self._cap_value = float(value)
            self.needs_update.emit()
        except ValueError:
            pass
    
    @property
    def max_intensity(self):
        max_value = super(ExperimentalLine, self).max_intensity
        if self.cap_value > 0:
            max_value = min(max_value, self.cap_value)
        return max_value

    _bg_position = 0
    bg_line = None
    def get_bg_position_value(self): return self._bg_position
    def set_bg_position_value(self, value):
        try:
            self._bg_position = float(value)
            self.needs_update.emit()
        except ValueError:
            pass

    _bg_scale = 1.0
    def get_bg_scale_value(self): return self._bg_scale
    def set_bg_scale_value(self, value):
        try:
            self._bg_scale = float(value)
            self.needs_update.emit()
        except ValueError:
            pass
            
    _bg_pattern = None
    def get_bg_pattern_value(self): return self._bg_pattern
    def set_bg_pattern_value(self, value):
        self._bg_pattern = value
        self.needs_update.emit()

    def get_bg_type_lbl(self):
        return self._bg_types[self._bg_type]    
    def on_bgtype(self, prop_name, value):
        self.find_bg_position()

    _smooth_degree = 0
    smooth_pattern = None
    smooth_line = None
    def get_smooth_degree_value(self): return self._smooth_degree
    def set_smooth_degree_value(self, value):
        self._smooth_degree = float(value)
        self.needs_update.emit()
        
    def on_sdtype(self, prop_name, value):
        self.needs_update.emit()
                
    _shift_value = 0.0
    shifted_line = None
    reference_line = None
    def get_shift_value_value(self): return self._shift_value
    def set_shift_value_value(self, value):
        try:
            self._shift_value = float(value)
            self.needs_update.emit()
        except ValueError:
            pass
  
    def on_shift(self, prop_name, value):
        self.find_shift_value()
    
    shift_position = MultiProperty(0.42574, float, on_shift, { 
        0.42574: "Quartz    0.42574   SiO2",
        0.3134:  "Silicon   0.3134    Si",
        0.2476:  "Zincite   0.2476    ZnO",
        0.2085:  "Corundum  0.2085    Al2O3"
    })
    smooth_type = MultiProperty(0, int, on_sdtype, { 0: "Moving Triangle" })
    bg_type = MultiProperty(0, int, on_bgtype, { 0: "Linear", 1: "Pattern" })
            
    # ------------------------------------------------------------
    #      Background Removal
    # ------------------------------------------------------------
    def remove_background(self):
        x_data, y_data = self.xy_store.get_raw_model_data()
        bg = None
        if self.bg_type == 0:
            bg = self.bg_position
        elif self.bg_type == 1 and self.bg_pattern != None and not (self.bg_position == 0 and self.bg_scale == 0):
            bg = self.bg_pattern * self.bg_scale + self.bg_position
        if bg!=None:
            y_data -= bg
            self.set_data(x_data, y_data)
        self.clear_bg_variables()
        
    def find_bg_position(self):
        self.bg_position = np.min(self.xy_store.get_raw_model_data()[1])
            
    def clear_bg_variables(self):
        self.bg_pattern = None
        self.bg_scale = 0.0
        self.bg_position = 0.0
        self.needs_update.emit()
                
    # ------------------------------------------------------------
    #       Data Smoothing
    # ------------------------------------------------------------
    def smooth_data(self):
        x_data, y_data = self.xy_store.get_raw_model_data()
        if self.smooth_degree > 0:
            degree = int(self.smooth_degree)
            smoothed = smooth(y_data, degree)
            self.set_ydata(smoothed)
        self.smooth_degree = 0.0
        self.needs_update.emit()
            
    # ------------------------------------------------------------
    #       Data Shifting
    # ------------------------------------------------------------
    def shift_data(self):
        x_data, y_data = self.xy_store.get_raw_model_data()
        if self.shift_value != 0.0:
            self.set_xdata(x_data - self.shift_value)
            if self.specimen:
                for marker in self.specimen.markers._model_data:
                    marker.position = marker.position-self.shift_value
        self.shift_value = 0.0
        self.needs_update.emit()
        
    def find_shift_value(self):
        position = self.parent.parent.goniometer.get_2t_from_nm(self.shift_position)
        if position > 0.1:
            x_data, y_data = self.xy_store.get_raw_model_data()
            max_x = position + 0.5
            min_x = position - 0.5
            condition = (x_data>=min_x) & (x_data<=max_x)
            section_x, section_y = np.extract(condition, x_data), np.extract(condition, y_data)
            actual_position = section_x[np.argmax(section_y)]
            self.shift_value = actual_position - position 
    pass #end of class
    
ExperimentalLine.register_storable()
