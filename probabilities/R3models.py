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

class R3G2Model(_AbstractProbability):
	"""
	Reichweite = 3 / Components = 2
	Restrictions:
	2/3 <= W0 <= 1.0
	P11 = 0
	P101 = 0
	
	independent variables = 2
	W0
	P0000 (W0<3/4) of P1001 (W0>3/4)
        
        W1 = 1 – W0
        
        P0000 given (W0 < 3/4):
            W100/W000 = W1 / (W0 - 2*W1) 
            P0001 = 1-P0000
            P1000 = P0001 * W100/W000
            P1001 = 1 - P1000
        P1001 given (W0 >= 3/4):
            W000/W100 = (W0 - 2*W1) / W1
            P1000 = 1-P1001
            P0000 = 1 - P1000 * W100/W000
            P0001 = 1 - P0000
            
        P0010 = 1
        P0011 = 0
        
        P0100 = 1
        P0101 = 0
        
        since P11=0 and P101=0:
        P1100 = P1101 = P1010 = P1011 = P1110 = P1111 = P0110 = P0111 = 0
	
	indexes are NOT zero-based in external property names!
	"""

    #MODEL INTEL:
    #FIXME ENFORCE RANGES!
    __independent_label_map__ = [
        ("W1", r"$W_1$"),
        ("P1111_or_P2112", r"$P_{1111} %s$ or $\newline P_{2112} %s$" % (
            mt_range(2.0/3.0, "W_1", 3.0/4.0),
            mt_range(3.0/4.0, "W_1", 1.0))
        ),
    ]
    __model_intel__ = [
        PropIntel(name=prop, label=label, minimum=0.0, maximum=1.0, data_type=float, refinable=True, storable=True, has_widget=True) \
            for prop, label in __independent_label_map__
    ]

    #PROPERTIES:
    twothirds = 2.0/3.0
    
    _W0 = 0.0
    def get_W1_value(self): return self._W0
    def set_W1_value(self, value):
        self._W0 = min(max(value, 0.5), 1.0)
        self.update()
          
    def get_P1111_or_P2112_value(self):
        if self._W0 <= self.twothirds:
            return self.mP[0,0,0,0]
        else:
            return self.mP[1,0,0,1]
    def set_P1111_or_P2112_value(self, value):
        if self._W0 <= self.twothirds:
            self.mP[0,0,0,0] = value
        else:
            self.mP[1,0,0,1] = value
        self.update()   

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.85, P1111_or_P2112=0.75):
        _AbstractProbability.setup(self, R=3)
        self.W1 = W1
        self.P1111_or_P2112 = P1111_or_P2112

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------     
    def update(self):
        W0 = self._W0
        W1 = 1.0 - W0
        
        print W0, self.mP[1,0,0,1]
        
        if W0 >= 0.75: #1,0,0,1 is given
            self.mP[1,0,0,0] = 1.0 - self.mP[1,0,0,1]
            self.mP[0,0,0,0] = 1.0 - self.mP[1,0,0,0] * W1/(W0-2*W1)
            self.mP[0,0,0,1] = 1.0 - self.mP[0,0,0,0]
        else: #0,0,0,0 is given
            self.mP[0,0,0,1] = 1.0 - self.mP[0,0,0,0]
            self.mP[1,0,0,0] = self.mP[0,0,0,1] * (W0-2*W1)/W1
            self.mP[1,0,0,1] = 1.0 - self.mP[1,0,0,0]

        self.mP[0,0,1,0] = 1.0
        self.mP[0,1,0,0] = 1.0
        
        self.mP[0,0,1,1] = 0.0
        self.mP[0,1,0,1] = 0.0
        self.mP[0,1,1,0] = 0.0
        self.mP[0,1,1,1] = 0.0
        self.mP[1,0,1,0] = 0.0
        self.mP[1,0,1,1] = 0.0
        self.mP[1,1,0,0] = 0.0
        self.mP[1,1,0,1] = 0.0
        self.mP[1,1,1,0] = 0.0
        self.mP[1,1,1,1] = 0.0

        #since P11=0 and P101=0:
        self.mW[1,0,1] = self.mW[1,1,0] =  self.mW[1,1,1] = 0.0
        
        t = (1 + 2 * self.mP[0,0,0,1] / self.mP[1,0,0,0])
        self.mW[0,0,0] = W0 / t
        self.mW[1,0,0] = self.mW[0,1,0] = self.mW[0,0,1] = 0.5 * (W0 - self.mW[0,0,0])
        self.mW[0,1,1] = W1 - self.mW[0,0,1]
        
        self.solve()
        self.validate()
        self.updated.emit()
    
    pass #end of class
