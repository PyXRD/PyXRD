# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os
import warnings

from gtkmvc.model import Model, Observer, Signal

import numpy as np

from generic.mathtext_support import mt_range
from generic.io import Storable
from generic.models import ChildModel, PropIntel
from generic.utils import delayed, indexproperty


# Overview of what is:
#   x   = currently implemented
#   np  = not possible
#   -/o = not yet implemented
#   o   = priority
#
#       G1  G2  G3  G4  G5  G6
#   R0  x   x   x   x   x   x
#   R1  np  x   x   o   -   -
#   R2  np  x   x   -   -   -
#   R3  np  o   o   -   -   -


def get_Gbounds_for_R(R, G):
    low, upp = 1,6
    if R==0:
        low, upp = 1,6
    elif R==1:
        low, upp = 2,3
    elif R==2:
        low, upp = 2,3
    else:
        raise ValueError, "Cannot yet handle R%d" % R
    return (low, upp, max(min(G, upp), low))

def get_Rbounds_for_G(G, R):
    low, upp = 0,0
    if G==1:
        low, upp = 0,0
    elif G==2:
        low, upp = 0,3
    elif G==3:
        low, upp = 0,1
    elif G>=4 and G<=6:
        low, upp = 0,0
    else:
        raise ValueError, "Cannot yet handle G%d" % G
    return (low, upp, max(min(R, upp), low))

def get_correct_probability_model(phase):
    if phase!=None:
        G = phase.data_G
        R = phase.data_R
        if R == 0 or G == 1:
            if G == 1:
                return R0G1Model(parent=phase)
            elif G == 2:
                return R0G2Model(parent=phase)
            elif G == 3:
                return R0G3Model(parent=phase)
            elif G == 4:
                return R0G4Model(parent=phase)
            elif G == 5:
                return R0G5Model(parent=phase)
            elif G == 6:
                return R0G6Model(parent=phase)
        elif G > 1:
            if R == 1: #------------------------- R1:
                if G == 2:
                    return R1G2Model(parent=phase)
                elif G == 3:
                    return R1G3Model(parent=phase)
                elif G == 4:
                    raise ValueError, "Cannot yet handle R1 G4"
            elif R == 2: #----------------------- R2:
                if G == 2:
                    return R2G2Model(parent=phase)
                elif G == 3:
                    raise ValueError, "Cannot yet handle R2 G3"
                elif G == 4:
                    raise ValueError, "Cannot yet handle R2 G4"            
            elif R == 3: #----------------------- R3:
                if G == 2:
                    return R3G2Model(parent=phase)
                elif G == 3:
                    raise ValueError, "Cannot yet handle R3 G3"
                elif G == 4:
                    raise ValueError, "Cannot yet handle R3 G4"
            else:
                raise ValueError, "Cannot (yet) handle Reichweite's other then 0, 1, 2 or 3"

class _AbstractProbability(ChildModel, Storable):

    #MODEL INTEL:     
    __parent_alias__ = 'phase'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="updated",   inh_name=None,  label="",             minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False,  observable=True,  has_widget=False),
        PropIntel(name="data_name", inh_name=None,  label="Probabilites", minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=False,  observable=True,  has_widget=False),
    ]
    __independent_label_map__ = []
    
    #SIGNALS:
    updated = None
    
    #PROPERTIES:
    data_name = "Probabilities"
    
    _R = -1
    @property
    def R(self):
        return self._R

    @property
    def rank(self):
        return self.G ** max(self.R, 1)

    @property
    def G(self):
        if self.parent!=None:
            return self.parent.data_G
        else:
            return None
    
    _W = None
    _P = None
    @property
    def parameters(self):
        return self._parameters
    
    @indexproperty
    def mP(self, indeces):
        return self._P[self._get_Pxy_from_indeces(indeces)]
    @mP.setter
    def mP(self, indeces, value):
        self._P[self._get_Pxy_from_indeces(indeces)] = min(max(value, 0.0), 1.0)
    
    @indexproperty
    def mW(self, indeces):
        return self._W[self._get_Wxy_from_indeces(indeces)]
    @mW.setter
    def mW(self, indeces, value):
        self._W[self._get_Wxy_from_indeces(indeces)] = min(max(value, 0.0), 1.0)    
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        self.updated = Signal()
        self.setup(**kwargs)
        self.update()
    
    def setup(self, R=-1):
        self._R = R
        self._create_matrices()
    
    def _create_matrices(self):
        self._W = np.zeros(shape=(self.rank, self.rank), dtype=float)
        self._P = np.zeros(shape=(self.rank, self.rank), dtype=float)
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update(self):
        raise NotImplementedError
        
    def _get_Pxy_from_indeces(self, indeces):
        assert(len(indeces)==(self.R+1))
        x, y = 0, 0
        for i in range(1,self.R+1):
            f = self.G ** (self.R-i)
            x += indeces[i-1] * f
            y += indeces[i] * f
        return x, y
    def _get_Wxy_from_indeces(self, indeces):
        assert(len(indeces)==self.R)
        x, y = 0, 0
        for i in range(0,self.R):
            x += indeces[i] * self.G ** (self.R-(i+1))
        return x, x
    
    def get_distribution_matrix(self): return self._W
        
    def get_distribution_array(self): return np.diag(self._W)

    def get_probability_matrix(self): return self._P
        
    def get_independent_label_map(self): return self.__independent_label_map__
    
    pass #end of class


