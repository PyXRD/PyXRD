# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from mvc.models.properties import SetActionMixin, FloatProperty, BoolProperty

from pyxrd.generic.io import storables
from pyxrd.generic.utils import not_none
from pyxrd.generic.models.properties import InheritableMixin
from pyxrd.refinement.refinables.properties import RefinableMixin

from .base_models import _AbstractProbability

def R0_model_generator(pasG):

    class _R0Meta(_AbstractProbability.Meta):
        store_id = "R0G%dModel" % pasG

    class _BaseR0Model(object):
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
        def __init__(self, *args, **kwargs):
            my_kwargs = self.pop_kwargs(kwargs, *[prop.label for prop in self.Meta.get_local_persistent_properties()])
            super(_BaseR0Model, self).__init__(R=0, *args, **kwargs)

            with self.data_changed.hold():
                if self.G > 1 and "W1" in my_kwargs: # old-style model
                    for i in range(self.G - 1):
                        name = "W%d" % (i + 1)
                        self.mW[i] = not_none(my_kwargs.get(name, None), 0.8)
                        name = "F%d" % (i + 1)
                        setattr(self, name, self.mW[i] / (np.sum(np.diag(self._W)[i:]) or 1.0))
                else:
                    for i in range(self.G - 1):
                        name = "inherit_F%d" % (i + 1)
                        setattr(self, name, my_kwargs.get(name, False))
                        name = "F%d" % (i + 1)
                        setattr(self, name, not_none(my_kwargs.get(name, None), 0.8))

                self.update()

        # ------------------------------------------------------------
        #      Methods & Functions
        # ------------------------------------------------------------
        def update(self):
            with self.monitor_changes():
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
    _dict["Meta"] = _R0Meta

    def set_attribute(name, value): # @NoSelf
        """Sets an attribute on the class and the dict"""
        _dict[name] = value
        setattr(_BaseR0Model, name, value)

    set_attribute("G", pasG)

    # PROPERTIES:
    for g in range(pasG - 1):
        label = "F%d" % (g + 1)
        text = "W%(g)d/Sum(W%(g)d+...+W%(G)d)" % {'g':g + 1, 'G':pasG }
        math_text = r"$\large\frac{W_{%(g)d}}{\sum_{i=%(g)d}^{%(G)d} W_i}$" % {'g':g + 1, 'G':pasG }
        inh_flag = "inherit_F%d" % (g + 1)
        inh_from = "parent.based_on.probabilities.F%d" % (g + 1)

        set_attribute(label, FloatProperty(
            default=0.8, text=text, math_text=math_text,
            refinable=True, persistent=True, visible=True,
            minimum=0.0, maximum=1.0,
            inheritable=True, inherit_flag=inh_flag, inherit_from=inh_from,
            is_independent=True, store_private=True,
            set_action_name="update",
            mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
        ))

        label = "inherit_F%d" % (g + 1)
        text = "Inherit flag for F%d" % (g + 1)
        set_attribute(label, BoolProperty(
            default=False, text=text,
            refinable=False, persistent=True, visible=True,
            set_action_name="update",
            mix_with=(SetActionMixin,)
        ))

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
