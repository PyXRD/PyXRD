# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from gtkmvc.model import Signal

import numpy as np
from scipy import stats
from scipy.interpolate import interp1d

import settings
from generic.io import unicode_open, Storable
from generic.models import ChildModel, PropIntel, MultiProperty
from generic.models.mixins import CSVMixin, ObjectListStoreChildMixin
from generic.peak_detection import multi_peakdetect, score_minerals

class MineralScorer(ChildModel):
    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [
        PropIntel(name="matches",                 data_type=list,    has_widget=True),
        PropIntel(name="minerals",                data_type=list,    has_widget=True),
        PropIntel(name="matches_changed",         data_type=object,  has_widget=False, storable=False)
    ]
    
    matches_changed = None
    
    _matches = None
    def get_matches_value(self):
        return self._matches
    
    _minerals = None
    def get_minerals_value(self):
        #Load them when accessed for the first time:
        if self._minerals==None:
            self._minerals = list()
            with unicode_open(settings.get_def_file("MINERALS")) as f:
                mineral = ""
                abbreviation = ""
                position_flag = True
                peaks = []
                for line in f:
                    line = line.replace('\n', '')
                    try:
                        number = float(line)
                        if position_flag:
                            position = number
                        else:
                            intensity = number
                            peaks.append((position, intensity))
                        position_flag = not position_flag
                    except ValueError:
                        if mineral!="":
                            self._minerals.append((mineral, abbreviation, peaks))
                        position_flag = True
                        if len(line) > 25:
                            mineral = line[:24].strip()
                        if len(line) > 49:
                            abbreviation = line[49:].strip()
                        peaks = []
        sorted(self._minerals, key=lambda mineral:mineral[0])
        return self._minerals
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, marker_peaks=[], *args, **kwargs):
        super(MineralScorer, self).__init__(*args, **kwargs)
        self._matches = []
        self.matches_changed = Signal()
        
        self.marker_peaks = marker_peaks #position, intensity
            
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def auto_match(self):
        self._matches = score_minerals(self.marker_peaks, self.minerals)
        self.matches_changed.emit()
    
    def del_match(self, index):
        if self.matches:
            del self.matches[index]
            self.matches_changed.emit()
         
    def add_match(self, name, abbreviation, peaks):
        matches = score_minerals(self.marker_peaks, [(name, abbreviation, peaks)])
        if len(matches):
            name, abbreviation, peaks, matches, score = matches[0]
        else:
            matches, score = [], 0.
        self.matches.append([name, abbreviation, peaks, matches, score])
        sorted(self._matches, key=lambda match: match[-1], reverse=True)
        self.matches_changed.emit()
         
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
            self.sel_num_peaks = int(interp1d(*self.threshold_plot_data)(self._sel_threshold))
    
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

                def calculate_deltas_for(max_threshold, steps):            
                    resolution = length / (data_x[-1] - data_x[0])
                    delta_angle = 0.05
                    window = int(delta_angle * resolution)
                    window += (window % 2)*2
                    
                    steps = max(steps, 2) - 1
                    factor = max_threshold / steps

                    deltas = [i*factor for i in range(0, steps)]
                    
                    numpeaks = []
                    maxtabs, mintabs = multi_peakdetect(data_y, data_x, 5, deltas)
                    for maxtab, mintab in zip(maxtabs, mintabs):
                        numpeak = len(maxtab)
                        numpeaks.append(numpeak)
                    numpeaks = map(float, numpeaks)
                    
                    return deltas, numpeaks
                                    
                #update plot:
                deltas, numpeaks = calculate_deltas_for(self.max_threshold, self.steps)
                self.threshold_plot_data = deltas, numpeaks
                
                #update auto selected threshold:
                
                # METHOD 1:
                #  Fit several lines with increasing number of points from the
                #  generated threshold / marker count graph. Stop when the
                #  R-coefficiënt drops below 0.95 (past linear increase from noise)
                #  Then repeat this by increasing the resolution of data points
                #  and continue until the result does not change anymore
                
                last_solution = None
                solution = False
                max_iters = 10
                itercount = 0
                delta_x = None
                while not solution:               
                    ln = 4
                    max_ln = len(deltas)
                    stop = False
                    while not stop:
                        x = deltas[0:ln]
                        y = numpeaks[0:ln]
                        slope, intercept, R, p_value, std_err = stats.linregress(x,y)
                        ln += 1
                        if abs(R) < 0.98 or ln >= max_ln:
                            stop = True
                        delta_x = -intercept / slope
                    itercount += 1
                    if last_solution:
                        if itercount < max_iters and last_solution - delta_x >= 0.001:                    
                            deltas, numpeaks = calculate_deltas_for(delta_x[-1], self.steps)
                        else:
                            solution = True
                    last_solution = delta_x

                if delta_x:
                    self.sel_threshold = delta_x
    pass #end of class

