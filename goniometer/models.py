# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import numpy as np

from gtkmvc.model import Model

import time
from scipy.special import erf
from math import sin, cos, pi, sqrt, radians, degrees, asin

from generic.models import ChildModel, PropIntel
from generic.utils import sqrt2pi, sqrt8
from generic.io import Storable
       
class Goniometer(ChildModel, Storable):
    #MODEL INTEL:
    __parent_alias__ = 'project'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="data_radius",       inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_divergence",   inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_soller1",      inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_soller2",      inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_min_2theta",   inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_max_2theta",   inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_lambda",       inh_name=None,  label="", minimum=None,  maximum=None,  is_column=True, ctype=float,    refinable=False, storable=True,  observable=True,  has_widget=True),
    ]
        
    #PROPERTIES:
    data_radius = float(24)
    data_divergence = float(0.5) #slit
    data_min_2theta = float(2)
    data_max_2theta = float(52)
    data_lambda = float(0.154056)
    
    _dirty_cache = True
    _S = 0
    
    _data_soller1 = float(2.3)
    _data_soller2 = float(2.3)
    @Model.getter("data_soller[12]")
    def get_data_soller(self, prop_name):
        prop_name = "_%s" % prop_name
        return getattr(self, prop_name)
    @Model.setter("data_soller[12]")
    def set_data_soller(self, prop_name, value):
        prop_name = "_%s" % prop_name
        if value != getattr(self, prop_name):
            setattr(self, prop_name, value)
            self._dirty_cache = True
        
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_radius = None, data_divergence = None, 
                 data_soller1 = None, data_soller2 = None,
                 data_min_2theta = None, data_max_2theta = None, data_lambda = None, parent=None):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        self.data_radius = data_radius or self.data_radius
        self.data_divergence = data_divergence or self.data_divergence
        self.data_soller1 = data_soller1 or self.data_soller1
        self.data_soller2 = data_soller2 or self.data_soller2
        self.data_min_2theta = data_min_2theta or self.data_min_2theta
        self.data_max_2theta = data_max_2theta or self.data_max_2theta
        self.data_lambda = data_lambda or self.data_lambda
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------    
    def get_S(self):
        if self._dirty_cache:
            self._S = sqrt((self.data_soller1 * 0.5)**2 + (self.data_soller2 * 0.5)**2)
            self._S1S2 = self.data_soller1 * self.data_soller2
            self._dirty_cache = False
        return self._S, self._S1S2
       
    def get_lorentz_polarisation_factor(self, range_theta, ss):
        t1 = time.time()
        ss = float(max(ss, 0.0000000000001))
        S, S1S2 = self.get_S()
        Q = S / (sqrt8 * np.sin(range_theta) * ss)
        T = erf(Q) * sqrt2pi / (2.0*ss * S) - 2.0*np.sin(range_theta) * (1.0- np.exp(-(Q**2.0))) / (S**2.0)
        t2 = time.time()
        #print '%s took %0.3f ms' % ("get_lorentz_polarisation_factor", (t2-t1)*1000.0)
        return (1.0 + np.cos(2.0*range_theta)**2) * T / np.sin(range_theta)
       
    def get_nm_from_t(self, theta):
        return self.get_nm_from_2t(2*theta)
    
    def get_nm_from_2t(self, twotheta):
        if twotheta != 0:
            return self.data_lambda / (2.0*sin(radians(twotheta/2.0)))
        else:
            return 0.0
        
    def get_t_from_nm(self, nm):
        return self.get_2t_from_nm(nm)/2

    def get_2t_from_nm(self, nm):
        twotheta = 0.0
        if nm != 0: 
            twotheta = degrees(asin(max(-1.0, min(1.0, self.data_lambda/(2.0*nm)))))*2.0
        return twotheta
       
    pass #end of class
