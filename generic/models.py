# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from collections import namedtuple

import matplotlib
from matplotlib.lines import Line2D
import matplotlib.transforms as transforms

import numpy as np

from gtkmvc.model import Model, Signal

from generic.metaclasses import PyXRDMeta
from generic.treemodels import XYListStore
from generic.io import Storable, PyXRDDecoder
from generic.utils import smooth, delayed

"""def add_cbb_props(*props): #TODO get this into the metaclass
    props, mappers, callbacks = zip(*props)
    prop_dict = dict(zip(props, zip(mappers, callbacks)))

    @Model.getter(*props)
    def get_cbb_prop(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @Model.setter(*props)
    def set_cbb_prop(self, prop_name, value):
        value = prop_dict[prop_name][0](value)
        if value in getattr(self, "_%ss" % prop_name): 
            setattr(self, "_%s" % prop_name, value)
            callback = prop_dict[prop_name][1]
            if callable(callback):
                prop_dict[prop_name][1](self, prop_name, value)
        else:
            raise ValueError, "'%s' is not a valid value for %s!" % (value, prop_name)"""

class MultiProperty(object):
    def __init__(self, value, mapper, callback, options):
        object.__init__(self)
        self.value = value
        self.mapper = mapper
        self.callback = callback
        self.options = options
        
    def create_accesors(self, prop):
        def getter(model):
            return getattr(model, prop)
        def setter(model, value):
            value = self.mapper(value)
            if value in self.options:
                setattr(model, prop, value)
                if callable(self.callback):
                    self.callback(model, prop, value)
            else:
                raise ValueError, "'%s' is not a valid value for %s!" % (value, prop)
        return getter, setter

class PropIntel(object):
    _container = None
    @property
    def container(self):
        return self._container
    @container.setter
    def container(self, value):
        self._container = value

    _label = ""
    @property
    def label(self):
        if callable(self._label):
            return self._label(self, self.container)
        else:
            return self._label
    @label.setter
    def label(self, value):
        self._label = value
        
    def __init__(self, **kwargs):
        object.__init__(self)
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
    pass #end of class

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

from generic.metaclasses import get_new_uuid, pyxrd_object_pool

class PyXRDModel(Model):
    __metaclass__ = PyXRDMeta
    __model_intel__ = [
        PropIntel(name="uuid",    inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str, refinable=False, storable=True, observable=False,  has_widget=False),
    ]
    
    @property
    def uuid(self): return self.__uuid__
    
    def __init__(self, *args, **kwargs):
        Model.__init__(self, *args, **kwargs)
        self.__stored_uuids__ = list()
    
    def stack_uuid(self):
        self.__stored_uuids__.append(self.__uuid__)
        pyxrd_object_pool.remove_object(self)
        self.__uuid__ = get_new_uuid()
        pyxrd_object_pool.add_object(self)
        
    def restore_uuid(self):
        pyxrd_object_pool.remove_object(self)
        self.__uuid__ = self.__stored_uuids__.pop()
        pyxrd_object_pool.add_object(self)
        
    def get_prop_intel_by_name(self, name):
        for prop in self.__model_intel__:
            if prop.name == name:
                return prop
                
    pass # end of class

