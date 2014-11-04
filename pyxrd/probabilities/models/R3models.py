# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.generic.mathtext_support import mt_range
from pyxrd.generic.io import storables
from pyxrd.generic.utils import not_none

from mvc import PropIntel

from .base_models import _AbstractProbability
from pyxrd.probabilities.models.properties import ProbabilityProperty

__all__ = [
    "R3G2Model"
]

@storables.register()
class R3G2Model(_AbstractProbability):
    r"""
    (Restricted) probability model for Reichweite 3 with 2 components.
    
    The (due to restrictions only) 2 independent variables are:
    
    .. math::
        :nowrap:
        
        \begin{align*}
            & W_1
            & P_{1111} \text{(if $\nicefrac{2}{3} \leq W_1 < \nicefrac{3}{4}$) or} P_{2112} \text{(if $\nicefrac{3}{4} \leq W_1 \leq 1)$} \\
        \end{align*}
    
    This model can only describe mixed layers with more than 
    :math:`\nicefrac{2}{3}` of the layers being of the first type, no two layers
    of the second type occur after each other, and in which the probability of
    finding a layer of the first type in between two layers of the second type
    is zero. This translates to the following conditions:
    
    .. math::
        :nowrap:
        
        \begin{align*}
	        & \nicefrac{2}{3} <= W_1 <= 1 \\
	        & P_{22} = 0  \\
	        & P_{212} = 0 \\
	        & \\
	        & \text{Since $P_{22} = 0$ and $P_{212} = 0$:} \\
            & P_{1122} = P_{1212} = 0 \\
            & \text{And thus:} \\
            & P_{1121} = P_{1211} = 1 \\
        \end{align*} 
        
    The following probabilities are undefined, but are set to zero or one to
    make the validation correct. This doesn't matter much, since the weight
    fractions these probabilities are multiplied with, equal zero anyway
    (e.g. :math:`W_{2211} = W_{22} * P_{221} * P_{2211}` and :math:`W_{22}` 
    is zero since :math:`P_{22}` is zero):
        
    .. math::
        :nowrap:
        
        \begin{align*}
            & P_{1121} &= P_{1211} &= P_{2211} 
            &= P_{2121} &= P_{2221} &= P_{1221} = 0 \\
            & P_{1122} &= P_{1212} &= P_{2212} 
            &= P_{2122} &= P_{2222} &= P_{1222} = 1 \\
        \end{align*}  

    The remaining probabilities and weight fractions can be calculated as 
    follows:
    
   .. math::
        :nowrap:
        
        \begin{align*}
            & W_2 = 1 - W_1 \\
            & \\
            & \text{if $W_1 < \nicefrac{3}{4}$:} \\
            & \quad \text{$P_{1111}$ is given}\\
            & \quad P_{1112} = 1 - P_{1111} \\
            & \quad P_{2111} = P_{1112} * \frac{W_1 - 2 \cdot W_2}{W_2} \\
            & \quad P_{2112} = 1 - P_{2111} \\  
            & \\
            & \text{if $W_1 \geq \nicefrac{3}{4}$:} \\
            & \quad \text{$P_{2112}$ is given}\\
            & \quad P_{2111} = 1 - P_{2112} \\
            & \quad P_{1111} = P_{2111} * \frac{W_2}{W_1 - 2 \cdot W_2} \\
            & \quad P_{1112} = 1 - P_{1111} \\  
            & \\
            & W_{111} = 3 \cdot W_1 - 2 \\
            & W_{212} = W_{221} = W_{222} = W_{122} = 0 \\
            & W_{211} = W_{121} = W_{112} = 1 - W_1 \\
        \end{align*}
	
	"""

    # MODEL METADATA:
    class Meta(_AbstractProbability.Meta):
        store_id = "R3G2Model"
        ind_properties = [
            PropIntel(name="W1", label="W1 (> 2/3)", math_label=r"$W_1$",
                stor_name="_W1", inh_name="inherit_W1", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=2.0 / 3.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="P1111_or_P2112", label="P1111 (W1 < 3/4) or\nP2112 (W1 > 3/4)",
                stor_name="_P1111_or_P2112", inh_name="inherit_P1111_or_P2112",
                inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$P_{1111} %s$ or $\newline P_{2112} %s$" % (
                    mt_range(2.0 / 3.0, "W_1", 3.0 / 4.0),
                    mt_range(3.0 / 4.0, "W_1", 1.0)),
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
        ]
        inh_properties = [
            PropIntel(name="inherit_%s" % prop.name, label="Inherit flag for %s" % prop.name,
                data_type=bool, refinable=False, storable=True, has_widget=True,
                widget_type="toggle") \
                for prop in ind_properties
        ]
        properties = ind_properties + inh_properties


    # PROPERTIES:
    _G = 2

    W1 = ProbabilityProperty(default=0.85, minimum=2.0 / 3.0, clamp=True, cast_to=float)
    inherit_W1 = ProbabilityProperty(default=False, cast_to=bool)

    P1111_or_P2112 = ProbabilityProperty(default=0.75, clamp=True, cast_to=float)
    inherit_P1111_or_P2112 = ProbabilityProperty(default=False, cast_to=bool)

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.85, P1111_or_P2112=0.75, **kwargs):
        _AbstractProbability.setup(self, R=3)
        self.W1 = not_none(W1, 0.85)
        self.P1111_or_P2112 = not_none(P1111_or_P2112, 0.75)

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update(self):
        with self.data_changed.hold_and_emit():
            self.mW[0] = self.W1
            self.mW[1] = 1.0 - self.W1

            if self.mW[0] <= 0.75: # 0,0,0,0 is given
                self.mP[0, 0, 0, 0] = self.P1111_or_P2112
                self.mP[0, 0, 0, 1] = max(min(1.0 - self.mP[0, 0, 0, 0], 1.0), 0.0)
                self.mP[1, 0, 0, 0] = max(min(self.mP[0, 0, 0, 1] * (self.mW[0] - 2 * self.mW[1]) / self.mW[1], 1.0), 0.0)
                self.mP[1, 0, 0, 1] = max(min(1.0 - self.mP[1, 0, 0, 0], 1.0), 0.0)
            else: # 1,0,0,1 is given
                self.mP[1, 0, 0, 1] = self.P1111_or_P2112
                self.mP[1, 0, 0, 0] = max(min(1.0 - self.mP[1, 0, 0, 1], 1.0), 0.0)
                self.mP[0, 0, 0, 0] = max(min(1.0 - self.mP[1, 0, 0, 0] * self.mW[1] / (self.mW[0] - 2 * self.mW[1]), 1.0), 0.0)
                self.mP[0, 0, 0, 1] = max(min(1.0 - self.mP[0, 0, 0, 0], 1.0), 0.0)

            # since P11=0 and P101=0, actual values don't matter:
            self.mP[0, 0, 1, 0] = 1.0
            self.mP[0, 0, 1, 1] = 0.0

            self.mP[0, 1, 0, 0] = 1.0
            self.mP[0, 1, 0, 1] = 0.0

            self.mP[0, 1, 1, 0] = 1.0
            self.mP[0, 1, 1, 1] = 0.0

            self.mP[1, 0, 1, 0] = 1.0
            self.mP[1, 0, 1, 1] = 0.0

            self.mP[1, 1, 0, 0] = 1.0
            self.mP[1, 1, 0, 1] = 0.0

            self.mP[1, 1, 1, 0] = 1.0
            self.mP[1, 1, 1, 1] = 0.0

            self.mW[0, 0, 0] = max(min(3 * self.mW[0] - 2, 1.0), 0.0)
            self.mW[1, 0, 1] = self.mW[1, 1, 0] = self.mW[1, 1, 1] = self.mW[0, 1, 1] = 0.0
            self.mW[1, 0, 0] = self.mW[0, 1, 0] = self.mW[0, 0, 1] = max(min(1 - self.mW[0], 1.0), 0.0)

            self.solve()
            self.validate()

    pass # end of class
