# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from gtkmvc.model import Signal

import settings

from generic.calculations.CSDS import calculate_distribution
from generic.calculations.data_objects import CSDSData
from generic.models import ChildModel, PropIntel
from generic.io import storables, Storable

from generic.refinement.mixins import RefinementGroup, RefinementValue

class _AbstractCSDSDistribution(ChildModel, Storable):

    #MODEL INTEL:
    __parent_alias__ = "phase"
    __description__ = "Abstract CSDS distr."
    __explanation__ = ""
    __model_intel__ = [
        PropIntel(name="distrib",   label="CSDS Distribution", data_type=unicode, is_column=True, has_widget=True),
        PropIntel(name="inherited", label="Inherited",         data_type=bool),
        PropIntel(name="updated",   label="",                  data_type=object),
    ]

    #SIGNALS:
    updated = None
    
    #PROPERTIES:
    inherited = False
    
    _distrib = None
    def get_distrib_value(self):
        if self._distrib==None:
            self.update_distribution()
        return self._distrib

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
                
        self.updated = Signal()
        self.setup(**kwargs)
        
    def setup(self, **kwargs):
        raise NotImplementedError        
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------        
    def update_distribution(self):
        raise NotImplementedError

    pass #end of class   

class _LogNormalMixin(object):
    
    _data_object = None
    @property
    def data_object(self):
        return self._data_object
    
    #PROPERTIES:
    def get_maximum_value(self): return self._data_object.maximum
    def get_minimum_value(self): return self._data_object.minimum
    
    def get_average_value(self): return self._data_object.average
    def set_average_value(self, value):
        if value < 1.0:
            self._data_object.average = 1.0  #re-apply
            self._data_object.maximum = int(settings.LOG_NORMAL_MAX_CSDS_FACTOR * self.average)
            self.update_distribution()
            return
        try:
            self._data_object.average = float(value)
            self._data_object.maximum = int(settings.LOG_NORMAL_MAX_CSDS_FACTOR * self.average)
            self.update_distribution()
        except ValueError:
            pass
            
    def get_alpha_scale_value(self): return self._data_object.alpha_scale
    def set_alpha_scale_value(self, value):
        self._data_object.alpha_scale = float(value)
        self.update_distribution()
    
    def get_alpha_offset_value(self): return self._data_object.alpha_offset
    def set_alpha_offset_value(self, value):
        self._data_object.alpha_offset = float(value)
        self.update_distribution()
        
    def get_beta_scale_value(self): return self._data_object.beta_scale
    def set_beta_scale_value(self, value):
        self._data_object.beta_scale = float(value)
        self.update_distribution()
        
    def get_beta_offset_value(self): return self._data_object.beta_offset
    def set_beta_offset_value(self, value):
        self._data_object.beta_offset = float(value)
        self.update_distribution()
        
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------       
    def setup(self, average=10, alpha_scale=0.9485, alpha_offset=-0.0017,
            beta_scale=0.1032, beta_offset=0.0034):
            
        self._data_object = CSDSData()
            
        self._data_object.average = average
        self._data_object.maximum = int(settings.LOG_NORMAL_MAX_CSDS_FACTOR * average)        
        self._data_object.minimum = 1
        self._data_object.alpha_scale = alpha_scale
        self._data_object.alpha_offset = alpha_offset
        self._data_object.beta_scale = beta_scale
        self._data_object.beta_offset = beta_offset
        self.update_distribution()

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------            
    def update_distribution(self):
        self._distrib = calculate_distribution(self.data_object)
        self.updated.emit()
                
    pass #end of class

