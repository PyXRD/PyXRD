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

class R1G2Model(_AbstractProbability):
	"""
	Reichweite = 1 / Components = 2
	g*(g-1) independent variables = 2
	W0 & P00 (W0<0,5) of P11 (W0>0,5)
	
	W1 = 1 – W0

    P00 given:                  or      P11 given:
	P01 = 1 - P00               or      P10 = 1 – P11
	P11 = (1 - P01*W0) / W1     or      P00 = (1 - P10*W1) / W0
	P10 = 1 - P11               or      P01 = 1 - P00
	
	indexes are NOT zero-based in external property names!
	"""

    #MODEL INTEL:
    __independent_label_map__ = [
        ("W1", r"$W_1$"),
        ("P11_or_P22", r"$P_{11} %s$ or $\newline P_{22} %s$" % (
            mt_range(0.0, "W_1", 0.5),
            mt_range(0.5, "W_1", 1.0))
        ),
    ]
    __model_intel__ = [
        PropIntel(name=prop, label=label, minimum=0.0, maximum=1.0, ctype=float, refinable=True, storable=True, has_widget=True) \
            for prop, label in __independent_label_map__
    ]

    #PROPERTIES:
    def get_W1_value(self): return self.mW[0]
    def set_W1_value(self, value):
        self.mW[0] = min(max(value, 0.0), 1.0)
        self.update()
                    
    def get_P11_or_P22_value(self):
        if self.mW[0] <= 0.5:
            return self.mP[0,0]
        else:
            return self.mP[1,1]
    def set_P11_or_P22_value(self, value):       
        if self.mW[0] <= 0.5:
            self.mP[0,0] = min(max(value, 0.0), 1.0)
        else:
            self.mP[1,1] = min(max(value, 0.0), 1.0)
        self.update()

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.25, P11_or_P22=0.5):
        _AbstractProbability.setup(self, R=1)
        self.W1 = W1
        self.P11_or_P22 = P11_or_P22

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    #@delayed()
    def update(self):
        self.mW[1] = 1.0 - self.mW[0]
        if self.mW[0] <= 0.5:
            self.mP[0,1] = 1.0 - self.mP[0,0]
            self.mP[1,0] = self.mW[0] * self.mP[0,1] / self.mW[1]
            self.mP[1,1] = 1.0 - self.mP[1,0]
        else:
            self.mP[1,0] = 1.0 - self.mP[1,1]
            self.mP[0,1] = self.mW[1] * self.mP[1,0] / self.mW[0]
            self.mP[0,0] = 1.0 - self.mP[0,1]
            
        self.solve()
        self.validate()
        self.updated.emit()
    
    pass #end of class
        
