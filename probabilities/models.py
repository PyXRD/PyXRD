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

from generic.io import Storable
from generic.models import ChildModel
from generic.utils import delayed, indexproperty


# Overview of what is:
#   x   = currently implemented
#   np  = not possible
#   -   = not yet implemented
#
#       G1  G2  G3  G4  G5  G6
#   R0  x   x   x   x   x   x
#   R1  np  x   x   -   -   -
#   R2  np  x   -   -   -   -
#   R3  np  np  -   -   -   -


def get_Gbounds_for_R(R):
    if R==0:
        return (1,6)
    elif R==1:
        return (2,3)
    elif R==2:
        return (2,2)
    else:
        raise ValueError, "Cannot yet handle R%d" % R

def get_Rbounds_for_G(G):
    if G==1:
        return (0,0)
    elif G==2:
        return (0,2)
    elif G==3:
        return (0,1)
    elif G>=4 and G<=6:
        return (0,0)
    else:
        raise ValueError, "Cannot yet handle G%d" % G

def get_correct_probability_model(phase):
    if phase!=None:
        G = phase.data_G
        R = phase.data_R
        #print "get_correct_probability_model %d %d" % (G, R)
        if R == 0 or G == 1:
            return R0Model(parent=phase)
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
                    raise ValueError, "Cannot yet handle R3 G2"
                elif G == 3:
                    raise ValueError, "Cannot yet handle R3 G3"
                elif G == 4:
                    raise ValueError, "Cannot yet handle R3 G4"
            else:
                raise ValueError, "Cannot (yet) handle Reichweite's other then 0, 1, 2 or 3"

class _AbstractProbability(ChildModel, Storable):

    #MODEL INTEL:
    __observables__ = ['updated']
    __storables__ = []
    __parent_alias__ = 'phase'
    
    #SIGNALS:
    updated = None
    
    #PROPERTIES:
    data_name = "Probabilities"
    
    _R = -1
    @property
    def R(self):
        return self._R

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
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        self.updated = Signal()
        self.setup(**kwargs)
        self.update()
    
    def setup(self, **kwargs):
        self._R = -1
        self._W = None
        self._P = None
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    def update(self):
        raise NotImplementedError
        
    def get_probability_matrix(self):
        raise NotImplementedError
        
    def get_distribution_matrix(self):
        raise NotImplementedError
        
    def get_independent_label_map(self):
        raise NotImplementedError
    
    pass #end of class
        
class _AbstractR0R1Model(_AbstractProbability):

    #MODEL INTEL:
    __independent_label_map__ = []

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    def get_probability_matrix(self):
        return np.array(np.matrix(self._P))
        
    def get_distribution_matrix(self):
        return np.array(np.matrix(np.diag(self._W)))
        
    def get_distribution_array(self):
        return self._W
        
    def get_independent_label_map(self):
        return self.__independent_label_map__
    
    pass #end of class

class R0Model(_AbstractR0R1Model):
    """
    Reichweite = 0
	(g-1) independent variables: W0, W1, ... W(g-2)

	Pij = Wj
	∑W = 1
	∑P = 1
	
	indexes are NOT zero-based in external property names!
	"""
	
    #MODEL INTEL:
    __independent_label_map__ = [
        ("W1", "W<sub>1</sub>"),
        ("W2", "W<sub>2</sub>"),
        ("W3", "W<sub>3</sub>"),
        ("W4", "W<sub>4</sub>"),
        ("W5", "W<sub>5</sub>"),
        ("W6", "W<sub>6</sub>"),
    ]
    @property
    def __refineables__(self):
        return [ "W%d" % (i+1) for i in range(self.G-1) ]
    __observables__ = [ prop for prop, lbl in  __independent_label_map__ ]
    __storables__ = [ val for val in __observables__ if not val in ('parent', "added", "removed")]

    #PROPERTIES:
    @Model.getter("W[1-6]")
    def get_W(self, prop_name):
        index = int(prop_name[1:])-1
        return self._W[index] if index < self.G else None
    @Model.setter("W[1-6]")
    def set_W(self, prop_name, value):
        index = int(prop_name[1:])-1
        self._W[index] = min(max(float(value), 0.0), 1.0)
        self.update()

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def setup(self, W1=1.0, W2=0.0, W3=0.0, W4=0.0, **kwargs):
        self._R = 0
        self._W = np.zeros(shape=(self.G), dtype=float)
        loc = locals()
        for i in range(self.G):
            self._W[i] = loc["W%d"%(i+1)]
            setattr(self, "W%d_range"%(i+1), [0, 1.0])
        self._P = np.repeat(self._W[np.newaxis,:], self.G, 0)

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    @delayed()
    def update(self):
        if self.G == 1:
            self._W[0] = 1.0
        elif self.G > 1:
            partial_sum = np.sum(self._W[:-1])
            self._W[-1] = max(1.0 - partial_sum, 0)
            if partial_sum > 1.0:
                self._W *= 1.0 / partial_sum
        self._P = np.repeat(self._W[np.newaxis,:], self.G, 0)
        self.updated.emit()
    
    def get_independent_label_map(self):
        return self.__independent_label_map__[:(self.G-1)]
    
    pass #end of class