class ChildModel(PyXRDModel):

    #MODEL INTEL:
    __parent_alias__ = None
    __model_intel__ = [
        PropIntel(name="parent",    inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="removed",   inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="added",     inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
    ]

    #SIGNALS:
    removed = None
    added = None

    #PROPERTIES:
    _parent = None
    def get_parent_value(self): return self._parent
    def set_parent_value(self, value):
        self._unattach_parent()
        self._parent = value
        self._attach_parent()

    def __init__(self, parent=None):
        PyXRDModel.__init__(self)
        self.removed = Signal()
        self.added = Signal()
        
        self.parent = parent
        if self.__parent_alias__ != None:
            setattr(self.__class__, self.__parent_alias__, property(lambda self: self.parent)) 

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
    __model_intel__ = [ #TODO add labels
        PropIntel(name="label",             inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=False),
        PropIntel(name="xy_store",          inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=True,  observable=True,  has_widget=False),
        PropIntel(name="offset",            inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="color",             inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=True,  observable=False, has_widget=False),
    ]

    #PROPERTIES:
    xy_empty_data = ([],[])
    xy_store = None

    _offset = 0
    def get_offset_value(self): return self._offset
    def set_offset_value(self, value):
        self._offset = float(value)
        self.update_line()
        
    def get_label_value(self): return self.get_label()
    def set_label_value(self, value): self.set_label(value)

    def get_color_value(self):
        return matplotlib.colors.rgb2hex(
            matplotlib.colors.colorConverter.to_rgb(self.get_color()))
    def set_color_value(self, value): self.set_colorimp(value)

    
    @property
    def max_intensity(self):
        if len(self.xy_store._model_data_x) > 1:
            return np.max(self.xy_store._model_data_y)
        else:
            return 0    
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, xy_store=None, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
        self.xy_store = xy_store or XYListStore()
        self.xy_store.connect('row-deleted', self.on_treestore_changed)
        self.xy_store.connect('row-inserted', self.on_treestore_changed)
        self.xy_store.connect('row-changed', self.on_treestore_changed)

        Line2D.__init__(self, *self.xy_store.get_raw_model_data(), **kwargs)
        
        self._inhibit_updates = False
        self.update_line()

    
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
        self.xy_store.save_data(self, "%s %s" % (self.parent.data_name, self.parent.data_sample), filename)
         
    def load_data(self, *args, **kwargs):    
        self._inhibit_updates = True
        self.xy_store.load_data(*args, **kwargs)
        self._inhibit_updates = False
        self.update_line()
            
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    def get_transform_factors(self):
        if self.parent:
            return self.parent.scale_factor_y(self.offset)
        else:
            return 1.0, self.offset

    def _transform_y(self, y):
        scale, offset = self.get_transform_factors()
        return np.array(y) * scale + offset
        
    def on_treestore_changed(self, treemodel, path, *args):
        self.update_line()
    
    def set_data(self, x, y):
        self._inhibit_updates = True
        Line2D.set_data(self, x, y)
        self.xy_store.update_from_data(x, y)
        self._inhibit_updates = False
        
    def set_xdata(self, x):
        Line2D.set_xdata(self, x)
        if not self._inhibit_updates:
            self.xy_store.update_from_data(x, self.get_ydata())
        
    def set_ydata(self, y):
        Line2D.set_ydata(self, self._transform_y(y))
        if not self._inhibit_updates:
            self.xy_store.update_from_data(self.get_xdata(), y)
            
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
        temp_y = self._yorig
        self._yorig = temp_y * scale + offset
        print self._yorig
        self.recache(always=True)
        self._yorig = temp_y
        Line2D.draw(self, renderer)
        

class CalculatedLine(PyXRDLine):

    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="child_lines",       inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
    ]
    
    #PROPERTIES:
    _child_lines = None
    def get_child_lines_value(self):
        if self._child_lines==None:
            self._child_lines = []
        return self._child_lines

    def set_figure(self, figure):
        PyXRDLine.set_figure(self, figure)
        for child in self.child_lines:
            if child: child.set_figure(figure)

    def set_axes(self, axes):
        PyXRDLine.set_axes(self, axes)
        for child in self.child_lines:
            if child: child.set_axes(axes)
    
    def draw(self, renderer):
        PyXRDLine.draw(self, renderer)
        scale, offset = self.get_transform_factors()
        for line in self.child_lines:
            if line: line.draw(renderer, scale, offset)
    
    def set_transform(self, transform):
        PyXRDLine.set_transform(self, transform)
        for line in self.child_lines:
            if line: line.set_transform(self.get_transform())

    def set_childs_visible(self, visible):
        for child in self.child_lines:
            if child: child.set_visible(visible)

    def update_child_lines(self, child_data):
        clen = len(child_data)
        mlen = len(self.child_lines)
        diff = mlen-clen
        print diff
        if diff>0: #too many child line instances
            self._child_lines = self._child_lines[:-diff]
        elif diff<0: #too few child line instances
            self._child_lines.extend([None]*-diff)
        axes = self.get_axes()
        figure = self.get_figure()
        for i, (color, ydata) in enumerate(child_data):
            line = self._child_lines[i]
            if not line:
                line = ScaledLine([],[])
                self._child_lines[i] = line
            line.set_data(self.get_xdata(), ydata)
            line.set_color(color)
            if axes: line.set_axes(axes)
            if figure: line.set_figure(figure)
        