def R0_model_generator(pasG):
             
    class R0Model(_AbstractProbability):
        """
        Reichweite = 0
	    (g-1) independent variables:
	    
	    W0 = W0/sum(W0>Wg)
	    W1/sum(W1>Wg)
	    W2/sum(W2>Wg)
	    etc.
	    

	    Pij = Wj
	    ∑W = 1
	    ∑P = 1
	
	    indexes are NOT zero-based in external property names!
	    """
	    
        #MODEL INTEL:
        __independent_label_map__ = [
            (
                "F%d" % (g+1),
                r"$\large\frac{W_{%(g)d}}{\sum_{i=%(g)d}^{%(G)d} W_i}$" % {'g':g+1, 'G':pasG }
            ) for g in range(pasG-1)
        ]
        __model_intel__ = [
            PropIntel(name=prop, inh_name=None, label=label, minimum=0.0, maximum=1.0, is_column=False, ctype=float, refinable=True, storable=True, observable=True, has_widget=True) \
                for prop, label in __independent_label_map__
        ]

        @property
        def G(self):
            return pasG

        #PROPERTIES:
        @Model.getter("F[1-%d]" % (pasG+1))
        def get_W(self, prop_name):
            index = int(prop_name[1:])-1
            return self._F[index] if index < self.G else None
        @Model.setter("F[1-%d]" % (pasG+1))
        def set_W(self, prop_name, value):
            index = int(prop_name[1:])-1
            self._F[index] = min(max(float(value), 0.0), 1.0)
            self.update()

        # ------------------------------------------------------------
        #      Initialisation and other internals
        # ------------------------------------------------------------
        def setup(self, **kwargs):
            _AbstractProbability.setup(self, R=0)
            self._F = np.zeros(shape=(self.G-1), dtype=float)
            
            if self.G > 1 and "W1" in kwargs: #old-style model
                for i in range(self.G-1):
                    self._W[i] = kwargs.get("W%d"%(i+1), 0.0 if i > 0 else 1.0)
                self._W[-1,-1] = 1 - np.sum(np.diag(self._W)[:-1])
                for i in range(self.G-1):
                    self._F[i] = self._W[i,i] / (np.sum(np.diag(self._W)[i:]) or 1.0)
            else:
                for i in range(self.G-1):
                    self._F[i] = kwargs.get("F%d"%(i+1), 0.0 if i > 0 else 1.0)
                if self.G > 1:
                    for i in range(self.G-1):
                        if i > 0:
                            self._W[i,i] = self._F[i] * (1 - np.sum(np.diag(self._W)[0:i]))
                        else:
                            self._W[i,i] = self._F[i]
                    self._W[-1,-1] = 1 - np.sum(np.diag(self._W)[:-1])
                else:
                    self._W[0,0] = 1.0
            self._P = np.repeat(np.diag(self._W)[np.newaxis,:], self.G, 0)

        # ------------------------------------------------------------
        #      Methods & Functions
        # ------------------------------------------------------------ 
        #@delayed()
        def update(self):
            if self.G > 1:
                self._W[0,0] = self._F[0]
                for i in range(1, self.G-1):
                    self._W[i,i] = self._F[i] * (1.0 - np.sum(np.diag(self._W)[0:i]))
                self._W[-1,-1] = 1.0 - np.sum(np.diag(self._W)[:-1])
            else:
                self._W[0,0] = 1.0
            self._P = np.repeat(np.diag(self._W)[np.newaxis,:], self.G, 0)
            self.updated.emit()
        
        #def get_independent_label_map(self):
        #    return self.__independent_label_map__[:(self.G-1)]
        
        pass #end of class
    return type("R0G%dModel" % pasG, (R0Model,), dict())