class R1G2Model(_AbstractR0R1Model):
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
        ("W1", "W<sub>1</sub>"),
        ("P11_or_P22", "P<sub>11</sub> or P<sub>22</sub>"),
    ]
    __refineables__ = [ prop for prop, lbl in  __independent_label_map__ ]
    __observables__ = __refineables__
    __storables__ = [ val for val in __observables__ if not val in ('parent', "added", "removed")]

    #PROPERTIES:
    W1_range = [0,1.0]
    def get_W1_value(self): return self._W[0]
    def set_W1_value(self, value):
        self._W[0] = min(max(value, 0.0), 1.0)
        self.update()
                    
    P11_or_P22_range = [0,1.0]
    def get_P11_or_P22_value(self):
        if self._W[0] <= 0.5:
            return self._P[0,0]
        else:
            return self._P[1,1]
    def set_P11_or_P22_value(self, value):       
        if self._W[0] <= 0.5:
            self._P[0,0] = min(max(value, 0.0), 1.0)
        else:
            self._P[1,1] = min(max(value, 0.0), 1.0)
        self.update()

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.25, P11_or_P22=0.5):
        self._R = 1
        self._W = np.zeros(shape=(2), dtype=float)
        self._P = np.zeros(shape=(2, 2), dtype=float)
        self.W1 = W1
        self.P11_or_P22 = P11_or_P22

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    #@delayed()
    def update(self):
        #print "%s %s Case 1" % (self._P, self._W)
        self._W[1] = 1.0 - self._W[0]
        if self._W[0] <= 0.5:
            self._P[0,1] = 1.0 - self._P[0,0]
            self._P[1,0] = self._W[0] * self._P[0,1] / self._W[1]
            self._P[1,1] = 1.0 - self._P[1,0]
        else:
            self._P[1,0] = 1.0 - self._P[1,1]
            self._P[0,1] = self._W[1] * self._P[1,0] / self._W[0]
            self._P[0,0] = 1.0 - self._P[0,1]
        self.updated.emit()
    
    pass #end of class
        