class R1G3Model(_AbstractProbability):
	"""
	Reichweite = 1 / Components = 3
	g*(g-1) independent variables = 6
    W0 & P00 (W0<0,5) of P11 (W0>0,5)
    W1/(W2+W1) = G1
    
    (W11+W12) / (W11+W12+W21+W22) = G2

    W11/(W11+W12) = G3
    W21/(W21+W22) = G4
		
	indexes are NOT zero-based in external property names!
	"""
	
    #MODEL INTEL:
    __independent_label_map__ = [
        ("W1", r"$W_1$"),
        ("P11_or_P22", r"$P_{11} %s$ or $\newline P_{22} %s$" % (
            mt_range(0.0, "W_1", 0.5),
            mt_range(0.5, "W_1", 1.0))
        ),
        ("G1", r"$\large\frac{W_2}{W_3 + W_2}$"),
        ("G2", r"$\large\frac{W_{22} + W_{23}}{W_{22} + W_{23} + W_{32} + W_{33}}$"),
        ("G3", r"$\large\frac{W_{22}}{W_{22} + W_{23}}$"),
        ("G4", r"$\large\frac{W_{32}}{W_{32} + W_{33}}$"),
    ]
    __model_intel__ = [
        PropIntel(name=prop, label=label, minimum=0.0, maximum=1.0, ctype=float, refinable=True, storable=True, has_widget=True) \
            for prop, label in __independent_label_map__
    ]

    #PROPERTIES
    _W0 = 0.0
    def get_W1_value(self): return self._W0
    def set_W1_value(self, value):
        self._W0 = min(max(value, 0.0), 1.0)
        self.update()
           
    _P00_P11 = 0.0
    def get_P11_or_P22_value(self): return self._P00_P11
    def set_P11_or_P22_value(self, value):
        self._P00_P11 = min(max(value, 0.0), 1.0)
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
    def setup(self, W1=0.6, P11_or_P22=0.3, G1=0.5, G2=0.4, G3=0.5, G4=0.2):
        _AbstractProbability.setup(self, R=1)
        self.W1 = W1
        self.P11_or_P22 = P11_or_P22
        self.G1 = G1
        self.G2 = G2
        self.G3 = G3
        self.G4 = G4                

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    #@delayed()
    def update(self):
        #temporary storage:
        #WW = np.matrix(np.zeros(shape=(3,3), dtype=float))
        
        G2inv =  ( 1.0 / self._G2) - 1.0 if self._G2 > 0.0 else 0.0
        G3inv =  ( 1.0 / self._G3) - 1.0 if self._G3 > 0.0 else 0.0
        G4inv =  ( 1.0 / self._G4) - 1.0 if self._G4 > 0.0 else 0.0
        
        #self.mW = diagonal with W1, W2, W3 etc.
        #WW = 3x3 with W11, W12, ... etc.
        self.mW[0] = self._W0
        self.mW[1] = (1-self.mW[0]) * self._G1
    	self.mW[2]   = 1.0 - self.mW[0] - self.mW[1]
    	
    	if self.mW[0] <= 0.5:
            self.mP[0,0] = self._P00_P11
    	    if self.mW[1] > 0.0:
        	    self.mP[1,1] = self._G2 * self._G3 * (self.mW[0]*(self.mP[0,0]-1.0) + self.mW[1] + self.mW[2]) / self.mW[1]
            else:
                self.mP[1,1] = 0.0
        else:
            self.mP[0,0] = 0.0
            self.mP[1,1] = self._P00_P11
    	
    	self.mW[1,1] = self.mP[1,1] * self.mW[1]
    	self.mW[1,2] = self.mW[1,1] * G3inv
    	self.mW[2,1] = self._G4 * G2inv * (self.mW[1,1] + self.mW[2,1])
    	self.mW[2,2] = G4inv * self.mW[2,1]
    	
    	self.mP[1,2] = (self.mW[1,2] / self.mW[1]) if self.mW[1] > 0.0 else 0.0
    	self.mP[1,0] = 1 - self.mP[1,1] - self.mP[1,2]
    	
    	self.mP[2,1] = (self.mW[2,1] / self.mW[2]) if self.mW[2] > 0.0 else 0.0
    	self.mP[2,2] = (self.mW[2,2] / self.mW[2]) if self.mW[2] > 0.0 else 0.0
    	self.mP[2,0] = 1 - self.mP[2,1] - self.mP[2,2]

    	self.mP[0,1] = ((self.mW[1] - self.mW[1,1] - self.mW[2,1]) / self.mW[0]) if self.mW[0] > 0.0 else 0.0
    	self.mP[0,2] = ((self.mW[2] - self.mW[1,2] - self.mW[2,2]) / self.mW[0]) if self.mW[0] > 0.0 else 0.0
    	
    	if self.mW[0] > 0.5:
        	self.mP[0,0] = 1 - self.mP[0,1] - self.mP[0,2]
    	
        
        for i in range(3):
            for j in range(3):
                self.mW[i,j] = self.mW[i,i] * self.mP[i,j]
                
        self.solve()
        self.validate()
        self.updated.emit()
    
    pass #end of class
        
