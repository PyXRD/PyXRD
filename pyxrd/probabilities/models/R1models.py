# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.


from mvc.models.properties import FloatProperty, BoolProperty

from pyxrd.generic.mathtext_support import mt_range
from pyxrd.generic.io import storables
from pyxrd.generic.utils import not_none
from pyxrd.generic.models.properties import InheritableMixin

from pyxrd.refinement.refinables.properties import RefinableMixin

from .base_models import _AbstractProbability
from mvc.models.properties.action_mixins import SetActionMixin

__all__ = [
    "R1G2Model",
    "R1G3Model",
    "R1G4Model",
]

@storables.register()
class R1G2Model(_AbstractProbability):
    r"""
    Probability model for Reichweite 1 with 2 components.
    
    The 2(=g*(g-1)) independent variables are:
    
    .. math::
        :nowrap:
        
        \begin{flalign*}
            & W_1 \\
            & \text{$P_{11} (W_1 < 0.5)$ or $P_{22} (W_1 > 0.5)$}
        \end{flalign*}
    
    Calculation of the other variables happens as follows:
    
    .. math::
        :nowrap:
        
        \begin{align*}
            & W_2 = 1 – W_1 \\
            & \begin{aligned}
                & \text{$P_{11}$ is given:}  \\
                & \quad P_{12} = 1 - P_{11} \\
                & \quad P_{21} = \frac{W_1 \cdot P_{12}}{W2} \\
                & \quad P_{22} = 1 - P_{21} \\
            \end{aligned}
            \quad \quad
            \begin{aligned}
                & \text{$P_{22}$ is given:} \\
                & \quad P_{21} = 1 - P_{22} \\
                & \quad P_{12} = \frac{W_2 \cdot P_{21}}{W1} \\
                & \quad P_{11} = 1 - P_{12} \\            
            \end{aligned} \\
        \end{align*}
        
    """

    # MODEL METADATA:
    class Meta(_AbstractProbability.Meta):
        store_id = "R1G2Model"

    # PROPERTIES:
    _G = 2

    inherit_W1 = BoolProperty(
        default=False, text="Inherit flag for W1",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )

    W1 = FloatProperty(
        default=0.0, text="W1", math_text=r"$W_1$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_W1", inherit_from="parent.based_on.probabilities.W1",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_P11_or_P22 = BoolProperty(
        default=False, text="Inherit flag for P11_or_P22",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )

    P11_or_P22 = FloatProperty(
        default=0.0, text="P11_or_P22",
        math_text=r"$P_{11} %s$ or $\newline P_{22} %s$" % (
            mt_range(0.0, "W_1", 0.5),
            mt_range(0.5, "W_1", 1.0)),
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_P11_or_P22", inherit_from="parent.based_on.probabilities.P11_or_P22",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, W1=0.75, P11_or_P22=0.5, inherit_W1=False, inherit_P11_or_P22=False, *args, **kwargs):
        super(R1G2Model, self).__init__(R=1, *args, **kwargs)

        with self.data_changed.hold():
            self.W1 = not_none(W1, 0.75)
            self.inherit_W1 = inherit_W1
            self.P11_or_P22 = not_none(P11_or_P22, 0.5)
            self.inherit_P11_or_P22 = inherit_P11_or_P22

            self.update()

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update(self):
        with self.monitor_changes():
            self.mW[0] = self.W1
            self.mW[1] = 1.0 - self.mW[0]
            if self.mW[0] <= 0.5:
                self.mP[0, 0] = self.P11_or_P22
                self.mP[0, 1] = 1.0 - self.mP[0, 0]
                self.mP[1, 0] = self.mW[0] * self.mP[0, 1] / self.mW[1]
                self.mP[1, 1] = 1.0 - self.mP[1, 0]
            else:
                self.mP[1, 1] = self.P11_or_P22
                self.mP[1, 0] = 1.0 - self.mP[1, 1]
                self.mP[0, 1] = self.mW[1] * self.mP[1, 0] / self.mW[0]
                self.mP[0, 0] = 1.0 - self.mP[0, 1]

            self.solve()
            self.validate()

    pass # end of class

@storables.register()
class R1G3Model(_AbstractProbability):
    r"""
    Probability model for Reichweite 1 with 3 components.
    
    The 6 (=g*(g-1)) independent variables are:
    
    .. math::
        :nowrap:
        
        \begin{align*}
                & W_1
                & \text{$P_{11} (W_1 < 0.5)$ or $P_{xx} (W_1 > 0.5)$}
                with P_{xx} = \frac {W_{22} + W_{23} + W_{32} + W_{33} + W_{42} + W_{43}}{W_2 + W_3} \\
                & G_1 = \frac{W_2}{W_2 + W_3}
                & G_2 = \frac{W_{22} + W_{23}}{W_{22} + W_{23} + W_{32} + W_{33}} \\
                & G_3 = \frac{W_{22}}{W_{22} + W_{23}}
                & G_4 = \frac{W_{32}}{W_{32} + W_{33}} \\
        \end{align*}
            
    Calculation of the other variables happens as follows:
    
    
    
    .. math::
        :nowrap:
        
        \begin{align*}
            & \text{Calculate the 'inverted' ratios of $G_2$, $G_3$ and $G_4$ as follows:} \\
            & \quad G_i^{\text{-1}} =
            \begin{cases}
                G_i^{-1} - 1.0, & \text{if } G_i > 0 \\
                0,              & \text{otherwise}
            \end{cases} \quad \forall i \in \left\{ {2, 3, 4}\right\} \\
            & \\
            & \text{Calculate the base weight fractions of each component:} \\
            & \quad W_2 = (1 - W_1) \cdot G_1\\
            & \quad W_3 = 1.0 - W_1 - W_2 \\
            & \\
            & \text{if $W_1 \leq 0.5$:} \\
            & \quad \text{$P_{11}$ is given and W_xx is derived as} \\
            & \quad W_{xx} = W_{22} + W_{23} + W_{32} + W_{23} = W_1 \cdot (1 - P_{11}) + W_2 + W_3 \\ 
            & \\
            & \text{if $W_1 > 0.5$:} \\
            & \quad \text{$P_{xx}$ is given and $P_{11}$ is derived further down} \\
            & \quad W_{xx} = W_{22} + W_{23} + W_{32} + W_{23} = P_{xx} \cdot (W_2 + W_3) \\
            & \\
            & W_{22} = W_{xx} \cdot G_2 \cdot G_3 \\
            & W_{23} = W_{22} \cdot G_3^{-1} \\
            & W_{32} = W_{xx} \cdot (1 - G_2) \\
            & W_{33} = G_4^{-1} \cdot W_{32} \\
            & \\
            & P_{23} = 
            \begin{dcases}
                \dfrac{W_{23}}{W_2}, & \text{if $W_2 > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & P_{12} = 1 - P_{22} - P_{23} \\
            & \\
            & P_{32} =
            \begin{dcases}
                \frac{W_{32}}{W_3}, & \text{if $W_3 > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & P_{33} =
            \begin{dcases}
                \frac{W_{33}}{W_3}, & \text{if $W_3 > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & P_{31} = 1 - P_{32} - P_{33} \\
            & \\
            & P_{12} =
            \begin{dcases}
                \frac{W_2 - W_{22} - W_{32}}{W_1}, & \text{if $W_1 > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & P_{13} =
            \begin{dcases}
                \frac{W_3 - W_{23} - W_{33}}{W_1}, & \text{if $W_1 > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & \\
            & \text{if $W_1 > 0.5$}: \\
            & \quad P_{11} = 1 - P_{12} - P_{13} \\
            & \\
            & \text{Remainder of weight fraction can be calculated as follows:} \\
            & \quad W_{ij} = {W_{ii}} \cdot {P_{ij}} \quad \forall {i,j} \in \left[ {1, 3} \right] \\
        \end{align*}
        
    """

    # MODEL METADATA:
    class Meta(_AbstractProbability.Meta):
        store_id = "R1G3Model"

    # PROPERTIES
    _G = 3

    inherit_W1 = BoolProperty(
        default=False, text="Inherit flag for W1",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    W1 = FloatProperty(
        default=0.8, text="W1", math_text=r"$W_1$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_W1", inherit_from="parent.based_on.probabilities.W1",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_P11_or_P22 = BoolProperty(
        default=False, text="Inherit flag for P11_or_P22",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    P11_or_P22 = FloatProperty(
        default=0.7, text="P11_or_P22",
        math_text=r"$P_{11} %s$ or $\newline P_{22} %s$" % (
            mt_range(0.0, "W_1", 0.5),
            mt_range(0.5, "W_1", 1.0)),
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_P11_or_P22", inherit_from="parent.based_on.probabilities.P11_or_P22",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_G1 = BoolProperty(
        default=False, text="Inherit flag for G1",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    G1 = FloatProperty(
        default=0.7, text="W2/(W2+W3)",
        math_text=r"$\large\frac{W_2}{W_3 + W_2}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_G1", inherit_from="parent.based_on.probabilities.G1",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_G2 = BoolProperty(
        default=False, text="Inherit flag for G2",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    G2 = FloatProperty(
        default=0.7, text="(W22+W23)/(W22+W23+W32+W33)",
        math_text=r"$\large\frac{W_{22} + W_{23}}{W_{22} + W_{23} + W_{32} + W_{33}}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_G2", inherit_from="parent.based_on.probabilities.G2",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_G3 = BoolProperty(
        default=False, text="Inherit flag for G3",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    G3 = FloatProperty(
        default=0.7, text="W22/(W22+W23)",
        math_text=r"$\large\frac{W_{22}}{W_{22} + W_{23}}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_G3", inherit_from="parent.based_on.probabilities.G3",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_G4 = BoolProperty(
        default=False, text="Inherit flag for G4",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    G4 = FloatProperty(
        default=0.7, text="W23/(W32+W33)",
        math_text=r"$\large\frac{W_{22}}{W_{22} + W_{23}}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_G4", inherit_from="parent.based_on.probabilities.G4",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, W1=0.8, P11_or_P22=0.7, G1=0.7, G2=0.7, G3=0.7, G4=0.7,
            inherit_W1=False, inherit_P11_or_P22=False, inherit_G1=False,
            inherit_G2=False, inherit_G3=False, inherit_G4=False, *args, **kwargs):
        super(R1G3Model, self).__init__(R=1, *args, **kwargs)

        with self.data_changed.hold():
            self.W1 = not_none(W1, 0.8)
            self.inherit_W1 = bool(inherit_W1)
            self.P11_or_P22 = not_none(P11_or_P22, 0.7)
            self.inherit_P11_or_P22 = bool(inherit_P11_or_P22)
            self.G1 = not_none(G1, 0.7)
            self.inherit_G1 = bool(inherit_G1)
            self.G2 = not_none(G2, 0.7)
            self.inherit_G2 = bool(inherit_G2)
            self.G3 = not_none(G3, 0.7)
            self.inherit_G3 = bool(inherit_G3)
            self.G4 = not_none(G4, 0.7)
            self.inherit_G4 = bool(inherit_G4)

            self.update()

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update(self):
        with self.monitor_changes():
            self.mW[0] = self.W1
            self.mW[1] = (1 - self.mW[0]) * self.G1
            self.mW[2] = 1.0 - self.mW[0] - self.mW[1]

            W0inv = 1.0 / self.mW[0] if self.mW[0] > 0.0 else 0.0

            Wxx = 0
            if self.mW[0] <= 0.5: # P00 given
                self.mP[0, 0] = self.P11_or_P22
                # Wxx = W11 + W12 + W21 + W22
                Wxx = self.mW[0] * (self.mP[0, 0] - 1) + self.mW[1] + self.mW[2]
            else: # Pxx given
                # Wxx = W11 + W12 + W21 + W22
                Wxx = (1.0 - self.mW[0]) * self.P11_or_P22

            # W11 + W12 = Wxx * G2:
            self.mW[1, 1] = Wxx * self.G2 * self.G3
            self.mW[1, 2] = Wxx * self.G2 * (1 - self.G3)
            self.mP[1, 1] = self.mW[1, 1] / self.mW[1] if self.mW[1] > 0.0 else 0.0

            self.mW[2, 1] = Wxx * (1 - self.G2) * self.G4
            self.mW[2, 2] = Wxx * (1 - self.G2) * (1 - self.G4)

            self.mP[1, 2] = (self.mW[1, 2] / self.mW[1]) if self.mW[1] > 0.0 else 0.0
            self.mP[1, 0] = 1 - self.mP[1, 1] - self.mP[1, 2]

            self.mP[2, 1] = (self.mW[2, 1] / self.mW[2]) if self.mW[2] > 0.0 else 0.0
            self.mP[2, 2] = (self.mW[2, 2] / self.mW[2]) if self.mW[2] > 0.0 else 0.0
            self.mP[2, 0] = 1 - self.mP[2, 1] - self.mP[2, 2]

            self.mP[0, 1] = (self.mW[1] - self.mW[1, 1] - self.mW[2, 1]) * W0inv
            self.mP[0, 2] = (self.mW[2] - self.mW[1, 2] - self.mW[2, 2]) * W0inv

            if self.mW[0] > 0.5:
                self.mP[0, 0] = 1 - self.mP[0, 1] - self.mP[0, 2]

            for i in range(3):
                for j in range(3):
                    self.mW[i, j] = self.mW[i, i] * self.mP[i, j]

            self.solve()
            self.validate()

    pass # end of class

@storables.register()
class R1G4Model(_AbstractProbability):

    r"""
    Probability model for Reichweite 1 with 4 components.
    
    The independent variables (# = g*(g-1) = 12) are:
    
    .. math::
        :nowrap:
        
            \begin{align*}
                & W_1
                & P_{11} (W_1 < 0,5)\text{ or }P_{xx} (W_1 > 0,5) 
                with P_{xx} = \frac {W_{22} + W_{23} + W_{24} + W_{32} + W_{33} + W_{34} + W_{42} + W_{43} + W_{44}}{W_2 + W_3 + W_4} \\
                & R_2 = \frac{ W_2 }{W_2 + W_3 + W_4}
                & R_3 = \frac{ W_3 }{W_3 + W_4} \\
                & G_2 = \frac{W_{22} + W_{23} + W_{24}}{\sum_{i=2}^{4}\sum_{j=2}^4{W_{ij}}}
                & G_3 = \frac{W_{32} + W_{33} + W_{34}}{\sum_{i=3}^{4}\sum_{j=2}^4{W_{ij}}} \\
                & G_{22} = \frac{W_{22}}{W_{22} + W_{23} + W_{24}}
                & G_{23} = \frac{W_{23}}{W_{23} + W_{24}} \\
                & G_{32} = \frac{W_{32}}{W_{32} + W_{33} + W_{34}}
                & G_{33} = \frac{W_{33}}{W_{33} + W_{34}} \\
                & G_{42} = \frac{W_{42}}{W_{42} + W_{43} + W_{44}}
                & G_{44} = \frac{W_{43}}{W_{43} + W_{44}}
            \end{align*} 
    
    Calculation of the other variables happens as follows:
    
    .. math::
        :nowrap:
        
        \begin{align*}
            & \text{Calculate the base weight fractions of each component:} \\
            & W_2 = (1 - W_1) \cdot R_1 \\
            & W_3 = (1 - W_1 - W_2) \cdot R_2 \\
            & W_4 = (1 - W_1 - W_2 - W_3) \\
            & \\
            & \text{if $W_1 \leq 0.5$:} \\
            & \quad \text{$P_{11}$ is given}\\
            & \quad W_{xx} = W_{22} + W_{23} + W_{24} + W_{32} + W_{33} + W_{34} + W_{42} + W_{43} + W_{44} = W_1 \cdot (1 - P_{11}) + W_2 + W_3 + W_4 \\
            & \text{if $W_1 > 0.5$:} \\
            & \quad \text{$P_{xx}$ is given and $P_{11}$ is derived further down} \\
            & \quad W_{xx} = W_{22} + W_{23} + W_{24} + W_{32} + W_{33} + W_{34} + W_{42} + W_{43} + W_{44} = P_{xx} \cdot (W_2 + W_3 + W_4) \\  
            & \\
            & \text{Caclulate a partial sum of the $2^{nd}$ component's contributions: } \\
            & W_{2x} = W_{xx} \cdot G_2 \\
            & \text{Calculate a partial sum of the $3^{d}$ and $4^{th}$ component's contributions:} \\
            & W_{yx} = W_{xx} - W_{2x} \\
            & \text{Calculate a partial sum of the $3^{d}$ component's contributions:} \\
            & W_{3x} = W_{yx} \cdot G_3 \\
            & \text{Calculate a partial sum of the $4^{th}$ component's contributions:} \\
            & W_{4x} = W_{yx} - W_{3x} \\
            & \\
            & W_{22} = G_{22} \cdot W_{2x} \\
            & W_{23} = G_{23} \cdot (W_{2x} - W_{22}) \\
            & W_{24} = W{2x} - W_{22} - W_{23} \\
            & \\
            & W_{32} = G_{32} \cdot W_{3x} \\
            & W_{33} = G_{33} \cdot (W_{3x} - W_{32}) \\
            & W_{34} = W{3x} - W_{32} - W_{33} \\
            & \\
            & W_{42} = G_{42} \cdot W_{4x} \\
            & W_{43} = G_{43} \cdot (W_{4x} - W_{42}) \\
            & W_{44} = W{4x} - W_{42} - W_{43} \\
            & \\
            & \text{ From the above weight fractions the junction probabilities 
                for any combination of $2^{nd}$, $3^{d}$ and $4^{th}$ type
                components can be calculated. } \\
            & \text{ The remaining probabilities are: } \\
            & P_{12} = \begin{dcases}
                \frac{W_2 - W_{22} - W_{32} - W_{42}}{W_1}, & \text{if $W_1 > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & P_{13} = \begin{dcases}
                \frac{W_3 - W_{23} - W_{33} - W_{43}}{W_1}, & \text{if $W_1 > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & P_{14} = \begin{dcases}
                \frac{W_4 - W_{24} - W_{34} - W_{44}}{W_1}, & \text{if $W_1 > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & \\
            & \text{if $W_1 \leq 0.5$}: \\
            & \quad P_{11} = 1 - P_{12} - P_{13} - P_{14} \\
            & \text{Remainder of weight fraction can now be calculated as follows:} \\
            & \quad W_{ij} = {W_{ii}} \cdot {P_{ij}} \quad \forall {i,j} \in \left[ {1, 4} \right] \\
        \end{align*}
    """

    # MODEL METADATA:
    class Meta(_AbstractProbability.Meta):
        store_id = "R1G4Model"

    # PROPERTIES
    _G = 4

    inherit_W1 = BoolProperty(
        default=False, text="Inherit flag for W1",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    W1 = FloatProperty(
        default=0.6, text="W1", math_text=r"$W_1$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_W1", inherit_from="parent.based_on.probabilities.W1",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_P11_or_P22 = BoolProperty(
        default=False, text="Inherit flag for P11_or_P22",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    P11_or_P22 = FloatProperty(
        default=0.25, text="P11_or_P22",
        math_text=r"$P_{11} %s$ or $\newline P_{22} %s$" % (
            mt_range(0.0, "W_1", 0.5),
            mt_range(0.5, "W_1", 1.0)),
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_P11_or_P22", inherit_from="parent.based_on.probabilities.P11_or_P22",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_R1 = BoolProperty(
        default=False, text="Inherit flag for R1",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    R1 = FloatProperty(
        default=0.5, text="W2/(W2+W3+W4)",
        math_text=r"$\large\frac{W_2}{W_2 + W_3 + W_4}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_R1", inherit_from="parent.based_on.probabilities.R1",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_R2 = BoolProperty(
        default=False, text="Inherit flag for R2",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    R2 = FloatProperty(
        default=0.5, text="W3/(W3+W4)",
        math_text=r"$\large\frac{W_3}{W_3 + W_4}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_R2", inherit_from="parent.based_on.probabilities.R2",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_G1 = BoolProperty(
        default=False, text="Inherit flag for G1",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    G1 = FloatProperty(
        default=0.5, text="(W22+W23+W24)/(W22+W23+W24+W32+W33+W34+W42+W43+W44)",
        math_text=r"$\large\frac{\sum_{j=2}^{4} W_{2j}}{\sum_{i=2}^{4} \sum_{j=2}^{4} W_{ij}}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_G1", inherit_from="parent.based_on.probabilities.G1",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_G2 = BoolProperty(
        default=False, text="Inherit flag for G2",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    G2 = FloatProperty(
        default=0.4, text="(W32+W33+W34)/(W32+W33+W34+W42+W43+W44)",
        math_text=r"$\large\frac{\sum_{j=2}^{4} W_{3j}}{\sum_{i=3}^{4} \sum_{j=2}^{4} W_{ij}}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_G2", inherit_from="parent.based_on.probabilities.G2",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_G11 = BoolProperty(
        default=False, text="Inherit flag for G11",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    G11 = FloatProperty(
        default=0.5, text="W22/(W22+W23+W24)",
        math_text=r"$\large\frac{W_{22}}{\sum_{j=2}^{4} W_{2j}}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_G11", inherit_from="parent.based_on.probabilities.G11",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_G12 = BoolProperty(
        default=False, text="Inherit flag for G12",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    G12 = FloatProperty(
        default=0.5, text="W23/(W23+W24)",
        math_text=r"$\large\frac{W_{23}}{\sum_{j=3}^{4} W_{2j}}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_G12", inherit_from="parent.based_on.probabilities.G12",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_G21 = BoolProperty(
        default=False, text="Inherit flag for G21",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    G21 = FloatProperty(
        default=0.8, text="W32/(W32+W33+W34)",
        math_text=r"$\large\frac{W_{32}}{\sum_{j=2}^{4} W_{3j}}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_G21", inherit_from="parent.based_on.probabilities.G21",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_G22 = BoolProperty(
        default=False, text="Inherit flag for G22",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    G22 = FloatProperty(
        default=0.8, text="W33/(W32+W34)",
        math_text=r"$\large\frac{W_{33}}{\sum_{j=3}^{4} W_{3j}}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_G22", inherit_from="parent.based_on.probabilities.G22",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_G31 = BoolProperty(
        default=False, text="Inherit flag for G31",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    G31 = FloatProperty(
        default=0.7, text="W42/(W42+W43+W44)",
        math_text=r"$\large\frac{W_{42}}{\sum_{j=2}^{4} W_{4j}}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_G31", inherit_from="parent.based_on.probabilities.G31",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    inherit_G32 = BoolProperty(
        default=False, text="Inherit flag for G32",
        persistent=True, visible=True,
        set_action_name="update",
        mix_with=(SetActionMixin,)
    )
    G32 = FloatProperty(
        default=0.5, text="W43/(W43+W44)",
        math_text=r"$\large\frac{W_{43}}{\sum_{j=3}^{4} W_{4j}}$",
        persistent=True, visible=True, refinable=True, store_private=True,
        minimum=0.0, maximum=1.0, is_independent=True, inheritable=True,
        inherit_flag="inherit_G32", inherit_from="parent.based_on.probabilities.G32",
        set_action_name="update",
        mix_with=(SetActionMixin, RefinableMixin, InheritableMixin)
    )

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------

    def __init__(self, W1=0.6, P11_or_P22=0.25, R1=0.5, R2=0.5, G1=0.5, G2=0.4,
            G11=0.5, G12=0.5, G21=0.8, G22=0.75, G31=0.7, G32=0.5,
            inherit_W1=False, inherit_P11_or_P22=False, inherit_R1=False,
            inherit_R2=False, inherit_G1=False, inherit_G2=False,
            inherit_G11=False, inherit_G12=False, inherit_G21=False,
            inherit_G22=False, inherit_G31=False, inherit_G32=False, *args, **kwargs):
        super(R1G4Model, self).__init__(R=1, *args, **kwargs)

        with self.data_changed.hold():
            self.W1 = not_none(W1, 0.6)
            self.inherit_W1 = inherit_W1
            self.P11_or_P22 = not_none(P11_or_P22, 0.25)
            self.inherit_P11_or_P22 = inherit_P11_or_P22
            self.R1 = not_none(R1, 0.5)
            self.inherit_R1 = inherit_R1
            self.R2 = not_none(R2, 0.5)
            self.inherit_R2 = inherit_R2
            self.G1 = not_none(G1, 0.5)
            self.inherit_G1 = inherit_G1
            self.G2 = not_none(G2, 0.4)
            self.inherit_G2 = inherit_G2
            self.G11 = not_none(G11, 0.5)
            self.inherit_G11 = inherit_G11
            self.G12 = not_none(G12, 0.5)
            self.inherit_G12 = inherit_G12
            self.G21 = not_none(G21, 0.8)
            self.inherit_G21 = inherit_G21
            self.G22 = not_none(G22, 0.75)
            self.inherit_G22 = inherit_G22
            self.G31 = not_none(G31, 0.7)
            self.inherit_G31 = inherit_G31
            self.G32 = not_none(G32, 0.5)
            self.inherit_G32 = inherit_G32

            self.update()

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update(self):
        with self.monitor_changes():
            self.mW[0] = self.W1
            self.mW[1] = (1.0 - self.mW[0]) * self.R1
            self.mW[2] = (1.0 - self.mW[0] - self.mW[1]) * self.R2
            self.mW[3] = 1.0 - self.mW[0] - self.mW[1] - self.mW[2]

            W0inv = 1.0 / self.mW[0] if self.mW[0] > 0.0 else 0.0

            if self.mW[0] < 0.5: # P11 is given
                self.mP[0, 0] = self.P11_or_P22
                Wxx = self.mW[0] * (self.mP[0, 0] - 1) + self.mW[1] + self.mW[2] + self.mW[3]
            else: # P22 is given
                Wxx = self.P11_or_P22 * (self.mW[1] + self.mW[2] + self.mW[3])

            W1x = Wxx * self.G1 # = W11 + W12 + W13
            Wyx = (Wxx - W1x)   # = W21 + W22 + W23 + W31 + W32 + W33
            W2x = Wyx * self.G2 # = W21 + W22 + W23
            W3x = Wyx - W2x     # = W31 + W32 + W33

            self.mW[1, 1] = self.G11 * W1x
            self.mW[1, 2] = self.G12 * (W1x - self.mW[1, 1])
            self.mW[1, 3] = W1x - self.mW[1, 1] - self.mW[1, 2]

            self.mW[2, 1] = self.G21 * W2x
            self.mW[2, 2] = self.G22 * (W2x - self.mW[2, 1])
            self.mW[2, 3] = W2x - self.mW[2, 1] - self.mW[2, 2]

            self.mW[3, 1] = self.G31 * W3x
            self.mW[3, 2] = self.G32 * (W3x - self.mW[3, 1])
            self.mW[3, 3] = W3x - self.mW[3, 1] - self.mW[3, 2]

            for i in range(1, 4):
                self.mP[i, 0] = 1
                for j in range(1, 4):
                    self.mP[i, j] = self.mW[i, j] / self.mW[i] if self.mW[i] > 0 else 0
                    self.mP[i, 0] -= self.mP[i, j]
                self.mW[i, 0] = self.mW[i] * self.mP[i, 0]

            self.mP[0, 1] = (self.mW[1] - self.mW[1, 1] - self.mW[2, 1] - self.mW[3, 1]) * W0inv
            self.mP[0, 2] = (self.mW[2] - self.mW[1, 2] - self.mW[2, 2] - self.mW[3, 2]) * W0inv
            self.mP[0, 3] = (self.mW[3] - self.mW[1, 3] - self.mW[2, 3] - self.mW[3, 3]) * W0inv

            if self.mW[0] >= 0.5:
                self.mP[0, 0] = 1 - self.mP[0, 1] - self.mP[0, 2] - self.mP[0, 3]

            for i in range(4):
                for j in range(4):
                    self.mW[i, j] = self.mW[i] * self.mP[i, j]

            self.solve()
            self.validate()

    pass # end of class
