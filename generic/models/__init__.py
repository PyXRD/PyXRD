# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from itertools import izip, count
from collections import namedtuple
from warnings import warn

import matplotlib
from matplotlib.lines import Line2D
import matplotlib.transforms as transforms

import numpy as np
import scipy

from gtkmvc.model import Signal
from gtkmvc.model import Model
from gtkmvc.model_mt import ModelMT

from generic.io import Storable, PyXRDDecoder
from generic.utils import smooth, delayed

from metaclasses import PyXRDMeta, get_new_uuid, pyxrd_object_pool
from properties import PropIntel, MultiProperty
from treemodels import XYListStore

class DefaultSignal (Signal):

    def __init__(self, before=None, after=None):
        Signal.__init__(self)
        self.before = before
        self.after = after
        return

    def emit(self):
        def after():
            Signal.emit(self)
            if callable(self.after): self.after()
        if callable(self.before): self.before(after)
        else: after()
            
    pass # end of class

class PyXRDModel(ModelMT):
    __metaclass__ = PyXRDMeta
    __model_intel__ = [
        PropIntel(name="uuid", data_type=str,  storable=True, observable=False),
    ]
    
    
    def get_depr(self, fun_kwargs, default, *keywords):
        """
        Can be used to check if any deprecated keywords are passed to a 
        function, and if not, return a default value. Additionally warns the 
        user about the fact that he is using a deprecated keyword.
        If more then one deprecated keyword argument is present, the value of
        the last keword as passed to this function is passed.
        By default, deprecated arguments should be ignored if a non-deprecated
        one is passed as well.
        
        *fun_kwargs* the keyword arguments as passed to the function
        
        *default* the default value if no deprecated arguments are present
        
        **keywords* the deprecated keywords
        
        :rtype: the retrieved value or the default one as explained above
        """
        if len(keywords) < 1:
            raise AttributeError, "get_depr() requires at least one alias (%d given)" % (len(keywords))
        
        value = default
        for key in keywords:
            if key in fun_kwargs:
                value = fun_kwargs[key]
                warn("The use of the keyword '%s' is deprecated for %s!" % (key, type(self)), DeprecationWarning)
        return value
    
    @property
    def uuid(self): return self.__uuid__
    
    def __init__(self, *args, **kwargs):
        ModelMT.__init__(self, *args, **kwargs)
        self.__stored_uuids__ = list()
    
    def stack_uuid(self):
        self.__stored_uuids__.append(self.__uuid__)
        pyxrd_object_pool.remove_object(self)
        self.__uuid__ = get_new_uuid()
        pyxrd_object_pool.add_object(self)
        
    def restore_uuid(self):
        pyxrd_object_pool.remove_object(self)
        try:
            self.__uuid__ = self.__stored_uuids__.pop()
        except IndexError: #nothing to pop: create a new one!
            self.__uuid__ = get_new_uuid()
        pyxrd_object_pool.add_object(self)
        
    def get_prop_intel_by_name(self, name):
        for prop in self.__model_intel__:
            if prop.name == name:
                return prop
                
    def get_base_value(self, attr):
        intel = self.get_prop_intel_by_name(attr)
        if intel.inh_name!=None:
            return getattr(self, "_%s" % attr)
        else:
            return getattr(self, attr)
                
    pass # end of class

class RefinementInfo(PyXRDModel, Storable):

    #MODEL INTEL:
    __model_intel__ = [
        PropIntel(name="minimum",         data_type=float,  storable=True),
        PropIntel(name="maximum",         data_type=float,  storable=True),
        PropIntel(name="refine",          data_type=bool,   storable=True),
    ] 

    minimum = None
    maximum = None
    refine = False
    
    def __init__(self, minimum=None, maximum=None, refine=False, **kwargs):
        PyXRDModel.__init__(self)
        Storable.__init__(self)
        self.refine = bool(refine)
        self.minimum = float(minimum) if minimum!=None else None
        self.maximum = float(maximum) if maximum!=None else None
        
    def to_json(self):
        return self.json_properties()
        
    def json_properties(self):
        return [self.minimum, self.maximum, self.refine]
        
    pass #end of class

