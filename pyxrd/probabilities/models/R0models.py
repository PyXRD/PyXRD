# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from pyxrd.mvc import PropIntel
from pyxrd.generic.io import storables
from pyxrd.generic.utils import not_none

from .base_models import _AbstractProbability
from pyxrd.probabilities.models.properties import ProbabilityProperty

def R0_model_generator(pasG):

    class _R0Meta(_AbstractProbability.Meta):
        store_id = "R0G%dModel" % pasG
        properties = [
            PropIntel(
                name="F%d" % (g + 1), minimum=0.0, maximum=1.0, default=0.8,
                label="W%(g)d/Sum(W%(g)d+...+W%(G)d)" % {'g':g + 1, 'G':pasG },
                math_label=r"$\large\frac{W_{%(g)d}}{\sum_{i=%(g)d}^{%(G)d} W_i}$" % {'g':g + 1, 'G':pasG },
                data_type=float, refinable=True, storable=True, has_widget=True,
                is_independent=True, # flag for the view creation
                stor_name="_F%d" % (g + 1),
                inh_name="inherit_F%d" % (g + 1), inh_from="parent.based_on.probabilities") \
                for g in range(pasG - 1)
        ] + [
            PropIntel(name="inherit_F%d" % (g + 1), label="Inherit flag for F%d" % (g + 1),
                data_type=bool, refinable=False, storable=True, has_widget=True,
                default=False,
                widget_type="toggle") \
                for g in range(pasG - 1)
        ]

    class _BaseR0Model():
        """
        Probability model for Reichweite = 0
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

        # ------------------------------------------------------------
        #      Initialization and other internals
        # ------------------------------------------------------------
        def setup(self, **kwargs):
            _AbstractProbability.setup(self, R=0)

            if self.G > 1 and "W1" in kwargs: # old-style model
                for i in range(self.G - 1):
                    name = "W%d" % (i + 1)
                    self.mW[i] = not_none(kwargs.get(name, None), 0.8)
                    name = "F%d" % (i + 1)
                    setattr(self, name, self.mW[i] / (np.sum(np.diag(self._W)[i:]) or 1.0))
            else:
                for i in range(self.G - 1):
                    name = "inherit_F%d" % (i + 1)
                    setattr(self, name, kwargs.get(name, False))
                    name = "F%d" % (i + 1)
                    setattr(self, name, not_none(kwargs.get(name, None), 0.8))

        # ------------------------------------------------------------
        #      Methods & Functions
        # ------------------------------------------------------------
        def update(self):
            with self.data_changed.hold_and_emit():
                if self.G > 1:
                    for i in range(self.G - 1):
                        name = "F%d" % (i + 1)
                        if i > 0:
                            self.mW[i] = getattr(self, name) * (1.0 - np.sum(np.diag(self._W)[0:i]))
                        else:
                            self.mW[i] = getattr(self, name)
                    self.mW[self.G - 1] = 1.0 - np.sum(np.diag(self._W)[:-1])
                else:
                    self.mW[0] = 1.0
                self._P[:] = np.repeat(np.diag(self._W)[np.newaxis, :], self.G, 0)

                self.solve()
                self.validate()

        pass # end of class

    _dict = dict()
    def set_attribute(name, value): # @NoSelf
        """Sets an attribute on the class and the dict"""
        _dict[name] = value
        setattr(_BaseR0Model, name, value)

    # MODEL METADATA:
    set_attribute("_G", pasG)
    _dict["Meta"] = _R0Meta

    # PROPERTIES:
    def set_generic_F_accesors(index):
        prop = None
        for p in _R0Meta.properties:
            if p.name == "F%d" % (index + 1):
                prop = p

        set_attribute(prop.name, ProbabilityProperty(default=0.0, clamp=True, cast_to=float))
        set_attribute(prop.inh_name, ProbabilityProperty(default=False, cast_to=bool))

    for index in range(pasG - 1):
        set_generic_F_accesors(index)

    # CREATE TYPE AND REGISTER AS STORABLE:
    cls = type("R0G%dModel" % pasG, (_BaseR0Model, _AbstractProbability), _dict)
    storables.register_decorator(cls)

    return cls

R0G1Model = R0_model_generator(1)
R0G2Model = R0_model_generator(2)
R0G3Model = R0_model_generator(3)
R0G4Model = R0_model_generator(4)
R0G5Model = R0_model_generator(5)
R0G6Model = R0_model_generator(6)

__all__ = [
    "R0G1Model",
    "R0G2Model",
    "R0G3Model",
    "R0G4Model",
    "R0G5Model",
    "R0G6Model"
]
