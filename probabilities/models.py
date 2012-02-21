# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import warnings

from gtkmvc.model import Model, Observer

import numpy as np

from generic.io import Storable
from generic.models import ChildModel

def get_correct_probability_model(phase):
    if phase!=None:
        G = phase.data_G
        R = phase.data_R
        if R == 0 or G == 1:
            return R0Model(parent=phase)
        elif G > 1:
            if R == 1: #------------------------- R1:
                if G == 2:
                    return R1G2Model(parent=phase)
                elif G == 3:
                    raise R1G3Model(parent=phase)
                elif G == 4:
                    raise ValueError, "Cannot yet handle R1 G4"
            elif R == 2: #----------------------- R2:
                if G == 2:
                    raise ValueError, "Cannot yet handle R2 G2"
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

    __storables__ = []

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
    
    def __init__(self, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        self.setup(**kwargs)
        self.update()
    
    def setup(self, **kwargs):
        self._R = -1
        self._W = None
        self._P = None
    
    def update(self):
        raise NotImplementedError        
        
    def get_probability_matrix(self):
        raise NotImplementedError
        
    def get_distribution_matrix(self):
        raise NotImplementedError
        
    def get_independent_label_map(self):
        raise NotImplementedError
        
        
class _AbstractR0R1Model(_AbstractProbability):

    __independent_label_map__ = []
    __observables__ = [ prop for prop, lbl in  __independent_label_map__ ]

    def get_probability_matrix(self):
        self.update()
        return np.array(np.matrix(self._P))
        
    def get_distribution_matrix(self):
        self.update()
        return np.array(np.matrix(np.diag(self._W)))
        
    def get_distribution_array(self):
        self.update()
        return self._W
        
    def get_independent_label_map(self):
        return self.__independent_label_map__
        
class R0Model(_AbstractR0R1Model):

    """
	(g-1) independent variables: W0, W1, ... W(g-2)

	Pij = Wj
	∑W = 1
	∑P = 1
	
	indexes are not zero-based in external property names!
	"""
    __independent_label_map__ = [
        ("W1", "W1"),
        ("W2", "W2"),
        ("W3", "W3"),
        ("W4", "W4"),
    ]
    __observables__ = [ prop for prop, lbl in  __independent_label_map__ ]
    __storables__ = [ val for val in __observables__ if not val in ('parent')]

    @Model.getter("W[1-4]")
    def get_W(self, prop_name):
        index = int(prop_name[1:])-1
        return self._W[index] if index < self.G else None
    @Model.setter("W[1-4]")
    def set_W(self, prop_name, value):
        index = int(prop_name[1:])-1
        self._W[index] = min(max(float(value), 0.0), 1.0)
        self.update()

    def setup(self, W1=None, W2=None, W3=None, W4=None, **kwargs):
        self._R = 0
        self._W = np.zeros(shape=(self.G), dtype=float)
        loc = locals()
        for i in range(self.G):
            self._W[i] = loc["W%d"%(i+1)]

    def update(self):
        if self.G == 1:
            self._W[0] = 1.0
        elif self.G > 1:
            partial_sum = np.sum(self._W[:-1])
            self._W[-1] = max(1.0 - partial_sum, 0)
            if partial_sum > 1.0:
                self._W *= 1.0 / partial_sum
        self._P = np.repeat(self._W[np.newaxis,:], self.G, 0)
        pass
    
class R1G2Model(_AbstractR0R1Model):

	"""
	g*(g-1) independent variables = 2
	W0 & P00 (W0<0,5) of P11 (W0>0,5)
	
	W1 = 1 – W0

    P00 given:                  or      P11 given:
	P01 = 1 - P00               or      P10 = 1 – P11
	P11 = (1 - P01*W0) / W1     or      P00 = (1 - P10*W1) / W0
	P10 = 1 - P11               or      P01 = 1 - P00
	
	indexes are not zero-based in external property names!
	"""

    __independent_label_map__ = [
        ("W1", "W1"),
        ("P11_or_P22", "P11 or P22"),
    ]

    @Model.getter("W1")
    def get_W(self, prop_name):
        return self._W[0]
    @Model.setter("W1")
    def set_W(self, prop_name, value):
        self._W[0] = min(max(value, 0), 1)
        self.update()
            
    @Model.getter("P11_or_P22")
    def get_P(self, prop_name):
        index = int(prop_name[1:])
        return self._P[index]
    @Model.setter("P11_or_P22") 
    def set_P(self, prop_name, value):
        if self._W[0] >= 0.5:
            self._P[0,0] = min(max(value, 0), 1)
        else:
            self._P[1,1] = min(max(value, 0), 1)
        self.update()

    def setup(self):
        self._R = 0
        self._W = np.zeros(shape=(2), dtype=float)
        self._P = np.matrix(np.zeros(shape=(2, 2), dtype=float))
        self.__observables__ += [ "W1", "P11_or_P22" ]

    def update(self):           
        self._W[1] = 1 - self.W[0]
        if self._W[1] <= 0.5:
            self._P[0,1] = 1 - self._P[0,0]
            self._P[1,1] = (1 - self._P[0,1]*self._W[0]) / self._W[1]
            self._P[1,0] = 1 - self._P[1,1]
        else:
            self._P[1,0] = 1 - self._P[1,1]
            self._P[0,0] = (1 - self._P[1,0]*self._W[1]) / self._W[0]
            self._P[0,1] = 1 - self._P[0,0]
        
class R1G3Model(_AbstractR0R1Model):

	"""
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
		
	indexes are not zero-based in external property names!
	"""

    __independent_label_map__ = [
        ("W1", "W1"),
        ("P11_or_P22", "P11 or P22"),
        ("G1", "W1 / (W2 + W1)"),
        ("G2", "(W11 + W12) / (W11 + W12 + W21 + W22)"),
        ("G3", "W11 / (W11 + W12)"),
        ("G4", "W21 / (W21 + W22)"),
    ]

    @Model.getter("W1")
    def get_W(self, prop_name):
        return self._W[0]
    @Model.setter("W1")
    def set_W(self, prop_name, value):
        self._W[0] = min(max(value, 0), 1)
        self.update()
            
    @Model.getter("P11_or_P22")
    def get_P(self, prop_name):
        index = int(prop_name[1:])
        return self._P[index]
    @Model.setter("P11_or_P22")
    def set_P(self, prop_name, value):
        if self._W[1] >= 0.5:
            self._P[0,0] = min(max(value, 0), 1)
        else:
            self._P[1,1] = min(max(value, 0), 1)
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

    def setup(self):
        self._R = 0
        self._W = np.zeros(shape=(3), dtype=float)
        self._P = np.matrix(np.zeros(shape=(3, 3), dtype=float))
        self.__observables__ += [ "W1", "P11_or_P22", "G1", "G2", "G3", "G4"]

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
		
		WW[2,1]         = self._G4 * (1.0 - self._G2) * (W[1,1] + W[1,2])
		self._P[2,1]    = WW[2,1] / self._W[2]

		WW[2,2]         = (1.0 - self._G4) * WW[2,1]
		self._P[2,2]    = WW[2,2]/self._W[2]
		
		WW[2,0]         = self._W[2] - self._W[2,1] - self._W[2,2]
		self._P[2,0]    = WW[2,0]/self._W[2]
		
		self._P[0,0]    = 1.0 - self._P[1,0] - self._P[2,0]
		self._P[0,1]    = 1.0 - self._P[1,1] - self._P[2,1]
		self._P[0,2]    = 1.0 - self._P[2,1] - self._P[2,2]
        
        