class ChildModel(PyXRDModel):

    #MODEL INTEL:
    __parent_alias__ = None
    __model_intel__ = [
        PropIntel(name="parent",  data_type=object),
        PropIntel(name="removed", data_type=object),
        PropIntel(name="added",   data_type=object),
    ]

    #SIGNALS:
    removed = None
    added = None

    #PROPERTIES:
    _parent = None
    def get_parent_value(self): return self._parent
    def set_parent_value(self, value):
        if value!=self._parent:
            self._unattach_parent()
            self._parent = value
            self._attach_parent()

    def __init__(self, parent=None):
        PyXRDModel.__init__(self)
        self.removed = Signal()
        self.added = Signal()

        if self.__parent_alias__ != None:
            setattr(self.__class__, self.__parent_alias__, property(lambda self: self.parent))         
        self.parent = parent

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------       
    def _unattach_parent(self):
        if self.parent != None:
            self.removed.emit()
    
    def _attach_parent(self):
        if self.parent != None:
            self.added.emit()
            
    pass #end of class

class PyXRDLine(ChildModel, Storable, Line2D):

    #MODEL INTEL:
    __model_intel__ = [
        PropIntel(name="label",           data_type=str,     storable=True),
        PropIntel(name="xy_store",        data_type=object,  storable=True),
        PropIntel(name="offset",          data_type=float),
        PropIntel(name="scale",           data_type=float),
        PropIntel(name="color",           data_type=str,     observable=False),
        PropIntel(name="lw",              data_type=float,   observable=False),
        PropIntel(name="needs_update",    data_type=object),
    ]

    #PROPERTIES:
    xy_empty_data = ([],[])
    _xy_store = None
    def get_xy_store_value(self): return self._xy_store
    needs_update = None

    _offset = 0
    def get_offset_value(self): return self._offset
    def set_offset_value(self, value):
        self._offset = float(value)
        self.update_line()
        
    _scale = 1.0
    def get_scale_value(self): return self._scale
    def set_scale_value(self, value):
        self._scale = float(scale)
        self.update_line()
        
    def get_label_value(self): return self.get_label()
    def set_label_value(self, value): self.set_label(value)

    @property
    def color(self):
        return matplotlib.colors.rgb2hex(
            matplotlib.colors.colorConverter.to_rgb(self.get_color()))
    @color.setter
    def color(self, value):
        self.set_color(value)
        self.needs_update.emit()

    @property
    def lw(self):
        return self.get_lw()
    @lw.setter
    def lw(self, value):
        self.set_lw(value)
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
    def __init__(self, xy_store=None, parent=None, color=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
        self.needs_update = Signal()
        self.init_xy_store(xy_store=xy_store)
        self.xy_store.connect('row-deleted', self.on_treestore_changed)
        self.xy_store.connect('row-inserted', self.on_treestore_changed)
        self.xy_store.connect('row-changed', self.on_treestore_changed)

        Line2D.__init__(self, *self.xy_store.get_raw_model_data(), color=color, **kwargs)
                
        self._inhibit_updates = False
        self.update_line()

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
        self._inhibit_updates = True
        ays = self.xy_store.load_data(*args, **kwargs)
        self._inhibit_updates = False
        self.update_line()
        return ays
            
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------           
    def set_transform_factors(self, scale, offset):
        self._scale = scale
        self._offset = offset
        self.update_line()

    def _transform_y(self, y):
        return np.array(y) * self.scale + self.offset
        
    def get_y_at_x(self, x):
        x_data, y_data = self.get_data()
        if len(x_data) > 0:
            return np.interp(x, x_data, y_data)
        else:
            return 0
        
    def on_treestore_changed(self, treemodel, path, *args):
        self.update_line()
        self.needs_update.emit()
    
    def set_data(self, x, y):
        self._inhibit_updates = True
        Line2D.set_data(self, x, y)
        self.xy_store.update_from_data(x, y)
        self._inhibit_updates = False
        
    def set_xdata(self, x):
        Line2D.set_xdata(self, x)
        if not self._inhibit_updates:
            xdata, ydata = self.xy_store.get_raw_model_data()
            self.xy_store.update_from_data(x, ydata)
        
    def set_ydata(self, y):
        Line2D.set_ydata(self, self._transform_y(y))
        if not self._inhibit_updates:
            xdata, ydata = self.xy_store.get_raw_model_data()
            self.xy_store.update_from_data(xdata, y)
            
    def clear(self):
        if len(self.xy_store._model_data_x) > 1:
            self._inhibit_updates = True
            self.xy_store.clear()
            self._inhibit_updates = False            
            self.update_line()
    
    def update_line(self):
        if not self._inhibit_updates:
            if len(self.xy_store._model_data_x) > 1:
                self.set_data(*self.xy_store.get_raw_model_data())
                self.set_visible(True)
            else:
                self.set_data(*self.xy_empty_data)
                self.set_visible(False)
    
    def draw(self, renderer):
        self.update_line()
        Line2D.draw(self, renderer)
            
    pass #end of class

class ScaledLine(Line2D):
       
    def draw(self, renderer, scale, offset):
        temp_y = np.array(self._yorig)
        self._yorig = temp_y * scale + offset
        try: self.recache(always=True)
        except:return #exit gracefully if this fails
        self._yorig = temp_y
        Line2D.draw(self, renderer)
        

class CalculatedLine(PyXRDLine):

    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [
        PropIntel(name="child_lines",  data_type=float),
    ]
    
    #PROPERTIES:
    _child_lines = None
    def get_child_lines_value(self):
        if self._child_lines==None:
            self._child_lines = []
        return self._child_lines
        
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        PyXRDLine.__init__(self, *args, **kwargs)
        self.set_linewidth(3)
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------  
    def set_figure(self, figure):
        PyXRDLine.set_figure(self, figure)
        for child in self.child_lines:
            if child: child.set_figure(figure)

    def set_axes(self, axes):
        PyXRDLine.set_axes(self, axes)
        for child in self.child_lines:
            if child: child.set_axes(axes)
    
    def draw(self, renderer):
        if self.parent.display_calculated:
            PyXRDLine.draw(self, renderer)
        if self.parent.display_phases:
            for line in self.child_lines:
                if line:
                    line.draw(renderer, self.scale, self.offset)
    
    def set_transform(self, transform):
        PyXRDLine.set_transform(self, transform)
        tf = self.get_transform()
        for line in self.child_lines:
            if line: line.set_transform(tf)

    def set_data(self, x, y, phases_y=None, phases_colors=None, phases_names=None):
        self._inhibit_updates = True
        #total line:
        if phases_y!=None and phases_colors:
            self.xy_store.update_from_data(x, y, *phases_y, names=phases_names)
            #phase lines:
            self._update_child_lines(phases_colors, phases_y)
        else:
            self.xy_store.update_from_data(x, y)
        Line2D.set_data(self, x, y)
        self._inhibit_updates = False

    def _update_child_lines(self, colors, ydata):
        clen = len(colors)
        mlen = len(self.child_lines)
        diff = mlen-clen
        if diff>0: #too many child line instances
            self._child_lines = self._child_lines[:-diff]
        elif diff<0: #too few child line instances
            self._child_lines.extend([None]*-diff)
        axes = self.get_axes()
        figure = self.get_figure()
        tf = self.get_transform()
        for i, color, y in izip(count(), colors, ydata):
            line = self._child_lines[i]
            if not line:
                line = ScaledLine([],[])
                self._child_lines[i] = line
            line.set_linewidth(self.get_linewidth())
            line.set_data(self.get_xdata(), y)
            line.set_color(color)
            line.set_transform(tf)
            if axes: line.set_axes(axes)
            if figure: line.set_figure(figure)
        

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
    ]
    
    #PROPERTIES:
    _bg_position = 0
    bg_line = None
    def get_bg_position_value(self): return self._bg_position
    def set_bg_position_value(self, value):
        try:
            self._bg_position = float(value)
            self.update_bg_line()
        except ValueError:
            pass

    _bg_scale = 1.0
    def get_bg_scale_value(self): return self._bg_scale
    def set_bg_scale_value(self, value):
        try:
            self._bg_scale = float(value)
            self.update_bg_line()
        except ValueError:
            pass
            
    _bg_pattern = None
    def get_bg_pattern_value(self): return self._bg_pattern
    def set_bg_pattern_value(self, value):
        self._bg_pattern = value
        self.update_bg_line()

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
        self.update_smooth_pattern()
        self.update_smooth_line()

    def on_sdtype(self, prop_name, value):
        self.update_smooth_pattern()
        self.update_smooth_line()
        
    _shift_value = 0.0
    shifted_line = None
    reference_line = None
    def get_shift_value_value(self): return self._shift_value
    def set_shift_value_value(self, value):
        try:
            self._shift_value = float(value)
            self.update_shifted_line()
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
    #      Methods & Functions
    # ------------------------------------------------------------        
    def set_figure(self, figure):
        PyXRDLine.set_figure(self, figure)
        for child in [self.bg_line, self.smooth_line, self.shifted_line, self.reference_line]:
            if child: child.set_figure(figure)

    def set_axes(self, axes):
        PyXRDLine.set_axes(self, axes)
        for child in [self.bg_line, self.smooth_line, self.shifted_line, self.reference_line]:
            if child: child.set_axes(axes)
    
    def set_transform(self, transform):
        PyXRDLine.set_transform(self, transform)
        for child in [self.bg_line, self.smooth_line, self.shifted_line, self.reference_line]:
            if child: child.set_transform(self.get_transform())
    
    def draw(self, renderer):
        if self.parent.display_experimental:
            PyXRDLine.draw(self, renderer)
            for line in [self.bg_line, self.smooth_line, self.shifted_line, self.reference_line]:
                line.draw(renderer, self.scale, self.offset)
    
    def __init__(self, *args, **kwargs):
        self.smooth_line = ScaledLine([],[], c="#660099", lw="2")
        self.bg_line = ScaledLine([],[], c="#660099", lw="2")
        self.shifted_line = ScaledLine([],[], c="#660099", lw="2")
        self.reference_line = ScaledLine([],[], c="#660099", lw="2", ls="--")
        PyXRDLine.__init__(self, *args, **kwargs)
    
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
        
    def update_bg_line(self):
        self.recache()
        x_data, y_data = self.xy_store.get_raw_model_data()
        if self.bg_type == 0 and self._bg_position != 0.0:
            xmin, xmax = np.min(x_data), np.max(x_data)
            self.bg_line.set_data((xmin, xmax), (self.bg_position, self.bg_position))
            self.bg_line.set_visible(True)            
        elif self.bg_type == 1 and self.bg_pattern != None:
            bg = ((self.bg_pattern * self.bg_scale) + self.bg_position)
            self.bg_line.set_data(x_data, bg)
            self.bg_line.set_visible(True)
        else:
            self.bg_line.set_data([],[])
            self.bg_line.set_visible(False)

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
            #self.xy_store._model_data_y = smoothed
        self.smooth_degree = 0.0
        self.needs_update.emit()
    
    def update_smooth_pattern(self):
        x_data, y_data = self.xy_store.get_raw_model_data()
        degree = int(self.smooth_degree)
        if degree > 1:
            self.smooth_pattern = x_data, smooth(y_data, degree)
        else:
            self.smooth_pattern = [],[]
            
    def update_smooth_line(self):
        self.update_smooth_pattern()
        self.smooth_line.set_data(*self.smooth_pattern)
        self.smooth_line.set_visible(( self._smooth_degree > 1))    
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
            
    def update_shifted_line(self):
        x_data, y_data = self.xy_store.get_raw_model_data()
        if self.shift_value!=0.0:
            self.shifted_line.set_data(x_data-self._shift_value, y_data.copy())
            self.shifted_line.set_visible(True)
            position = self.parent.parent.goniometer.get_2t_from_nm(self.shift_position)
            ymax = np.max(y_data)
            self.reference_line.set_data((position, position), (0, ymax))
            self.reference_line.set_visible(True)            
        else:
            self.shifted_line.set_data([],[])
            self.shifted_line.set_visible(False)
            self.reference_line.set_data([],[])
            self.reference_line.set_visible(False)
            
        trans = self.get_transform()
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