class R1G3Model(_AbstractR0R1Model):
	"""
	Reichweite = 1 / Components = 3
	g*(g-1) independent variables = 6
	W0 & P00 (W0<0,5) of P11 (W0>0,5)
	W1/(W2+W1) = G1
	
	(W11+W12) / (W11+W12+W21+W22) = G2

	W11/(W11+W12) = G3
	W21/(W21+W22) = G4
	
	W1 = (1 – W0) * W1 / (W1+W2) = (1 – W0) * G1
	W2 = 1 – W0 – W1
	
	Als W0 < 0,5 (P00 gegeven):
		W00 = P00*W0
		
		W11 = (W0-W1-W2-W00) * G3 * G2
		P11 = W11 / W1
		
	Als W0 > 0,5 (P11 gegeven):
		W11 = P11*W1

	W12 = W11 * (1-G3)
	P12 = W12/W1 (= P11 * (1–G3))
	
	W10 = W1 – W12 – W11 (= W1 – W11/G3)
	P10 = W10/W1
	
	W21 = G4 * (1-G2)*(W11+W12)
	P21 = W21/W2

	W22 = (1 – G4) * W21
	P22 = W22/W2
	
	W20 = W2 – W21 - W22
	P20 = W20/W2
	
	P00 = 1 – P10 – P20
	P01 = 1 – P11 – P21
	P02 = 1 – P21 – P22
		
	indexes are NOT zero-based in external property names!
	"""
	
    #MODEL INTEL:
    __independent_label_map__ = [
        ("W1", "W<sub>1</sub>"),
        ("P11_or_P22", "P<sub>11</sub> or P<sub>22</sub>"),
        ("G1", "W<sub>2</sub> / (W<sub>3</sub> + W<sub>2</sub>)"),
        ("G2", "(W<sub>22</sub> + W<sub>23</sub>) / (W<sub>22</sub> + W<sub>23</sub> + W<sub>32</sub> + W<sub>33</sub>)"),
        ("G3", "W<sub>22</sub> / (W<sub>22</sub> + W<sub>23</sub>)"),
        ("G4", "W<sub>32</sub> / (W<sub>32</sub> + W<sub>33</sub>)"),
    ]
    __refineables__ = [ prop for prop, lbl in  __independent_label_map__ ]
    __observables__ = __refineables__
    __storables__ = [ val for val in __observables__ if not val in ('parent', "added", "removed")]

    #PROPERTIES
    W1_range = [0,1.0]
    def get_W1_value(self): return self._W[0]
    def set_W1_value(self, value):
        self._W[0] = min(max(value, 0.0), 1.0)
        self.update()
            
    P11_or_P22_range = [0,1.0]
    def get_P11_or_P22_value(self):
        if self._W[0] <= 0.5:
            return self._P[0,0]
        else:
            return self._P[1,1]
    def set_P11_or_P22_value(self, value):
        if self._W[0] <= 0.5:
            self._P[0,0] = min(max(value, 0.0), 1.0)
        else:
            self._P[1,1] = min(max(value, 0.0), 1.0)
        self.update()

    G1_range = [0,1.0]
    G2_range = [0,1.0]
    G3_range = [0,1.0]
    G4_range = [0,1.0]
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
    def setup(self, W1=0.25, P11_or_P22=0.5):
        self._R = 0
        self._W = np.zeros(shape=(3), dtype=float)
        self._P = np.zeros(shape=(3, 3), dtype=float)
        self.W1 = W1
        self.P11_or_P22 = P11_or_P22

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    @delayed()    
    def update(self):    
        #temporary storage:
        WW = np.matrix(np.zeros(shape=(3,3), dtype=float))
             
        self._W[1]   = (1.0 - self._W[0]) * self._G1
    	self._W[2]   = 1.0 - self._W[0] - self._W[1]
	
	    if self._W[0] <= 0.5:
	        WW[0,0]         = self._P[0,0]*self._W[0]
	        
	        WW[1,1]         = (self._W[0] - self._W[1] - self._W[2] - WW[0,0]) * self._G3 * self._G2
	        self._P[1,1]    = WW[1,1] / self._W[1]
	    else:
	        WW[1,1]         = self._P[1,1]*self._W[1]
	        
        WW[1,2]         = WW[1,1] * (1.0-self._G3)
        self._P[1,2]    = WW[1,2] / self._W[1]

        WW[1,0]         = self._W[1] - WW[1,2] - WW[1,1]
        self._P[1,0]    = WW[1,0] / self._W[1]        
		
		WW[2,1]         = self._G4 * (1.0 - self._G2) * (WW[1,1] + WW[1,2])
		self._P[2,1]    = WW[2,1] / self._W[2]

		WW[2,2]         = (1.0 - self._G4) * WW[2,1]
		self._P[2,2]    = WW[2,2]/self._W[2]
		
		WW[2,0]         = self._W[2] - WW[2,1] - WW[2,2]
		self._P[2,0]    = WW[2,0]/self._W[2]
		
		self._P[0,0]    = 1.0 - self._P[1,0] - self._P[2,0]
		self._P[0,1]    = 1.0 - self._P[1,1] - self._P[2,1]
		self._P[0,2]    = 1.0 - self._P[2,1] - self._P[2,2]
    
        self.updated.emit()
    
    pass #end of class
        
        
class R2G2Model(_AbstractR0R1Model): #TODO new abstract class needed?
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
        ("W1", "W<sub>1</sub>"),
        ("P112_or_P211", "P<sub>112</sub> or P<sub>211</sub>"),
        ("P21", "P<sub>21</sub>"),
        ("P122_or_P221", "P<sub>122</sub> or P<sub>221</sub>"),
    ]
    __refineables__ = [ prop for prop, lbl in  __independent_label_map__ ]
    __observables__ = __refineables__
    __storables__ = [ val for val in __observables__ if not val in ('parent', "added", "removed")]

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
        self._R = 2
        self._W = np.zeros(shape=(self.G**2, self.G**2), dtype=float)
        self._P = np.zeros(shape=(self.G**2, self.G**2), dtype=float)
        self.W1 = W1
        self.P112_or_P211 = P112_or_P211
        self.P21 = P21
        self.P122_or_P221

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    
    @indexproperty
    def mP(self, indeces):
        i, j, k = indeces
        return self._P[self.G * i + j, self.G * j + k]
    @mP.setter
    def mP(self, indeces, value):
        i, j, k = indeces    
        self._P[self.G * i + j, self.G * j + k] = min(max(value, 0.0), 1.0)
    
    @indexproperty
    def mW(self, indeces):
        i, j = indeces
        return self._W[self.G * i + j, self.G * i + j]
    @mW.setter
    def mW(self, indeces, value):
        i, j = indeces
        self._W[self.G * i + j, self.G * i + j] = min(max(value, 0.0), 1.0)
    
    def get_distribution_matrix(self): return self._W
        
    def get_distribution_array(self): return np.diag(self._W)
    
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
