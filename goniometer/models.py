# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from collections import OrderedDict
import numpy as np

from gtkmvc.model import Model

import time
from scipy.special import erf
from math import sin, cos, pi, sqrt, radians, degrees, asin, tan

from generic.models import ChildModel, PropIntel
from generic.models.mixins import CSVMixin
from generic.custom_math import sqrt2pi, sqrt8
from generic.utils import get_md5_hash
from generic.io import Storable
       
class Goniometer(ChildModel, Storable):
    #MODEL INTEL:
    __parent_alias__ = 'project'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="radius",            data_type=float, storable=True, has_widget=True),
        PropIntel(name="divergence",        data_type=float, storable=True, has_widget=True),
        PropIntel(name="soller1",           data_type=float, storable=True, has_widget=True),
        PropIntel(name="soller2",           data_type=float, storable=True, has_widget=True),
        PropIntel(name="min_2theta",        data_type=float, storable=True, has_widget=True),
        PropIntel(name="max_2theta",        data_type=float, storable=True, has_widget=True),
        PropIntel(name="steps",             data_type=float, storable=True, has_widget=True),
        PropIntel(name="wavelength",        data_type=float, storable=True),
        PropIntel(name="has_ads",           data_type=bool,  storable=True, has_widget=True),
        PropIntel(name="ads_fact",          data_type=float, storable=True, has_widget=True),
        PropIntel(name="ads_phase_fact",    data_type=float, storable=True, has_widget=True),
        PropIntel(name="ads_phase_shift",   data_type=float, storable=True, has_widget=True),
        PropIntel(name="ads_const",         data_type=float, storable=True, has_widget=True),
    ]
    __store_id__ = "Goniometer"
        
    #PROPERTIES:
    radius = 24.0
    divergence = 0.5
    min_2theta = 3.0
    max_2theta = 45.0
    steps = 2500
    wavelength = 0.154056
    
    has_ads = False
    ads_fact = 1.0
    ads_phase_fact = 1.0
    ads_phase_shift = 0.0
    ads_const = 0.0
    
    _dirty_cache = True
    _S = 0
    
    _soller1 = 2.3
    _soller2 = 2.3
    @Model.getter("soller[12]")
    def get_soller(self, prop_name):
        prop_name = "_%s" % prop_name
        return getattr(self, prop_name)
    @Model.setter("soller[12]")
    def set_soller(self, prop_name, value):
        prop_name = "_%s" % prop_name
        if value != getattr(self, prop_name):
            setattr(self, prop_name, value)
            self._dirty_cache = True
        
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, radius = None, divergence = None,
                 soller1 = None, soller2 = None,
                 min_2theta = None, max_2theta = None, steps=2500,
                 wavelength = None, has_ads =  False, ads_fact = 1.0, 
                 ads_phase_fact=1.0, ads_phase_shift = 0.0, ads_const = 0.0,
                 parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        self.radius = radius or self.get_depr(kwargs, 24.0, "data_radius")
        self.divergence = divergence or self.get_depr(kwargs, 0.5, "data_divergence")
        self.soller1 = soller1 or self.get_depr(kwargs, 2.3, "data_soller1")
        self.soller2 = soller2 or self.get_depr(kwargs, 2.3, "data_soller2")
        self.min_2theta = min_2theta or self.get_depr(kwargs, 3.0, "data_min_2theta")
        self.max_2theta = max_2theta or self.get_depr(kwargs, 45.0, "data_max_2theta")
        self.steps = steps
        self.wavelength = wavelength or self.get_depr(kwargs, 0.154056, "data_lambda")
        self.has_ads = has_ads
        self.ads_fact = ads_fact
        self.ads_phase_fact = ads_phase_fact
        self.ads_phase_shift = ads_phase_shift
        self.ads_const = ads_const
        
    def __reduce__(self):
        return (type(self), ((),self.json_properties()))
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------    
    def reset_from_file(self, path):
        new_gonio = Goniometer.load_object(path, parent=None)
        for prop in self.__model_intel__:
            if prop.storable and prop.name!="uuid":
                setattr(self, prop.name, getattr(new_gonio, prop.name))
    
    def get_S(self):
        if self._dirty_cache:
            self._S = sqrt((self.soller1 * 0.5)**2 + (self.soller2 * 0.5)**2)
            self._S1S2 = self.soller1 * self.soller2
            self._dirty_cache = False
        return self._S, self._S1S2
       
    def get_lorentz_polarisation_factor(self, range_theta, ss):
        ss = float(max(ss, 0.0000000000001))
        S, S1S2 = self.get_S()
        Q = S / (sqrt8 * np.sin(range_theta) * ss)
        T = erf(Q) * sqrt2pi / (2.0*ss * S) - 2.0*np.sin(range_theta) * (1.0- np.exp(-(Q**2.0))) / (S**2.0)
        return (1.0 + np.cos(2.0*range_theta)**2) * T / np.sin(range_theta)
       
    def get_nm_from_t(self, theta):
        return self.get_nm_from_2t(2*theta)
    
    def get_nm_from_2t(self, twotheta):
        if twotheta != 0:
            return self.wavelength / (2.0*sin(radians(twotheta/2.0)))
        else:
            return 0.0
        
    def get_t_from_nm(self, nm):
        return self.get_2t_from_nm(nm)/2

    def get_2t_from_nm(self, nm):
        twotheta = 0.0
        if nm != 0: 
            twotheta = degrees(asin(max(-1.0, min(1.0, self.wavelength/(2.0*nm)))))*2.0
        return twotheta
        
    def get_default_theta_range(self, as_radians=True): #TODO cache this
        def torad(val):
            if as_radians:
                return radians(val)
            else:
                return val
        min_theta = torad(self.min_2theta*0.5)
        max_theta = torad(self.max_2theta*0.5)
        delta_theta = float(max_theta - min_theta) / float(self.steps-1)
        theta_range = (min_theta + delta_theta * np.arange(0,self.steps-1, dtype=float))
        return theta_range
        
    _mc_cache = OrderedDict()
    @classmethod
    def _get_mc_range(cls, theta_range, sample_length, absorption, radius, 
            divergence, has_ads, ads_fact, 
            ads_phase_fact, ads_phase_shift, ads_const):
        args = (get_md5_hash(theta_range), sample_length, absorption, radius, 
            divergence, has_ads, ads_fact, 
            ads_phase_fact, ads_phase_shift, ads_const)
        if not args in cls._mc_cache:
            if len(cls._mc_cache) == 10:
                cls._mc_cache.popitem(last=False)
            sin_range = np.sin(theta_range)
            correction_range = np.ones_like(theta_range)
            #Correct for automatic divergence slits first:
            if has_ads:
                test = (divergence * ads_fact / (np.sin(ads_phase_fact*theta_range + radians(ads_phase_shift)) - ads_const))
                correction_range /= test
            #Then correct for sample absorption:
            if absorption > 0.0:
                correction_range *= np.minimum(1.0 - np.exp(-2.0*absorption / sin_range), 1.0)
            #And finally correct for sample length
            if not has_ads:
                L_Rta =  sample_length / (radius * tan(radians(divergence)))
                correction_range *= np.minimum(sin_range * L_Rta, 1)
            #Store calculated correction
            cls._mc_cache[args] = correction_range
        return cls._mc_cache[args]
    
    def get_machine_correction_range(self, theta_range, sample_length, absorption):
        """
            Calculates correction factors for the given theta range, sample
            length and absorption using the information about the machine's
            geometry.
        """
        return Goniometer._get_mc_range(theta_range, sample_length, absorption,
            self.radius, self.divergence, self.has_ads, self.ads_fact,
            self.ads_phase_fact, self.ads_phase_shift, self.ads_const)
       
    pass #end of class
    
Goniometer.register_storable()
