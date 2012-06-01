# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from gtkmvc.support.metaclasses import ObservablePropertyMeta

class PyXRDMeta(ObservablePropertyMeta):

    def __init__(cls, name, bases, d):        

        #get the model intel for this class type (excluding bases for now):        
        __model_intel__ = set(d.get("__model_intel__", list()))

        #properties to be generated base on model intel named tuples:
        keys = ["__observables__", "__storables__", "__columns__", "__inheritables__", "__refinables__", "__have_no_widget__"]
    
        #loop over the variables and fetch any custom values for this class (if present):
        for key in keys:
            val = []
            d[key] = set(d[key]) if key in d else set()
        
        #loop over the model intel and generate observables list:
        for prop in __model_intel__:
            if prop.observable: d["__observables__"].add(prop.name)
            
        #add model intel from the base classes to generate the remaining properties, 
        #and replace the variable by a frozenset including the complete model intel for eventual later use:
        for base in bases: __model_intel__ |= getattr(base, "__model_intel__", set())
        setattr(cls, "__model_intel__", frozenset(__model_intel__))            
            
        #generate remaining properties based on model intel (including bases):
        for prop in __model_intel__:
            if prop.storable:   d["__storables__"].add(prop.name)
            if prop.is_column:  d["__columns__"].add((prop.name, prop.ctype))
            if prop.inh_name:   d["__inheritables__"].add(prop.name)
            if prop.refinable:  d["__refinables__"].add(prop.name)
            if not prop.has_widget: d["__have_no_widget__"].add(prop.name)                
                
        #apply properties:
        for key in keys:
            setattr(cls, key, list(d[key]))
            
        return ObservablePropertyMeta.__init__(cls, name, bases, d)
        
    def __call__(cls, *args, **kwargs):
        instance = ObservablePropertyMeta.__call__(cls, *args, **kwargs)
        for prop_intel in instance.__model_intel__:
            prop_intel.container = instance
        return instance