class Marker(ChildModel, Storable, ObjectListStoreChildMixin, CSVMixin):
    
    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="label",         data_type=unicode, storable=True, has_widget=True, is_column=True),
        PropIntel(name="visible",       data_type=bool,    storable=True, has_widget=True),
        PropIntel(name="position",      data_type=float,   storable=True, has_widget=True),
        PropIntel(name="x_offset",      data_type=float,   storable=True, has_widget=True),
        PropIntel(name="y_offset",      data_type=float,   storable=True, has_widget=True),
        PropIntel(name="align",         data_type=str,     storable=True, has_widget=True),
        PropIntel(name="color",         data_type=float,   storable=True, has_widget=True),
        PropIntel(name="base",          data_type=float,   storable=True, has_widget=True),
        PropIntel(name="angle",         data_type=float,   storable=True, has_widget=True, inh_name="inherit_angle"),
        PropIntel(name="inherit_angle", data_type=bool,    storable=True, has_widget=True),
        PropIntel(name="style",         data_type=str,     storable=True, has_widget=True),
        PropIntel(name="needs_update",  data_type=object),
    ]
    __csv_storables__ = [ (prop.name, prop.name) for prop in __model_intel__ ]
    __store_id__ = "Marker"

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
    @ChildModel.getter("visible", "position", "x_offset", "y_offset", "color")
    def get_plot_value(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @ChildModel.setter("visible", "position", "x_offset", "y_offset", "color")
    def set_plot_value(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        self.needs_update.emit()

    _inherit_angle = True
    def get_inherit_angle_value(self): return self._inherit_angle
    def set_inherit_angle_value(self, value):
        self._inherit_angle = bool(value)
        self.needs_update.emit()
            
    _angle = 0.0
    def get_angle_value(self):
        if self.inherit_angle and self.parent!=None and self.parent.parent!=None:
            return self.parent.parent.display_marker_angle
        else:
            return self._angle
    def set_angle_value(self, value):
        self._angle = value
        self.needs_update.emit()
     
    def cbb_callback(self, prop_name, value):
        self.needs_update.emit() 
    
    align = MultiProperty(settings.MARKER_ALIGN, lambda i: i, cbb_callback, { 
        "left": "Left align", 
        "center": "Centered", 
        "right": "Right align"
    })  
    
    _bases = { 0: "X-axis", 1: "Experimental profile" }
    if not settings.VIEW_MODE:
        _bases.update({ 2: "Calculated profile", 3: "Lowest of both", 4: "Highest of both" })
    base = MultiProperty(settings.MARKER_BASE, int, cbb_callback, _bases)
    
    style = MultiProperty(settings.MARKER_STYLE, lambda i: i, cbb_callback, { 
        "none": "Display at base", "solid": "Solid", 
        "dashed": "Dash", "dotted": "Dotted", 
        "dashdot": "Dash-Dotted", "offset": "Display at Y-offset" 
    })
        
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, label=None, visible=None, position=None, 
             x_offset=None, y_offset=None, 
             color=None, base=None, angle=None,
             inherit_angle=True, align=None, style=None, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
        self.needs_update = Signal()
        
        self.label = label or self.get_depr(kwargs, "", "data_label")
        self.visible = visible or self.get_depr(kwargs, True, "data_visible")
        self.position = float(position or self.get_depr(kwargs, 0.0, "data_position"))
        self.x_offset = float(x_offset or self.get_depr(kwargs, 0.0, "data_x_offset"))
        self.y_offset = float(y_offset or self.get_depr(kwargs, 0.05, "data_y_offset"))
        self.color = color or self.get_depr(kwargs, settings.MARKER_COLOR, "data_color")
        self.base = int(base if base!=None else self.get_depr(kwargs, settings.MARKER_BASE, "data_base"))
        self.inherit_angle = inherit_angle
        self.angle = float(angle or self.get_depr(kwargs, 0.0, "data_angle"))
        self.align = align or settings.MARKER_ALIGN        
        self.style = style or self.get_depr(kwargs, settings.MARKER_STYLE, "data_style")
        
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
        
Marker.register_storable()
    