class R1G4Model(_AbstractProbability):
	"""
	Reichweite = 1 / Components = 4
	g*(g-1) independent variables = 12
	
    W0
    W1/(W1+W2+W3) = R1
    W2/(W2+W3) = R2

    P00 (W0<0,5) of P11 (W0>0,5)
    (W11+W12+W13) / sum{i:1-3;j:1-3}(Wij) = G1
    (W21+W22+W23) / sum{i:2-3;j:1-3}(Wij) = G2
    
    W11 / (W11 + W12 + W13) = G11
    W12/(W12+W13) = G12
    
    W21 / (W21 + W22 + W23) = G21
    W22/(W22+W23) = G22
    
    W31 / (W31 + W32 + W33) = G31
    W32/(W32+W33) = G32
		
	indexes are NOT zero-based in external property names!
	"""
	
    #MODEL INTEL:
    __independent_label_map__ = [
        ("W1", r"$W_1$"),
        ("R1", r"$\large\frac{W_2}{W_2 + W_3 + W_4}$"),
        ("R2", r"$\large\frac{W_3}{W_3 + W_4}$"),
                        
        ("P11_or_P22", r"$P_{11} %s$ or $\newline P_{22} %s$" % (
            mt_range(0.0, "W_1", 0.5),
            mt_range(0.5, "W_1", 1.0))
        ),
        ("G1", r"$\large\frac{\sum_{j=2}^{4} W_{2j}}{\sum_{i=2}^{4} \sum_{j=2}^{4} W_{ij}}$"),
        ("G2", r"$\large\frac{\sum_{j=2}^{4} W_{3j}}{\sum_{i=3}^{4} \sum_{j=2}^{4} W_{ij}}$"),
        ("G11", r"$\large\frac{W_{22}}{\sum_{j=2}^{4} W_{2j}}$"),
        ("G12", r"$\large\frac{W_{23}}{\sum_{j=3}^{4} W_{2j}}$"),
        ("G21", r"$\large\frac{W_{32}}{\sum_{j=2}^{4} W_{3j}}$"),
        ("G22", r"$\large\frac{W_{33}}{\sum_{j=3}^{4} W_{3j}}$"),
        ("G31", r"$\large\frac{W_{42}}{\sum_{j=2}^{4} W_{4j}}$"),
        ("G32", r"$\large\frac{W_{43}}{\sum_{j=3}^{4} W_{4j}}$"),
    ]
    __model_intel__ = [
        PropIntel(name=prop, label=label, minimum=0.0, maximum=1.0, ctype=float, refinable=True, storable=True, has_widget=True) \
            for prop, label in __independent_label_map__
    ]

    #PROPERTIES
    def get_W1_value(self): return self.mW[0]
    def set_W1_value(self, value):
        self.mW[0] = min(max(value, 0.0), 1.0)
        self.update()
            
    def get_P11_or_P22_value(self):
        if self.mW[0] <= 0.5:
            return self.mP[0,0]
        else:
            return self.mP[1,1]
    def set_P11_or_P22_value(self, value):
        if self.mW[0] <= 0.5:
            self.mP[0,0] = min(max(value, 0.0), 1.0)
        else:
            self.mP[1,1] = min(max(value, 0.0), 1.0)
        self.update()

    _R1 = 0
    _R2 = 0
    _G1 = 0
    _G2 = 0
    _G11 = 0
    _G12 = 0
    _G21 = 0
    _G22 = 0
    _G31 = 0
    _G32 = 0
    @Model.getter("R[12]", "G[12]", "G[123][12]")
    def get_G1(self, prop_name):
        return getattr(self, "_%s"%prop_name)
    @Model.setter("R[12]", "G[12]", "G[123][12]")
    def set_G(self, prop_name, value):
        setattr(self, "_%s"%prop_name, min(max(value, 0), 1))
        self.update()

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------       
    def setup(self, W1=0.6, P11_or_P22=0.3, R1=0.5, R2=0.5, G1=0.5, G2=0.4,
            G11=0.5, G12=0.2, G21=0.8, G22=0.75, G31=0.7, G32=0.5):
        _AbstractProbability.setup(self, R=1)
        self.W1 = W1
        self.P11_or_P22 = P11_or_P22
        self.R1 = R1
        self.R2 = R2
        self.G1 = G1
        self.G2 = G2
        self.G11 = G11
        self.G12 = G12
        self.G21 = G21
        self.G22 = G22
        self.G31 = G31
        self.G32 = G32


    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    def update(self):
        #temporary storage:
        #WW = np.matrix(np.zeros(shape=(4,4), dtype=float))
        
        G1inv = ( 1.0 / self._G1) - 1.0 if self._G1 > 0 else 0.0
        
        G11inv = ( 1.0 / self._G11) - 1.0 if self._G11 > 0 else 0.0
        G21inv = ( 1.0 / self._G21) - 1.0 if self._G21 > 0 else 0.0
        G31inv = ( 1.0 / self._G31) - 1.0 if self._G31 > 0 else 0.0
        
        
        #self.mW = diagonal with W1, W2, W3 etc.
        #WW = 4x4 with W11, W12, ... etc.
             
        self.mW[1] = (1.0 - self.mW[0]) * self._R1
    	self.mW[2] = (1.0 - self.mW[0] - self.mW[1]) * self._R2
    	self.mW[3] = 1.0 - self.mW[0] - self.mW[1] - self.mW[2]

    	W0inv = 1.0 / self.mW[0] if self.mW[0] > 0.0 else 0.0    	    
    	W1inv = 1.0 / self.mW[1] if self.mW[1] > 0.0 else 0.0
    	W2inv = 1.0 / self.mW[1] if self.mW[1] > 0.0 else 0.0
    	W3inv = 1.0 / self.mW[1] if self.mW[1] > 0.0 else 0.0
    	    	
    	if self.mW[0] < 0.5: #P11 is given
        	self.mW[0,0] = self.mW[0] * self.P11_or_P22
        	if (self.mW[1] * self._G1) > 0.0:
        	    self.mP[1,1] = self._G1 * self._G2 * (self.mW[0,0] - 2*self.mW[0] + 1.0)
            else:
                self.mP[1,1] = 0.0
    	
    	self.mW[1,1] = self.mP[1,1] * self.mW[1]
    	self.mW[1,2] = self.mW[1,1] * G11inv * self._G12
    	self.mW[1,3] = self.mW[1,1] * G11inv * (1.0 - self._G12)
    	SBi = self.mW[1,1] + self.mW[1,2] + self.mW[1,3]
    	
    	SCi = G1inv * self._G2 * SBi
    	self.mW[2,1] = SCi * self._G21
    	self.mW[2,2] = (SCi - self.mW[2,1]) * self._G22
    	self.mW[2,3] = SCi - self.mW[2,1] - self.mW[2,2]
    	
    	SDi = G1inv * (1.0 - self._G2) * SBi
    	self.mW[3,1] = SDi * self._G31
    	self.mW[3,2] = (SDi - self.mW[3,1]) * self._G32
    	self.mW[3,3] = SDi - self.mW[3,1] - self.mW[3,2]    	
    	
    	self.mP[1,2] = self.mW[1,2] * W1inv
    	self.mP[1,3] = self.mW[1,3] * W1inv
    	self.mP[1,0] = 1 - self.mP[1,1] - self.mP[1,2] - self.mP[1,3]
    	
    	self.mP[2,1] = self.mW[2,1] * W2inv
    	self.mP[2,2] = self.mW[2,2] * W2inv
    	self.mP[2,3] = self.mW[2,3] * W2inv
    	self.mP[2,0] = 1 - self.mP[2,1] - self.mP[2,2] - self.mP[2,3]

    	self.mP[3,1] = self.mW[3,1] * W3inv
    	self.mP[3,2] = self.mW[3,2] * W3inv
    	self.mP[3,3] = self.mW[3,3] * W3inv
    	self.mP[3,0] = 1 - self.mP[3,1] - self.mP[3,2] - self.mP[3,3]

        print W0inv, self.mW[1] - self.mW[1,1] - self.mW[2,1] - self.mW[3,1]

    	self.mP[0,1] = (self.mW[1] - self.mW[1,1] - self.mW[2,1] - self.mW[3,1]) * W0inv
    	self.mP[0,2] = (self.mW[2] - self.mW[1,2] - self.mW[2,2] - self.mW[3,2]) * W0inv
    	self.mP[0,3] = (self.mW[3] - self.mW[1,3] - self.mW[2,3] - self.mW[3,3]) * W0inv
    	
    	if self.mW[0] >= 0.5:
        	self.mP[0,0] = 1 - self.mP[0,1] - self.mP[0,2] - self.mP[0,3]
        
        for i in range(4):
            for j in range(4):
                self.mW[i,j] = self.mW[i] * self.mP[i,j]
        
        self.solve()
        self.validate()
        self.updated.emit()
    
    pass #end of class