@storables.register()
class LogNormalCSDSDistribution(RefinementGroup, _LogNormalMixin, _AbstractCSDSDistribution):

    #MODEL INTEL:
    __description__ = "Generic log-normal CSDS distr. (Eberl et al. 1990)"
    __model_intel__ = [
        PropIntel(name="maximum",       label="Maximum CSDS",      minimum=1,     maximum=1000,   is_column=True,  data_type=float),
        PropIntel(name="minimum",       label="Minimum CSDS",      minimum=1,     maximum=1000,   is_column=True,  data_type=float),
        PropIntel(name="average",       label="Average CSDS",      minimum=1,     maximum=200,    is_column=True,  data_type=float,   refinable=True,  storable=True,     has_widget=True),
        
        PropIntel(name="alpha_scale",   label="α scale factor",    minimum=0,   maximum=10, is_column=True,  data_type=float,   refinable=True,  storable=True,     has_widget=True),
        PropIntel(name="alpha_offset",  label="α offset factor",   minimum=-5,   maximum=5, is_column=True,  data_type=float,   refinable=True,  storable=True,     has_widget=True),
        PropIntel(name="beta_scale",    label="β² scale factor",   minimum=0,   maximum=10, is_column=True,  data_type=float,   refinable=True,  storable=True,     has_widget=True),
        PropIntel(name="beta_offset",   label="β² offset factor",  minimum=-5,   maximum=5, is_column=True,  data_type=float,   refinable=True,  storable=True,     has_widget=True),
    ]
    __store_id__ = "LogNormalCSDSDistribution"
        
    #REFINEMENT GROUP IMPLEMENTATION:
    @property
    def refine_title(self):
        return "CSDS Distribution"
    
    pass #end of class
    
@storables.register()    
class DritsCSDSDistribution(RefinementValue, _LogNormalMixin, _AbstractCSDSDistribution):

    #MODEL INTEL:
    __description__ = "Log-normal CSDS distr. (Drits et. al, 1997)"
    __model_intel__ = [
        PropIntel(name="maximum",       label="Maximum CSDS",      minimum=1,     maximum=1000,   is_column=True,  data_type=float),
        PropIntel(name="minimum",       label="Minimum CSDS",      minimum=1,     maximum=1000,   is_column=True,  data_type=float),
        PropIntel(name="average",       label="Average CSDS",      minimum=1,     maximum=200,    is_column=True,  data_type=float,   refinable=True,  storable=True,     has_widget=True),
        
        PropIntel(name="alpha_scale",   label="α scale factor",    minimum=0,   maximum=10, is_column=True,  data_type=float),
        PropIntel(name="alpha_offset",  label="α offset factor",   minimum=-5,   maximum=5, is_column=True,  data_type=float),
        PropIntel(name="beta_scale",    label="β² scale factor",   minimum=0,   maximum=10, is_column=True,  data_type=float),
        PropIntel(name="beta_offset",   label="β² offset factor",  minimum=-5,   maximum=5, is_column=True,  data_type=float),
    ]
    __store_id__ = "DritsCSDSDistribution"
       
    #PROPERTIES:   
    def get_alpha_scale_value(self): return 0.9485
    set_alpha_scale_value = property() #delete this function
    
    def get_alpha_offset_value(self): return 0.017
    set_alpha_offset_value = property() #delete this function
        
    def get_beta_scale_value(self): return 0.1032
    set_beta_scale_value = property() #delete this function
        
    def get_beta_offset_value(self): return 0.0034
    set_beta_offset_value = property() #delete this function
    
    #REFINEMENT VALUE IMPLEMENTATION:
    @property
    def refine_title(self):
        return "Average CSDS"

    @property
    def refine_value(self):
        return self.average
    @refine_value.setter
    def refine_value(self, value):
        self.average = value
        
    @property
    def refine_info(self):
        return self.average_ref_info
        
    @property 
    def is_refinable(self):
        return not self.inherited
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def setup(self, average=10):
        super(DritsCSDSDistribution, self).setup(average=average)
        self.update_distribution()
       
    pass #end of class
        
CSDS_distribution_types = [
    LogNormalCSDSDistribution,
    DritsCSDSDistribution
]
