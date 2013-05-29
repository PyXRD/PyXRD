# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from gtkmvc.model import Model

from generic.mathtext_support import mt_range
from generic.models import PropIntel
from generic.io import storables
from probabilities.base_models import _AbstractProbability

@storables.register()
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
        PropIntel(name=prop, label=label, minimum=0.0, maximum=1.0, data_type=float, refinable=True, storable=True, has_widget=True) \
            for prop, label in __independent_label_map__
    ]
    __store_id__ = "R2G2Model"

    #PROPERTIES:
    twothirds = 2.0/3.0
    
    def get_W1_value(self): return self.mW[0]
    def set_W1_value(self, value):
        self.mW[0] = min(max(value, 0.5), 1.0)
        self.update()
          
    def get_P112_or_P211_value(self):
        if self.mW[0] <= self.twothirds:
            return self.mP[0,0,1]
        else:
            return self.mP[1,0,0]
    def set_P112_or_P211_value(self, value):
        if self.mW[0] <= self.twothirds:
            self.mP[0,0,1] = value
        else:
            self.mP[1,0,0] = value
        self.update()
          
    def get_P21_value(self): return self.mP[1,0]
    def set_P21_value(self, value):
        self.mP[1,0] = min(max(value, 0.0), 1.0)
        self.update()

    def get_P122_or_P221_value(self):
        if self.mP[1,0] <= 0.5:
            return self.mP[0,1,1]
        else:
            return self.mP[1,1,0]
        self.update() 
    def set_P122_or_P221_value(self, value):
        if self.mP[1,0] <= 0.5:
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
        self.mW[1] = 1.0 - self.mW[0]
        
        self.mP[1,1] = 1.0 - self.mP[1,0]
        
        self.mW[1,0] = self.mW[1] * self.mP[1,0]
        self.mW[1,1] = self.mW[1] * self.mP[1,1]
        self.mW[0,1] = self.mW[1,0]
        self.mW[0,0] = self.mW[0] - self.mW[1,0]
        
        if self.mW[0] <= self.twothirds:
            self.mP[1,0,0] = self.mP[0,0,1] * self.mW[0,0] / self.mW[1,0]
        else:
            self.mP[0,0,1] = self.mP[1,0,0] * self.mW[1,0] / self.mW[0,0]
        self.mP[1,0,1] = 1.0 - self.mP[1,0,0]
        self.mP[0,0,0] = 1.0 - self.mP[0,0,1]            
            
        if self.mP[1,0] <= 0.5:
            self.mP[1,1,0] = self.mP[0,1,1] * self.mW[0,1] / self.mW[1,1]
        else:
            self.mP[0,1,1] = self.mP[1,1,0] * self.mW[1,1] / self.mW[0,1]
        self.mP[0,1,0] = 1.0 - self.mP[0,1,1]
        self.mP[1,1,1] = 1.0 - self.mP[1,1,0]
            
        self.solve()
        self.validate()
        self.updated.emit()
    
    pass #end of class
  