class ExperimentalLine(PyXRDLine):

    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="bg_position",       inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="bg_scale",          inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="bg_pattern",        inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="bg_type",           inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=int,    refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="smooth_degree",     inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=int,    refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="smooth_type",       inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=int,    refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="shift_value",       inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="shift_position",    inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
    ]
    
    #PROPERTIES:
    _bg_position = 0
    bg_line = None
    def get_bg_position_value(self): return self._bg_position
    def set_bg_position_value(self, value):
        self._bg_position = float(value)
        self.update_bg_line()

    _bg_scale = 1.0
    def get_bg_scale_value(self): return self._bg_scale
    def set_bg_scale_value(self, value):
        self._bg_scale = float(value)
        self.update_bg_line()
            
    _bg_pattern = None
    def get_bg_pattern_value(self): return self._bg_pattern
    def set_bg_pattern_value(self, value):
        self._bg_pattern = value
        self.update_bg_line()

    def get_bg_type_lbl(self):
        return self._bg_types[self._bg_type]    
    def on_bgtype(self, prop_name, value):
        self.find_bg_position()
        self.find_bg_scale()

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
        self._shift_value = float(value)
        self.update_shifted_line()
  
    def on_shift(self, prop_name, value):
        self.find_shift_value()
    
    shift_position = MultiProperty(0.42574, float, on_shift, { 
        0.42574: "Quartz\t(SiO2)",
        0.3134: "Silicon\t(Si)",
        0.2476: "Zincite\t(ZnO)",
        0.2085: "Corundum\t(Al2O3)"
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
        PyXRDLine.draw(self, renderer)      
        if self.bg_line: self.bg_line.draw(renderer)
        if self.smooth_line: self.smooth_line.draw(renderer)
        if self.shifted_line: self.shifted_line.draw(renderer)
        if self.reference_line: self.reference_line.draw(renderer)
    
    # ------------------------------------------------------------
    #      Background Removal
    # ------------------------------------------------------------
    def remove_background(self):
        y_data = self.xy_store._model_data_y
        bg = 0
        if self.bg_type == 0:
            bg = self.bg_position
        elif self.bg_type == 1 and self.bg_pattern != None and not (self.bg_position == 0 and self.bg_scale == 0):
            bg = self.bg_pattern * self.bg_scale + self.bg_position
        if bg!=0:
            y_data -= bg
            self.set_data(self.xy_store._model_data_x, y_data)
        self.bg_pattern = None
        self.bg_scale = 0.0
        self.bg_position = 0.0
        self.update_line()
        
    def find_bg_position(self):
        self.bg_position = np.min(self.xy_store._model_data_y)
        
    def find_bg_scale(self):
        pass #TODO
        
    def update_bg_line(self):
        if not self.bg_line:
            self.bg_line = Line2D([],[], c="#660099")
            
        if self.bg_type == 0 and self._bg_position != 0.0:
            xmin, xmax = np.min(self._x), np.max(self._y)
            self.bg_line.set_data([(xmin, self.bg_position),(xmax, self.bg_position)])
            self.bg_line.set_visible(True)            
        elif self.bg_type == 1 and self.bg_pattern != None:
            bg = ((self.bg_pattern * self.bg_scale) + self.bg_position)
            self.bg_line.set_data(self.xy_store._model_data_x, bg)
            self.bg_line.set_visible(True)
        else:
            self.bg_line.set_data([],[])
            self.bg_line.set_visible(False)

        self.bg_line.set_transform(self.get_transform())
        
    # ------------------------------------------------------------
    #       Data Smoothing
    # ------------------------------------------------------------
    def smooth_data(self):
        y_data = self.xy_store._model_data_y
        if self.smooth_degree > 0:
            degree = int(self.smooth_degree)
            smoothed = smooth(y_data, degree)
            #smoothed = y_data[:degree] + smoothed + y_data[-degree:]
            self.xy_store._model_data_y = smoothed
        self.smooth_degree = 0.0
        self.update_line()
    
    def update_smooth_pattern(self):
        y_data = self.xy_store._model_data_y
        if self.smooth_degree > 0:
            degree = int(self.smooth_degree)
            self.smooth_pattern = smooth(y_data, degree)
    
    def update_smooth_line(self):
        if not self.smooth_line:
            self.smooth_line = Line2D([],[], c="#660099")
        
        if self._smooth_degree != 0.0:
            self.smooth_line.set_data(self.xy_store._model_data_x, ydata=self.smooth_pattern)
            self.smooth_line.set_visible(True)            
        else:
            self.smooth_line.set_data([],[])
            self.smooth_line.set_visible(False)
    
        self.smooth_line.set_transform(self.get_transform())
        
           
    # ------------------------------------------------------------
    #       Data Shifting
    # ------------------------------------------------------------
    def shift_data(self):
        x_data = self.xy_store._model_data_x
        if self.shift_value != 0.0:
            self.set_xdata(x_data - self.shift_value)
            if self.specimen:
                for marker in self.specimen.data_markers._model_data:
                    marker.data_position = marker.data_position-self.shift_value
        self.shift_value = 0.0
        self.update_line()
            
    def update_shifted_line(self):
        yfactor, offset = self.scale_factor_y
              
        if not self.shifted_line:
            self.shifted_line = Line2D([],[], c="#660099")
        if not self.reference_line:
            self.reference_line = Line2D([],[], c="#660099", ls="--")
               
        if self.shift_value!=0.0:
            self.shifted_line.set_data(self.xy_store._model_data_x-self._shift_value, self.xy_store._model_data_y)
            position = self.parent.parent.data_goniometer.get_2t_from_nm(self.shift_position)
            ymax = np.max(self._y)
            self.reference_line.set_data([(position, 0), (position, ymax)])
        else:
            self.shifted_line.set_data([],[])
            self.shifted_line.set_visible(False)
            self.reference_line.set_data([],[])
            self.reference_line.set_visible(False)
            
        trans = self.get_transform()
        self.shifted_line.set_transform(trans)
        self.reference_line.set_transform(trans)
            
    def find_shift_value(self):
        position = self.parent.parent.data_goniometer.get_2t_from_nm(self.shift_position)
        if position > 0.1:
            x_data = self.xy_store._model_data_x
            y_data = self.xy_store._model_data_y
            max_x = position + 0.5
            min_x = position - 0.5
            condition = (x_data>=min_x) & (x_data<=max_x)
            section_x, section_y = np.extract(condition, x_data), np.extract(condition, y_data)
            actual_position = section_x[np.argmax(section_y)]
            self.shift_value = actual_position - position 
        
        

"""class XYData(ChildModel, Storable):

    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="data_name",         inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=False),
        PropIntel(name="data_label",        inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=False),
        PropIntel(name="xy_data",           inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=True,  observable=True,  has_widget=False),
        PropIntel(name="needs_update",      inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="display_offset",    inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="bg_position",       inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="bg_scale",          inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="bg_pattern",        inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="bg_type",           inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=int,    refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="sd_degree",         inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=int,    refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="sd_type",           inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=int,    refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="shift_value",       inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="shift_position",    inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="color",             inh_name=None,  label="", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=True,  observable=False, has_widget=False),
    ]

    #SIGNALS:
    needs_update = None

    #PROPERTIES:
    xy_empty_data = ([0,0],[0,0])
    line = None
    
    xy_data = None

    _data_name = "XYData"    
    def get_data_name_value(self): return self._data_name
    def set_data_name_value(self, value):
        self._data_name = str(value)
        self.line.set_label(self.data_label)

    _data_label = "%(name)s"
    def get_data_label_value(self): return self._data_label % { 'name': self._data_name }
    def set_data_label_value(self, value):
        self._data_label = str(value)
        self.line.set_label(self.data_label)
    
    _display_offset = 0
    def get_display_offset_value(self): return self._display_offset
    def set_display_offset_value(self, value):
        self._display_offset = float(value)
        
    _bg_position = 0
    bg_line = None
    def get_bg_position_value(self): return self._bg_position
    def set_bg_position_value(self, value):
        self._bg_position = float(value)
        self.needs_update.emit()

    _bg_scale = 1.0
    def get_bg_scale_value(self): return self._bg_scale
    def set_bg_scale_value(self, value):
        self._bg_scale = float(value)
        self.needs_update.emit()
            
    _bg_pattern = None
    def get_bg_pattern_value(self): return self._bg_pattern
    def set_bg_pattern_value(self, value):
        self._bg_pattern = value
        self.needs_update.emit()

    _sd_degree = 0
    sd_pattern = None
    sd_line = None
    def get_sd_degree_value(self): return self._sd_degree
    def set_sd_degree_value(self, value):
        self._sd_degree = float(value)
        self.try_smooth_data()
        self.needs_update.emit()

    _shift_value = 0.0
    shifted_line = None
    reference_line = None
    def get_shift_value_value(self): return self._shift_value
    def set_shift_value_value(self, value):
        self._shift_value = float(value)
        self.needs_update.emit()
  
    def on_shift(self, prop_name, value):
        self.find_shift_value()
    def get_bg_type_lbl(self):
        return self._bg_types[self._bg_type]    
    def on_bgtype(self, prop_name, value):
        self.find_bg()
    
    shift_position = MultiProperty(0.42574, float, on_shift, { 
        0.42574: "Quartz\t(SiO2)",
        0.3134: "Silicon\t(Si)",
        0.2476: "Zincite\t(ZnO)",
        0.2085: "Corundum\t(Al2O3)"
    })
    sd_type = MultiProperty(0, int, None, { 0: "Moving Triangle" })
    bg_type = MultiProperty(0, int, on_bgtype, { 0: "Linear", 1: "Pattern" })
               
    @property
    def color(self):
        return self.line.get_color()
    @color.setter
    def color(self, color):
        if self.color != color:
            self.line.set_color(color)
            if self.line.get_visible() and self.line.get_axes() != None:
                self.needs_update.emit()
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name=None, data_label=None, xy_data=None, color="#0000FF", parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
        self.needs_update = Signal()
        
        self._data_name = data_name or self._data_name
        self._data_label = data_label or self._data_label
        self.line = matplotlib.lines.Line2D(*self.xy_empty_data, label=self.data_label, color=color, aa=True, lw=2)
        self.xy_data = xy_data or XYListStore()
        
        self.update_data()
    
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------    
    @staticmethod
    def from_json(data_name=None, data_label=None, xy_data=None, color=None, **kwargs):
        xy_data = PyXRDDecoder().__pyxrd_decode__(xy_data)
        return XYData(data_name=data_name, data_label=data_label, xy_data=xy_data, color=color)
            
    def save_data(self, filename):
        self.xy_data.save_data(self, "%s %s" % (self.parent.data_name, self.parent.data_sample), filename)
         
    def load_data(self, data, format="DAT", has_header=True, clear=True, silent=False):    
        self.xy_data.load_data(data, format, has_header, clear)
        self.update_data(silent=silent)
            
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    @property
    def max_intensity(self):
        if len(self.xy_data._model_data_x) > 1:
            return np.max(self.xy_data._model_data_y)
        else:
            return 0
    
    def update_from_data(self, data_x, data_y):
        self.xy_data.update_from_data(data_x, data_y)
        self.update_data()
    
    @property
    def scale_factor_y(self):
        if self.parent:
            return self.parent.scale_factor_y(self._display_offset)
        else:
            return 1.0, self._display_offset
    
    def update_data(self, silent=False):
        if len(self.xy_data._model_data_x) > 1:
            
            data_x = self.xy_data._model_data_x
            data_y = self.xy_data._model_data_y
                        
            yscale, offset = self.scale_factor_y
            data_y = data_y * yscale
            trans = transforms.Affine2D().translate(0, offset)
            data = trans.transform(np.array([data_x, data_y]).transpose())
            self.line.set_data(np.transpose(data))
            self.line.set_visible(True)
        else:
            self.line.set_data(self.xy_empty_data)
            self.line.set_visible(False)
        if not silent: self.needs_update.emit()
    
    def clear(self, update=True):
        if len(self.xy_data._model_data_x) > 1:
            self.xy_data.clear()
            if update: self.update_data()
    
    def remove_from_plot(self, figure, axes, pctrl):
        try: self.line.remove()
        except: pass   
        try: self.bg_line.remove()
        except: pass   
        try: self.sd_line.remove()
        except: pass  
        try: self.shifted_line.remove()
        except: pass
    
    def on_update_plot(self, figure, axes, pctrl):
        self.update_data(silent=True)
        
        if self.data_name == "Calculated Profile":
            print "ON UPDATE PLOT"
        
        #Add pattern
        lines = axes.get_lines()
        if not self.line in lines:
            axes.add_line(self.line)
        
        def try_or_die(line):
            try: line.remove()
            except: pass            
        
        yfactor, offset = self.scale_factor_y
        
        #Add bg line (if present)
        try_or_die(self.bg_line)
        if self.bg_type == 0 and self._bg_position != 0.0:
            self.bg_line = axes.axhline(y=self.bg_position*yfactor, c="#660099")
        elif self.bg_type == 1 and self.bg_pattern != None:
            bg = ((self.bg_pattern * self.bg_scale) + self.bg_position) * yfactor
            self.bg_line = matplotlib.lines.Line2D(xdata=self.xy_data._model_data_x, ydata=bg, c="#660099")
            axes.add_line(self.bg_line)
        else:
            self.bg_line = None
            
        #Add bg line (if present)
        try_or_die(self.sd_line)
        if self._smooth_degree != 0.0:
            self.sd_line = matplotlib.lines.Line2D(xdata=self.xy_data._model_data_x, ydata=self.sd_data, c="#660099")
            axes.add_line(self.sd_line)
        else:
            self.sd_line = None
    
        #Add shifted line (if present)
        try_or_die(self.shifted_line)
        try_or_die(self.reference_line)
        if self._shift_value != 0.0:
            self.shifted_line = matplotlib.lines.Line2D(xdata=(self.xy_data._model_data_x-self._shift_value), ydata=self.xy_data._model_data_y, c="#660099")
            position = self.parent.parent.data_goniometer.get_2t_from_nm(self.shift_position)
            self.reference_line = axes.axvline(x=position, c="#660099", ls="--")     
            axes.add_line(self.shifted_line)
        else:
            self.shifted_line = None
            self.reference_line = None
    
    # ------------------------------------------------------------
    #      Background Removal
    # ------------------------------------------------------------
    def remove_background(self):
        y_data = self.xy_data._model_data_y
        bg = 0
        if self.bg_type == 0:
            bg = self.bg_position
        elif self.bg_type == 1 and self.bg_pattern != None and not (self.bg_position == 0 and self.bg_scale == 0):
            bg = self.bg_pattern * self.bg_scale + self.bg_position
        y_data -= bg
        self.xy_data._model_data_y = y_data - np.min(y_data)
        self.bg_pattern = None
        self.bg_scale = 0.0
        self.bg_position = 0.0
        self.update_data()
        
    def find_bg(self):
        if self.bg_type == 0:
            y_min = np.min(self.xy_data._model_data_y)
            self.bg_position = y_min
        #elif self.bg_type == 1:
        #    self.bg_scale = #TODO
           


    # ------------------------------------------------------------
    #       Data Smoothing
    # ------------------------------------------------------------
    def smooth_data(self):
        y_data = self.xy_data._model_data_y
        if self.smooth_degree > 0:
            degree = int(self.smooth_degree)
            smoothed = smooth(y_data, degree)
            #smoothed = y_data[:degree] + smoothed + y_data[-degree:]
            self.xy_data._model_data_y = smoothed
        self.smooth_degree = 0.0
        self.update_data()            
    
    def try_smooth_data(self):
        y_data = self.xy_data._model_data_y
        if self.smooth_degree > 0:
            degree = int(self.smooth_degree)
            smoothed = smooth(y_data, degree)
            self.sd_data = smoothed
           
    # ------------------------------------------------------------
    #       Data Shifting
    # ------------------------------------------------------------
    def shift_data(self):
        x_data = self.xy_data._model_data_x
        if self.shift_value != 0.0:
            x_data = x_data - self.shift_value
            self.xy_data._model_data_x = x_data
            for marker in self.parent.data_markers._model_data:
                marker.data_position = marker.data_position-self.shift_value
        self.shift_value = 0.0
        self.update_data()
            
    def find_shift_value(self):
        position = self.parent.parent.data_goniometer.get_2t_from_nm(self.shift_position)
        if position > 0.1:
            x_data = self.xy_data._model_data_x
            y_data = self.xy_data._model_data_y
            max_x = position + 0.5
            min_x = position - 0.5
            condition = (x_data>=min_x) & (x_data<=max_x)
            section_x, section_y = np.extract(condition, x_data), np.extract(condition, y_data)
            actual_position = section_x[np.argmax(section_y)]
            self.shift_value = actual_position - position
            
    pass #end of class"""

