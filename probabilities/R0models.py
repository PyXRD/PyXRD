# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import numpy as np
from gtkmvc.model import Model

from generic.models import PropIntel
from probabilities.base_models import _AbstractProbability

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
            PropIntel(name=prop, label=label, minimum=0.0, maximum=1.0, data_type=float, refinable=True, storable=True, has_widget=True) \
                for prop, label in __independent_label_map__
        ]
        __store_id__ = "R0G%dModel" % pasG

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
                    self.mW[i] = kwargs.get("W%d"%(i+1), 0.0 if i > 0 else 1.0)
                self.mW[self.G-1] = 1 - np.sum(np.diag(self._W)[:-1])
                for i in range(self.G-1):
                    self._F[i] = self.mW[i] / (np.sum(np.diag(self._W)[i:]) or 1.0)
            else:
                for i in range(self.G-1):
                    self._F[i] = kwargs.get("F%d"%(i+1), 0.0 if i > 0 else 1.0)
                if self.G > 1:
                    for i in range(self.G-1):
                        if i > 0:
                            self.mW[i] = self._F[i] * (1 - np.sum(np.diag(self._W)[0:i]))
                        else:
                            self.mW[i] = self._F[i]
                    self.mW[self.G-1] = 1 - np.sum(np.diag(self._W)[:-1])
                else:
                    self.mW[0] = 1.0
            self._P[:] = np.repeat(np.diag(self._W)[np.newaxis,:], self.G, 0)

        # ------------------------------------------------------------
        #      Methods & Functions
        # ------------------------------------------------------------ 
        #@delayed()
        def update(self):
            if self.G > 1:
                self.mW[0] = self._F[0]
                for i in range(1, self.G-1):
                    self.mW[i] = self._F[i] * (1.0 - np.sum(np.diag(self._W)[0:i]))
                self.mW[self.G-1] = 1.0 - np.sum(np.diag(self._W)[:-1])
            else:
                self.mW[0] = 1.0
            self._P[:] = np.repeat(np.diag(self._W)[np.newaxis,:], self.G, 0)
            
            self.solve()
            self.validate() 
            self.updated.emit()
        
        #def get_independent_label_map(self):
        #    return self.__independent_label_map__[:(self.G-1)]
        
        pass #end of class
    cls = type("R0G%dModel" % pasG, (R0Model,), dict())
    cls.register_storable()
    return cls 

R0G1Model = R0_model_generator(1)
R0G2Model = R0_model_generator(2)
R0G3Model = R0_model_generator(3)
R0G4Model = R0_model_generator(4)
R0G5Model = R0_model_generator(5)
R0G6Model = R0_model_generator(6)
