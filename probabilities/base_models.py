# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import numpy as np

from gtkmvc.model import Signal

from generic.io import Storable
from generic.models import ChildModel, PropIntel
from generic.utils import indexproperty

from mixture.refinement import RefinementGroup

class _AbstractProbability(ChildModel, Storable, RefinementGroup):

    #MODEL INTEL:     
    __parent_alias__ = 'phase'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="updated",   inh_name=None,  label="",               minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False,  observable=True,  has_widget=False),
        PropIntel(name="data_name", inh_name=None,  label="Probabilites",   minimum=None,  maximum=None,  is_column=False, ctype=str,    refinable=False, storable=False,  observable=True,  has_widget=False),
        PropIntel(name="W_valid",   inh_name=None,  label="Valid W matrix", minimum=None,  maximum=None,  is_column=False, ctype=bool,   refinable=False, storable=False,  observable=True,  has_widget=False),
        PropIntel(name="P_valid",   inh_name=None,  label="Valid P matrix", minimum=None,  maximum=None,  is_column=False, ctype=bool,   refinable=False, storable=False,  observable=True,  has_widget=False),
    ]
    __independent_label_map__ = []
    
    #SIGNALS:
    updated = None
    
    #PROPERTIES:
    data_name = "Probabilities"
    W_valid = False
    W_valid_mask = None
    P_valid = False
    P_valid_mask = None
    
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
    
    #REFINEMENT GROUP IMPLEMENTATION:
    @property
    def refine_title(self):
        return self.data_name
    
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
        
    def validate(self):   
        self.W_valid_mask = np.ones_like(self._W)
        self.P_valid_mask = np.ones_like(self._P)
        
        if np.sum(self._W) != 1.0:
            for i in range(self.rank):
                self.W_valid_mask[i,i] -= 1
        
        for i in range(self.rank):
            if np.sum(self._P[i]) != 1.0:
                self.P_valid_mask[i] -= 1
        
        for i in range(self.rank):
            for j in range(self.rank):
                if self._W[i,j] < 0.0 or self._W[i,j] > 1.0:
                    self.W_valid_mask[i,i] -= 1
                if self._P[i,j] < 0.0 or self._P[i,j] > 1.0:
                    self.P_valid_mask[i,j] -= 1
        
        self.W_valid = (np.sum(self.W_valid_mask) == self.rank**2)
        self.P_valid = (np.sum(self.P_valid_mask) == self.rank**2)
    
        
    def _get_Pxy_from_indeces(self, indeces, R=None):
        if not hasattr(indeces, "__iter__"):
            indeces = [indeces]
        R = R or self.R
        assert(len(indeces)==(R+1))
        x, y = 0, 0
        for i in range(1,R+1):
            f = self.G ** (R-i)
            x += indeces[i-1] * f
            y += indeces[i] * f
        return x, y
    def _get_Wxy_from_indeces(self, indeces, R=None):
        if not hasattr(indeces, "__iter__"):
            indeces = [indeces]
        R = R or self.R
        assert(len(indeces)==max(R, 1))
        x, y = 0, 0
        for i in range(0,R):
            x += indeces[i] * self.G ** (R-(i+1))
        return x, x
        
    #TODO calculate & store lower-R W and P matrixes from high-R W and P matrices
    #needs a more generic index attribute for mP and mW, requires some code refactoring
    """def calculate_W_matrix(self, R):
        assert(R<self.R)
        w_rank = self.G ** max(R, 1)
        W = np.zeros(shape=(w_rank, w_rank), dtype=float)
        for j in range(self.G):
            for i in range(self.G):
        
        pass
        
    def calculate_P_matrix(self, R):
        assert(R<self.R)
        pass"""
    
    def get_distribution_matrix(self): return self._W
        
    def get_distribution_array(self): return np.diag(self._W)

    def get_probability_matrix(self): return self._P
        
    def get_independent_label_map(self): return self.__independent_label_map__
    
    pass #end of class