R0G1Model = R0_model_generator(1)
R0G2Model = R0_model_generator(2)
R0G3Model = R0_model_generator(3)
R0G4Model = R0_model_generator(4)
R0G5Model = R0_model_generator(5)
R0G6Model = R0_model_generator(6)

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
        PropIntel(name=prop, inh_name=None, label=label, minimum=0.0, maximum=1.0, is_column=False, ctype=float, refinable=True, storable=True, observable=True, has_widget=True) \
            for prop, label in __independent_label_map__
    ]

    #PROPERTIES:
    def get_W1_value(self): return self._W[0,0]
    def set_W1_value(self, value):
        self._W[0,0] = min(max(value, 0.0), 1.0)
        self.update()
                    
    def get_P11_or_P22_value(self):
        if self._W[0,0] <= 0.5:
            return self._P[0,0]
        else:
            return self._P[1,1]
    def set_P11_or_P22_value(self, value):       
        if self._W[0,0] <= 0.5:
            self._P[0,0] = min(max(value, 0.0), 1.0)
        else:
            self._P[1,1] = min(max(value, 0.0), 1.0)
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
        self._W[1,1] = 1.0 - self._W[0,0]
        if self._W[0,0] <= 0.5:
            self._P[0,1] = 1.0 - self._P[0,0]
            self._P[1,0] = self._W[0,0] * self._P[0,1] / self._W[1,1]
            self._P[1,1] = 1.0 - self._P[1,0]
        else:
            self._P[1,0] = 1.0 - self._P[1,1]
            self._P[0,1] = self._W[1,1] * self._P[1,0] / self._W[0,0]
            self._P[0,0] = 1.0 - self._P[0,1]
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
        PropIntel(name=prop, inh_name=None, label=label, minimum=0.0, maximum=1.0, is_column=False, ctype=float, refinable=True, storable=True, observable=True, has_widget=True) \
            for prop, label in __independent_label_map__
    ]

    #PROPERTIES
    def get_W1_value(self): return self._W[0,0]
    def set_W1_value(self, value):
        self._W[0,0] = min(max(value, 0.0), 1.0)
        self.update()
            
    def get_P11_or_P22_value(self):
        if self._W[0,0] <= 0.5:
            return self._P[0,0]
        else:
            return self._P[1,1]
    def set_P11_or_P22_value(self, value):
        if self._W[0,0] <= 0.5:
            self._P[0,0] = min(max(value, 0.0), 1.0)
        else:
            self._P[1,1] = min(max(value, 0.0), 1.0)
        self.update()

    _G1 = 0
    _G2 = 0
    _G3 = 0
    _G4 = 0
    @Model.getter("G[1234]")
    def get_G1(self, prop_name):
        return getattr(self, "_%s"%prop_name)
    @Model.setter("G[1234]")
    def set_G(self, prop_name, value):
        setattr(self, "_%s"%prop_name, min(max(value, 0), 1))
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
        WW = np.matrix(np.zeros(shape=(3,3), dtype=float))
        
        G2inv =  ( 1.0 / self._G2) - 1.0 if self._G2 > 0 else 0.0
        G3inv =  ( 1.0 / self._G3) - 1.0 if self._G3 > 0 else 0.0
        G4inv =  ( 1.0 / self._G4) - 1.0 if self._G4 > 0 else 0.0
        
             
        self._W[1,1] = (1-self._W[0,0]) * self._G1
    	self._W[2,2]   = 1.0 - self._W[0,0] - self._W[1,1]
    	
    	if self._W[0,0] < 0.5:
    	    self._P[1,1] =  self._G2 * self._G3 * (self._W[0,0]*(self._P[0,0]-1) + self._W[1,1] + self._W[2,2]) / self._W[1,1]
    	
    	WW[1,1] = self._P[1,1] * self._W[1,1]
    	WW[1,2] = WW[1,1] * G3inv
    	WW[2,1] = self._G4 * G2inv * (WW[1,1] + WW[2,1])
    	WW[2,2] = G4inv * WW[2,1]
    	
    	self._P[1,2] = WW[1,2] / self._W[1,1]
    	self._P[1,0] = 1 - self._P[1,1] - self._P[1,2]
    	
    	self._P[2,1] = WW[2,1] / self._W[2,2]
    	self._P[2,2] = WW[2,2] / self._W[2,2]
    	self._P[2,0] = 1 - self._P[2,1] - self._P[2,2]

    	self._P[0,1] = (self._W[1,1] - WW[1,1] - WW[2,1]) / self._W[0,0]
    	self._P[0,2] = (self._W[2,2] - WW[1,2] - WW[2,2]) / self._W[0,0]
    	if self._W[0,0] >= 0.5:
        	self._P[0,0] = 1 - self._P[0,1] - self._P[0,2]
        
        for i in range(3):
            for j in range(3):
                WW[i,j] = self._W[i,i] * self._P[i,j]
                
        self.updated.emit()
    
    pass #end of class
        
        
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
            
        self.updated.emit()
    
    pass #end of class
    
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
    __independent_label_map__ = [
        ("W1", r"$W_1$"),
        ("P1111_or_P2112", r"$P_{1111} %s$ or $\newline P_{2112} %s$" % (
            mt_range(2.0/3.0, "W_1", 3.0/4.0),
            mt_range(3.0/4.0, "W_1", 1.0))
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
        
        self.updated.emit()
    
    pass #end of class
