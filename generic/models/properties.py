# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from warnings import warn
from generic.controllers.handlers import widget_types

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

    inh_name = None
    
    minimum = None
    maximum = None
    
    is_column = False
    data_type = object #type of the value instance
    widget_type = 'input' #string description of the widget type
    widget_handler = None
    refinable = False
    storable = False
    observable = True
    has_widget = False

    def __init__(self, **kwargs):
        object.__init__(self)
        
        if "ctype" in kwargs:
            #deprecated and ignored!
            ctype = kwargs.pop("ctype")
            warn("The use of the keyword '%s' is deprecated for %s!" % ("ctype", type(self)), DeprecationWarning)
        
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
            
        # check if the widget type matches with the data type:
        if 'widget_type' in kwargs:
            data_type = None
            for wid, tp in widget_types:
                if wid == self.widget_type:
                    data_type = tp
            if data_type != self.data_type:
                raise AttributeError, "Data type '%s' does not match with widget type '%s'!" % (self.data_type, self.widget_type)            
        else:
            # if the widget type is not explicitly set,
            # set manually:
            self.widget_type = self._get_default_widget_type()
            
    def __eq__(self, other):
        return other!=None and self.name == other.name

    def __neq__(self, other):
        return other!=None and self.name != other.name

    def _get_default_widget_type(self):
        for wid, tp in widget_types:
            if tp == self.data_type:
                return wid
                
    def get_widget_handler(self):
        if isinstance(self.widget_handler, basestring) and hasattr(self.container, self.widget_handler):
            self.widget_handler = getattr(self.container, self.widget_handler)
            return self.widget_handler

    pass #end of class
