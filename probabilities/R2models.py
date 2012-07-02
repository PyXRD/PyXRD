# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import numpy as np

from gtkmvc.model import Model

from generic.mathtext_support import mt_range
from generic.models import PropIntel

from probabilities.base_models import _AbstractProbability

class R2G2Model(_AbstractProbability):
	"""
	Reichweite = 2 / Components = 2
	g^2 independent variables = 4
	W0 
	P001 (W0<2/3) of P100 (W0>2/3)
	P10
	P011 (P10<1/2) of P110 (P10>1/2)
	
	W1 = 1 – W0
	P11 = 1-P10
	
	W10 = W1*P10
	W01 = W10 
	W00 = W0 - W10
	W11 = W1*P11
    
    P001 given:                 or      P100 given:
      P100 = (W00 / W10) * P001 or        P001 = (W10 / W00) * P100
    P101 = 1 - P100
    P000 = 1 - P001

    P011 given:                 or      P110 given:
      P110 = (W01 / W11) * P011 or        P001 = (W11 / W01) * P110
    P010 = 1 - P011
    P111 = 1 - P110
	
	indexes are NOT zero-based in external property names!
	"""

    #MODEL INTEL:
    __independent_label_map__ = [
        ("W1", r"$W_1$"),        
        ("P112_or_P211", r"$P_{112} %s$ or $\newlineP_{211} %s$" % (
            mt_range(0.0, "W_1", 2.0/3.0),
            mt_range(2.0/3.0, "W_1", 1.0))
        ),
        ("P21", r"$P_{21}$"),
        ("P122_or_P221", r"$P_{122} %s$ or $\newlineP_{221} %s$" % (
            mt_range(0.0, "W_1", 1.0/2.0),
            mt_range(1.0/2.0, "W_1", 1.0))
        ),
    ]
    __model_intel__ = [
        PropIntel(name=prop, inh_name=None, label=label, minimum=0.0, maximum=1.0, is_column=False, ctype=float, refinable=True, storable=True, observable=True, has_widget=True) \
            for prop, label in __independent_label_map__
    ]

    #PROPERTIES:
    twothirds = 2.0/3.0
    
    _W0 = 0.0
    def get_W1_value(self): return self._W0
    def set_W1_value(self, value):
        self._W0 = min(max(value, 0.5), 1.0)
        self.update()
          
    def get_P112_or_P211_value(self):
        if self._W0 <= self.twothirds:
            return self.mP[0,0,1]
        else:
            return self.mP[1,0,0]
    def set_P112_or_P211_value(self, value):
        if self._W0 <= self.twothirds:
            self.mP[0,0,1] = value
        else:
            self.mP[1,0,0] = value
        self.update()
          
    _P10 = 0.0
    def get_P21_value(self): return self._P10
    def set_P21_value(self, value):
        self._P10 = min(max(value, 0.0), 1.0)
        self.update()

    def get_P122_or_P221_value(self):
        if self._P10 <= 0.5:
            return self.mP[0,1,1]
        else:
            return self.mP[1,1,0]
        self.update() 
    def set_P122_or_P221_value(self, value):
        if self._P10 <= 0.5:
            self.mP[0,1,1] = value
        else:
            self.mP[1,1,0] = value
        self.update()        
    

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.75, P112_or_P211=0.75, P21=0.75, P122_or_P221=0.75):
        _AbstractProbability.setup(self, R=2)    
        self.W1 = W1
        self.P112_or_P211 = P112_or_P211
        self.P21 = P21
        self.P122_or_P221

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    
    #@delayed()
    def update(self):
        W0 = self._W0
        W1 = 1.0 - W0
        
        P10 = self._P10
        P11 = 1 - P10
        
        self.mW[1,0] = W1 * P10
        self.mW[1,1] = W1 * P11
        self.mW[0,1] = self.mW[1,0]
        self.mW[0,0] = W0 - self.mW[1,0]
        
        if W0 <= self.twothirds:
            self.mP[1,0,0] = self.mP[0,0,1] * self.mW[0,0] / self.mW[1,0]
        else:
            self.mP[0,0,1] = self.mP[1,0,0] * self.mW[1,0] / self.mW[0,0]
        self.mP[1,0,1] = 1.0 - self.mP[1,0,0]
        self.mP[0,0,0] = 1.0 - self.mP[0,0,1]
            
        if P10 <= 0.5:
            self.mP[1,1,0] = self.mP[0,1,1] * self.mW[0,1] / self.mW[1,1]
        else:
            self.mP[0,1,1] = self.mP[1,1,0] * self.mW[1,1] / self.mW[0,1]
        self.mP[0,1,0] = 1.0 - self.mP[0,1,1]
        self.mP[1,1,1] = 1.0 - self.mP[1,1,0]
            
        self.validate()
        self.updated.emit()
    
    pass #end of class
