# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk
import gobject

from collections import deque

from gtkmvc import Observable
from gtkmvc.model import ListStoreModel, Model, Signal, Observer

import matplotlib  
from matplotlib.figure import Figure   
#from matplotlib.axes import Subplot   
from matplotlib.backends.backend_gtk import FigureCanvasGTK

import json
import time
from math import sin, cos, pi, sqrt

from generic.treemodels import ObjectListStore, XYListStore, Point
from generic.io import Storable
       
class Goniometer(Model, Observable, Storable):
    data_radius = float(24)
    data_divergence = float(0.5) #slit
    data_min_2theta = float(2)
    data_max_2theta = float(52)
    data_lambda = float(0.154056)
    
    _dirty_cache = True
    _S = 0
    
    _data_soller1 = float(2.3)
    _data_soller2 = float(2.3)
    @Model.getter("data_soller1", "data_soller2")
    def get_data_soller(self, prop_name):
        prop_name = "_%s" % prop_name
        return getattr(self, prop_name)
    @Model.setter("data_soller1", "data_soller2")
    def set_data_soller(self, prop_name, value):
        prop_name = "_%s" % prop_name
        if value != getattr(self, prop_name):
            setattr(self, prop_name, value)
            self._dirty_cache = True    
                    
    __observables__ = ( "data_radius",
                        "data_divergence",
                        "data_soller1",
                        "data_soller2",
                        "data_min_2theta",
                        "data_max_2theta",
                        "data_lambda" )
    __storables__ = __observables__    
        
    def __init__(self, data_radius = None, data_divergence = None, 
                 data_soller1 = None, data_soller2 = None,
                 data_min_2theta = None, data_max_2theta = None, data_lambda = None):
        Model.__init__(self)
        Observable.__init__(self)
        Storable.__init__(self)
        self.data_radius = data_radius or self.data_radius
        self.data_divergence = data_divergence or self.data_divergence
        self.data_soller1 = data_soller1 or self.data_soller1
        self.data_soller2 = data_soller2 or self.data_soller2
        self.data_min_2theta = data_min_2theta or self.data_min_2theta
        self.data_max_2theta = data_max_2theta or self.data_max_2theta
        self.data_lambda = data_lambda or self.data_lambda
        
    
    def get_S(self):
        #if self._dirty_cache:
        #    self._S = sqrt( (self.data_soller1 * 0.5)**2 + (self.data_soller2 * 0.5)**2)
        #    self._dirty_cache = False
        return sqrt( (self.data_soller1 * 0.5)**2 + (self.data_soller2 * 0.5)**2) #self._S
