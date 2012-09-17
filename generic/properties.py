# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

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
    refinable = False
    storable = False
    observable = True
    has_widget = False

    def __init__(self, **kwargs):
        object.__init__(self)
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
            
    def __eq__(self, other):
        return other!=None and self.name == other.name

    def __neq__(self, other):
        return other!=None and self.name != other.name

    pass #end of class