@storables.register()
class R2G3Model(_AbstractProbability):
	"""
	Reichweite = 2 / Components = 3
	independent variables = 6 -> restricted model!
	W0
	W1 / (W1 + W2) = G1
	P000 (0.5<W0<2/3) of P101 (2/3<W0<1)
    (W101+W102) / (W101+W102+W201+W202) = G2
    W101 / (W101+W102) = G3
    W201 / (W201+W202) = G4
    
	Restriction:
	- no 1 or 2 type layer can follow or precede another 1 or 2 type layer:
	P11 = P12 = 0
	P10 = 1
	P21 = P22 = 0
	P20 = 1
	
	P011 = P012 = 0
	P010 = 1
	P021 = P022 = 0
	P020 = 1
	P111 = P112 = 0
	P110 = 1
	P121 = P122 = 0
	P120 = 1
	P211 = P212 = 0
	P210 = 1
	P221 = P222 = 0
	P220 = 1
	
	Consequences:
	- weight fraction of a type X layer following or preceding a type 0 layer
	  equals the weight fraction of (single) X type layers:
	W10 = W01 = W1
	W20 = W02 = W2
	W00 = W0
	
	W1 = G1 * (1 - W0)
	W2 = 1 - W0 - W1
	
    If P000 given:
        P101 = (G2*G1 / W1) * [W00*(P000-1)+2]
        
    P102 = P101 * (1/G3 - 1)
    W101 = P101 * W10 = P101 * W1
    W102 = P102 * W1
    W100 = 1 - W101 - W102
    
    W201 + W202 = (1-G2) / (G2*G3) * W101
    W201 = G4 * (W201+W202)
    W202 = (1/G4 - 1) * W201
    W200 = 1 - W201 - W202
    
    W000 = W00 - W100 - W200
    W001 = W01 - W101 - W201
    W002 = 1 - W000 - W001
    
    Pxxx's are calculated from dividing Wxxx's with Wx's
	
	indexes are NOT zero-based in external property names!
	"""

    #MODEL INTEL:
    __independent_label_map__ = [
        ("W1", r"$W_1$"),   
        ("P111_or_P212", r"$P_{111} %s$ or $\newline P_{212} %s$" % (
            mt_range(0.5, "W_1", 2.0/3.0),
            mt_range(2.0/3.0, "W_1", 1.0))
        ),
        ("G1", r"$\large\frac{W_2}{W_3 + W_2}$"),
        ("G2", r"$\large\frac{W_{212} + W_{213}}{W_{212} + W_{213} + W_{312} + W_{313}}$"),
        ("G3", r"$\large\frac{W_{212}}{W_{212} + W_{213}}$"),
        ("G4", r"$\large\frac{W_{312}}{W_{312} + W_{313}}$"),


    ]
    __model_intel__ = [
        PropIntel(name=prop, label=label, minimum=0.0, maximum=1.0, data_type=float, refinable=True, storable=True, has_widget=True) \
            for prop, label in __independent_label_map__
    ]
    __store_id__ = "R2G3Model"

    #PROPERTIES:
    twothirds = 2.0/3.0
    
    _W0 = 0.75
    def get_W1_value(self): return self._W0
    def set_W1_value(self, value):
        self._W0 = min(max(value, 0.5), 1.0)
        self.update()
          
    def get_P111_or_P212_value(self):
        if self._W0 <= self.twothirds:
            return self.mP[0,0,0]
        else:
            return self.mP[1,0,1]
    def set_P111_or_P212_value(self, value):
        if self._W0 <= self.twothirds:
            self.mP[0,0,0] = value
        else:
            self.mP[1,0,1] = value
        self.update()
          
    _G1 = 0
    _G2 = 0
    _G3 = 0
    _G4 = 0
    @Model.getter("G[1234]")
    def get_G(self, prop_name):
        return getattr(self, "_%s"%prop_name)
    @Model.setter("G[1234]")
    def set_G(self, prop_name, value):
        setattr(self, "_%s"%prop_name, min(max(value, 0.0), 1.0))
        self.update()

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.75, P111_or_P212=0.5, G1=0.5, G2=0.5, G3=0.5, G4=0.5):
        _AbstractProbability.setup(self, R=2)
        self.W1 = W1
        self.P111_or_P212 = P111_or_P212
        self.G1 = G1
        self.G2 = G2
        self.G3 = G3
        self.G4 = G4   

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    
    def update(self):

        G2inv =  ( 1.0 / self._G2) - 1.0 if self._G2 > 0 else 0.0
        G3inv =  ( 1.0 / self._G3) - 1.0 if self._G3 > 0 else 0.0
        G4inv =  ( 1.0 / self._G4) - 1.0 if self._G4 > 0 else 0.0
           
        #calculate Wx's:
        W0 = self._W0
        W1 = (1.0 - W0) * self._G1
    	W2 = 1.0 - W0 - W1
        
        #consequences of restrictions:
        self.mW[1,0] = self.mW[0,1] = W1
        self.mW[2,0] = self.mW[0,2] = W2
        self.mW[0,0] = 2.0*W0 - 1.0
        
        #continue calculations:
    	if W0 < 0.5:
    	    self.mP[1,0,1] =  self._G2*self._G3*(self.mW[0,0]*(self.mP[0,0,0]-1.0)+2.0) / W1
        self.mP[1,0,2] = (self.mP[1,0,1] * ((1.0 / self._G3) - 1.0)) if self._G3 > 0 else 1.0
        #self.mP[0,0,0] = 1.0 - self.mP[1,0,1] - self.mP[1,0,2]
        
        self.mW[1,0,1] = self.mP[1,0,1] * W1
        self.mW[1,0,2] = self.mP[1,0,2] * W1
        self.mW[1,0,0] = self.mW[1,0] - self.mW[1,0,1] - self.mW[1,0,2]

        self.mW[2,0,1] = (self._G4 * (1.0 - self._G2) / (self._G2 * self._G3) * self.mW[1,0,1]) if (self._G2 * self._G3) > 0 else 0.0
        self.mW[2,0,2] = (self.mW[2,0,1] * ((1.0 / self._G4) - 1.0)) if self._G4 > 0 else 1.0
        self.mW[2,0,0] = self.mW[2,0] - self.mW[2,0,1] - self.mW[2,0,2]
        for i in range(3):
            self.mP[2,0,i] = self.mW[2,0,i] / self.mW[2,0] if self.mW[2,0] > 0 else 0.0
        
        self.mW[0,0,0] = self.mW[0,0] - self.mW[1,0,0] - self.mW[2,0,0]
        self.mW[0,0,1] = self.mW[0,1] - self.mW[1,0,1] - self.mW[2,0,1]
        self.mW[0,0,2] = self.mW[0,2] - self.mW[1,0,2] - self.mW[2,0,2]
        for i in range(3):
            self.mP[0,0,i] = self.mW[0,0,i] / self.mW[0,0] if self.mW[0,0] > 0 else 0.0
            pass

        #restrictions:            
        for i in range(3):
            for j in range(1,3):
                for k in range(3):
                    self.mP[i,j,k] = 0.0 if k > 0 else 1.0
            
        
        self.solve()
        self.validate()
        self.updated.emit()
    
    pass #end of class
