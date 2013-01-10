# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from collections import OrderedDict
from math import sin, cos, pi, sqrt, exp, radians, log

from gtkmvc.model import Signal

import numpy as np

import settings

from generic.utils import lognormal, sqrt2pi, sqrt8, print_timing, get_md5_hash, recgetattr, recsetattr
from generic.io import Storable, PyXRDDecoder
from generic.models import ChildModel, PropIntel

from atoms.models import Atom
from probabilities.models import get_correct_probability_model
from mixture.refinement import RefinementGroup, RefinementValue

class _AbstractCSDSDistribution(ChildModel, Storable):

    #MODEL INTEL:
    __parent_alias__ = "phase"
    __description__ = "Abstract CSDS distr."
    __explanation__ = ""
    __model_intel__ = [
        PropIntel(name="distrib",   label="CSDS Distribution", data_type=str, is_column=True, has_widget=True),
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

class _LogNormalMixin():
    
    #PROPERTIES:
    def get_maximum_value(self): return int(settings.LOG_NORMAL_MAX_CSDS_FACTOR * self.average)
    def get_minimum_value(self): return 1
    
    _average = 10.0
    def get_average_value(self): return self._average
    def set_average_value(self, value):
        if value < 1.0:
            self.average = 1.0  #re-apply
            return
        self._average = value
        self.update_distribution()
    
    _alpha_scale = 0.9485
    def get_alpha_scale_value(self): return self._alpha_scale
    def set_alpha_scale_value(self, value):
        self._alpha_scale = float(value)
        self.update_distribution()
    
    _alpha_offset = -0.017
    def get_alpha_offset_value(self): return self._alpha_offset
    def set_alpha_offset_value(self, value):
        self._alpha_offset = float(value)
        self.update_distribution()
        
    _beta_scale = 0.1032
    def get_beta_scale_value(self): return self._beta_scale
    def set_beta_scale_value(self, value):
        self._beta_scale = float(value)
        self.update_distribution()
        
    _beta_offset = 0.0034
    def get_beta_offset_value(self): return self._beta_offset
    def set_beta_offset_value(self, value):
        self._beta_offset = float(value)
        self.update_distribution()
        
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------       
    def setup(self, average=10, alpha_scale=0.9485, alpha_offset=-0.0017,
            beta_scale=0.1032, beta_offset=0.0034):
        self._average = average or self._average
        self._alpha_scale = alpha_scale or self._alpha_scale
        self._alpha_offset = alpha_offset or self._alpha_offset
        self._beta_scale = beta_scale or self._beta_scale
        self._beta_offset = beta_offset or self._beta_offset
        
        self.update_distribution()

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    
    _distribution_cache = OrderedDict()
    @classmethod
    def get_distribution(cls, Tmean, Tmax, Tmin, alpha_scale, alpha_offset, beta_scale, beta_offset):
        args = (Tmean, Tmax, Tmin, 
                alpha_scale, alpha_offset, 
                beta_scale, beta_offset)
        if not args in cls._distribution_cache:
            if len(cls._distribution_cache) == 100:
                cls._distribution_cache.popitem(last=False)
            cls._distribution_cache[args] = cls._calculate_distribution(*args)
        return cls._distribution_cache[args]
        
    @classmethod
    def _calculate_distribution(cls, Tmean, Tmax, Tmin, alpha_scale, alpha_offset, beta_scale, beta_offset):
        a = alpha_scale * log(Tmean) + alpha_offset
        b = sqrt(beta_scale * log(Tmean) + beta_offset)
            
        steps = int(Tmax - Tmin) + 1
        
        smq = 0
        q_log_distr = []
        TQDistr = dict()
        for i in range(steps):
            T = max(Tmin + i, 1e-50)
            q = lognormal(T, a, b)
            smq += q
            
            TQDistr[int(T)] = q
            
        Rmean = 0
        for T,q in TQDistr.iteritems():
            TQDistr[T] = q / smq
            Rmean += T*q
        Rmean /= smq
            
        return (TQDistr.items(), TQDistr, Rmean)
    
    _update_lock = False
    def update_distribution(self):
        if not self._update_lock:
            self._update_lock = True
            self._distrib = LogNormalCSDSDistribution.get_distribution(
                self.average, self.maximum, self.minimum, 
                self.alpha_scale, self.alpha_offset, 
                self.beta_scale, self.beta_offset
            )
            self.updated.emit()
            self._update_lock = False
    pass #end of class

class LogNormalCSDSDistribution(_LogNormalMixin, _AbstractCSDSDistribution, RefinementGroup):

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
    
LogNormalCSDSDistribution.register_storable()
    
class DritsCSDSDistribution(_LogNormalMixin, _AbstractCSDSDistribution, RefinementValue):

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
        self._average = average or self._average
        
        self.update_distribution()
       
    pass #end of class
    
DritsCSDSDistribution.register_storable()
    
CSDS_distribution_types = [
    LogNormalCSDSDistribution,
    DritsCSDSDistribution
]
