# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from mvc import PropIntel
from pyxrd.generic.mathtext_support import mt_range
from pyxrd.generic.io import storables
from pyxrd.generic.utils import not_none

from .base_models import _AbstractProbability
from pyxrd.probabilities.models.properties import ProbabilityProperty

__all__ = [
    "R2G2Model",
    "R2G3Model"
]

@storables.register()
class R2G2Model(_AbstractProbability):
    r"""
    Probability model for Reichweite 2 with 2 components.
    
    The 4 (=g^2) independent variables are:
    
    .. math::
        :nowrap:
    
        \begin{align*}
            & W_1
            & P_{112} (W_1 leq \nicefrac{2}{3})
            \text{ or }P_{211} (W_1 > \nicefrac{2}{3}) \\
            & P_{21}
            & P_{122} (P_{21} leq \nicefrac{1}{2})
            \text{ or }P_{221} (P_{21} > \nicefrac{1}{2}) \\
        \end{align*}
            
    Calculation of the other variables happens as follows:
    
    .. math::
        :nowrap:

        \begin{align*}
            & W_2 = 1 - W_1 \\
            & P_{22} = 1 - P_{21} \\
            & \\
            & W_{21} = W_2 \cdot P_{21} \\
            & W_{21} = W_{12} \\
            & W_{11} = W_1 - W_{21} \\
            & W_{22} = W_{2} \cdot P_{22} \\
            & \\
            & \text{if $W_1 leq \nicefrac{2}{3}$:} \\
            & \quad \text{$P_{112}$ is given}\\
            & \quad P_{211} =
            \begin{dcases}
                \frac{W_{11}}{W_{21}} \cdot P_{112} , & \text{if $W_{21} > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & \\
            & \text{if $W_1 > \nicefrac{2}{3}$:} \\
            & \quad \text{$P_{211}$ is given}\\
            & \quad P_{112} =
            \begin{dcases}
                \frac{W_{21}}{W_{11}} \cdot P_{211} , & \text{if $W_{11} > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & \\
            & P_{212} = 1 - P_{211} \\
            & P_{111} = 1 - P_{112} \\
            & \\
            & \text{if $P_{21} leq \nicefrac{1}{2}$:} \\
            & \quad \text{$P_{122}$ is given}\\
            & \quad P_{221} =
            \begin{dcases}
                \frac{W_{12}}{W_{22}} \cdot P_{122} , & \text{if $W_{22} > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & \\
            & \text{if $P_{21} > \nicefrac{1}{2}$:} \\
            & \quad \text{$P_{221}$ is given}\\
            & \quad P_{122} =
            \begin{dcases}
                \frac{W_{22}}{W_{12}} \cdot P_{221} , & \text{if $W_{12} > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & P_{121} = 1 - P_{122} \\
            & P_{222} = 1 - P_{221} \\
        \end{align*}
    
    """

    # MODEL METADATA:
    class Meta(_AbstractProbability.Meta):
        store_id = "R2G2Model"
        ind_properties = [
            PropIntel(name="W1", label="W1 (> 0.5)", math_label=r"$W_1$",
                stor_name="_W1", inh_name="inherit_W1", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.5, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="P112_or_P211", label="P112 (W1 < 2/3) or\nP211 (W1 > 2/3)",
                stor_name="_P112_or_P211", inh_name="inherit_P112_or_P211",
                 inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$P_{112} %s$ or $\newlineP_{211} %s$" % (
                    mt_range(1.0 / 2.0, "W_1", 2.0 / 3.0),
                    mt_range(2.0 / 3.0, "W_1", 1.0)),
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="P21", label="P21", math_label=r"$P_{21}$",
                stor_name="_P21", inh_name="inherit_P21",
                inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="P122_or_P221", label="P122_or_P221",
                stor_name="_P122_or_P221", inh_name="inherit_P122_or_P221",
                inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$P_{122} %s$ or $\newlineP_{221} %s$" % (
                    mt_range(0.0, "W_1", 1.0 / 2.0),
                    mt_range(1.0 / 2.0, "W_1", 1.0)),
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
    twothirds = 2.0 / 3.0

    W1 = ProbabilityProperty(minimum=0.5, default=0.75, clamp=True, cast_to=float)
    inherit_W1 = ProbabilityProperty(default=False, cast_to=bool)

    P112_or_P211 = ProbabilityProperty(default=0.75, clamp=True, cast_to=float)
    inherit_P112_or_P211 = ProbabilityProperty(default=False, cast_to=bool)

    P21 = ProbabilityProperty(default=0.75, clamp=True, cast_to=float)
    inherit_P21 = ProbabilityProperty(default=False, cast_to=bool)

    P122_or_P221 = ProbabilityProperty(default=0.75, clamp=True, cast_to=float)
    inherit_P122_or_P221 = ProbabilityProperty(default=False, cast_to=bool)

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.75, P112_or_P211=0.75, P21=0.75, P122_or_P221=0.75,
            inherit_W1=False, inherit_P112_or_P211=False,
            inherit_P21=False, inherit_P122_or_P221=False, **kwargs):
        _AbstractProbability.setup(self, R=2)
        with self.data_changed.hold():
            self.W1 = not_none(W1, 0.75)
            self.inherit_W1 = inherit_W1
            self.P112_or_P211 = not_none(P112_or_P211, 0.75)
            self.inherit_P112_or_P211 = inherit_P112_or_P211
            self.P21 = not_none(P21, 0.75)
            self.inherit_P21 = inherit_P21
            self.P122_or_P221 = not_none(P122_or_P221, 0.75)
            self.inherit_P122_or_P221 = inherit_P122_or_P221

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update(self):
        with self.data_changed.hold_and_emit():
            self.mW[0] = self.W1
            self.mW[1] = 1.0 - self.mW[0]

            self.mP[1, 0] = self.P21
            self.mP[1, 1] = 1.0 - self.mP[1, 0]

            self.mW[1, 0] = self.mW[1] * self.mP[1, 0]
            self.mW[1, 1] = self.mW[1] * self.mP[1, 1]
            self.mW[0, 1] = self.mW[1, 0]
            self.mW[0, 0] = self.mW[0] - self.mW[1, 0]

            if self.mW[0] <= self.twothirds:
                self.mP[0, 0, 1] = self.P112_or_P211
                if self.mW[1, 0] == 0.0:
                    self.mP[1, 0, 0] = 0.0
                else:
                    self.mP[1, 0, 0] = self.mP[0, 0, 1] * self.mW[0, 0] / self.mW[1, 0]
            else:
                self.mP[1, 0, 0] = self.P112_or_P211
                if self.mW[0, 0] == 0.0:
                    self.mP[0, 0, 1] = 0.0
                else:
                    self.mP[0, 0, 1] = self.mP[1, 0, 0] * self.mW[1, 0] / self.mW[0, 0]
            self.mP[1, 0, 1] = 1.0 - self.mP[1, 0, 0]
            self.mP[0, 0, 0] = 1.0 - self.mP[0, 0, 1]

            if self.mP[1, 0] <= 0.5:
                self.mP[0, 1, 1] = self.P122_or_P221
                self.mP[1, 1, 0] = self.mP[0, 1, 1] * self.mW[0, 1] / self.mW[1, 1]
            else:
                self.mP[1, 1, 0] = self.P122_or_P221
                self.mP[0, 1, 1] = self.mP[1, 1, 0] * self.mW[1, 1] / self.mW[0, 1]
            self.mP[0, 1, 0] = 1.0 - self.mP[0, 1, 1]
            self.mP[1, 1, 1] = 1.0 - self.mP[1, 1, 0]

            self.solve()
            self.validate()

    pass # end of class

@storables.register()
class R2G3Model(_AbstractProbability):
    r"""
    
    (Restricted) probability model for Reichweite 2 with 3 components.
    
    The (due to restrictions only) 6 independent variables are:
    
    .. math::
        :nowrap:

        \begin{align*}
            & W_{1}
            & P_{111} \text{(if $\nicefrac{1}{2} \leq W_1 < \nicefrac{2}{3}$) or} P_{x1x} \text{(if $\nicefrac{2}{3} \leq W_1 \leq 1)$ with $x \in \left\{ {2,3} \right\}$} \\
            & G_1 = \frac{W_2}{W_2 + W_3}
            & G_2 = \frac{W_{212} + W_{213}}{W_{212} + W_{213} + W_{312} + W_{313}} \\
            & G_3 = \frac{W_{212}}{W_{212} + W_{213}}
            & G_4 = \frac{W_{312}}{W_{312} + W_{313}} \\
        \end{align*}
        
    This model can not describe mixed layers in which the last two components
    occur right after each other in a stack. In other words there is always
    an alternation between (one or more) layers of the first component and a 
    single layer of the second or third component. Therefore, the weight 
    fraction of the first component (:math:`W_1`) needs to be > than 1/2.
    
    The restriction also translates in the following:
    
    .. math::
        :nowrap:
        
        \begin{align*}
            & P_{22} = P_{23} = P_{32} = P_{33} = 0 \\
            & P_{21} = P_{31} = 1 \\
            & \\
            & P_{122} = P_{123} = P_{132} = P_{133} = 0 \\
            & P_{121} = P_{131} = 1 \\
            & \\
            & P_{222} = P_{223} = P_{232} = P_{233} = 0 \\
            & P_{221} = P_{231} = 1 \\
            & \\
            & P_{322} = P_{323} = P_{332} = P_{333} = 0 \\
            & P_{321} = P_{331} = 1 \\
        \end{align*}
    
    Using the above, we can calculate a lot of the weight fractions of stacks:
    
    .. math::
        :nowrap:
    
        \begin{align*}
            & W_{22} = W_{23} = W_{32} = W_{33} 0 \\
            & W_{21} = W_{2} \\
            & W_{31} = W_{3} \\
            & \\
            & W_{122} = W_{123} = W_{132} = W_{133} = 0 \\
            & W_{121} = W_{12} = W_{21} = W_2 \\
            & W_{131} = W_{13} = W_{31} = W_3 \\
            & W_{11} = W_1 - W_{12} - W_{13} \\
            & \\
            & W_{221} = W_{231} = W_{222} = W_{223} = W_{232} = W_{233} = 0 \\
            & W_{331} = W_{331} = W_{322} = W_{323} = W_{332} = W_{333} = 0 \\             
        \end{align*}

    Then the remaining fractions and probablities can be calculated as follows:
    
    .. math::
        :nowrap:
    
        \begin{align*}
            & W_2 = G_1 * (1 - W_1) \\
            & W_3 = 1 - W_1 - W_2 \\
            & \\
            & W_x = W_2 + W_3 &
            & \text{if $W_1 < \nicefrac{2}{3}$:} \\
            & \quad \text{$P_{111}$ is given}\\
            & \quad P_{x1x} = 
            \begin{dcases}
                1 - \frac{W_1 - W_x}{W_x} \cdot (1 - P_{111}, & \text{if $W_x > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\ 
            & \\
            & \text{if $W_1 \geq \nicefrac{2}{3}$:} \\
            & \quad \text{$P_{x1x}$ is given}\\
            & \quad P_{111} = 
            \begin{dcases}
                1 - \frac{W_x}{W_1 - W_x} \cdot (1 - P_{x1x}, & \text{if $(W_1 - W_x) > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\
            & \\
            & W_{x1x} = W_x \cdot P_{x1x} \\
            & W_{21x} = G_2 \cdot W_{x1x} \\
            & W_{31x} = W_{x1x} - W_{21x} \\
            & \\
            & W_{212} = G_3 \cdot W_{21x} \\
            & W_{213} = (1 - G_3) \cdot W_{21x} \\
            & W_{211} = W_{21} - W_{212} - W_{213} \\
            & \\
            & W_{312} = G_4 \cdot W_{31x} \\
            & W_{313} = (1 - G_4) \cdot W_{31x} \\
            & W_{311} = W_{31} - W_{312} - W_{313} \\
            & \\
            & W_{111} = W_{11} \cdot P_{111} \\
            & W_{112} = W_{12} - W_{212} - W_{312} \\
            & W_{112} = W_{13} - W_{213} - W_{313} \\
            & \\
            & \text{Calculate the remaining P using:} \\
            & P_{ijk} = 
            \begin{dcases}
                \frac{W_{ijk}}{W_{ij}}, & \text{if $W_{ij} > 0$} \\
                0, & \text{otherwise}
            \end{dcases} \\ 
        \end{align*}
        
    """

    # MODEL METADATA:
    class Meta(_AbstractProbability.Meta):
        store_id = "R2G3Model"
        ind_properties = [
            PropIntel(name="W1", label="W1 (> 0.5)", math_label=r"$W_1$",
                stor_name="_W1", inh_name="inherit_W1", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.5, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="P111_or_P212", label="P111 (W1 < 2/3) or\nPx1x (W1 > 2/3)",
                stor_name="_P111_or_P212", inh_name="inherit_P111_or_P212",
                inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$P_{111} %s$ or $\newline P_{x1x} %s$" % (
                mt_range(0.5, "W_1", 2.0 / 3.0),
                mt_range(2.0 / 3.0, "W_1", 1.0)),
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G1", label="W2/(W2+W3)", math_label=r"$\large\frac{W_2}{W_3 + W_2}$",
                stor_name="_G1", inh_name="inherit_G1", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G2", label="(W212+W213)/(W212+W213+W312+W313)",
                stor_name="_G2", inh_name="inherit_G2", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$\large\frac{W_{212} + W_{213}}{W_{212} + W_{213} + W_{312} + W_{313}}$",
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G3", label="W212/(W212+W213)",
                stor_name="_G3", inh_name="inherit_G3", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$\large\frac{W_{212}}{W_{212} + W_{213}}$",
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G4", label="W312/(W312+W313)",
                stor_name="_G4", inh_name="inherit_G4", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$\large\frac{W_{312}}{W_{312} + W_{313}}$",
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
    _G = 3
    twothirds = 2.0 / 3.0

    W1 = ProbabilityProperty(default=0.8, minimum=0.5, clamp=True, cast_to=float)
    inherit_W1 = ProbabilityProperty(default=False, cast_to=bool)

    P111_or_P212 = ProbabilityProperty(default=0.9, clamp=True, cast_to=float)
    inherit_P111_or_P212 = ProbabilityProperty(default=False, cast_to=bool)

    G1 = ProbabilityProperty(default=0.9, clamp=True, cast_to=float)
    inherit_G1 = ProbabilityProperty(default=False, cast_to=bool)

    G2 = ProbabilityProperty(default=0.9, clamp=True, cast_to=float)
    inherit_G2 = ProbabilityProperty(default=False, cast_to=bool)

    G3 = ProbabilityProperty(default=0.9, clamp=True, cast_to=float)
    inherit_G3 = ProbabilityProperty(default=False, cast_to=bool)

    G4 = ProbabilityProperty(default=0.9, clamp=True, cast_to=float)
    inherit_G4 = ProbabilityProperty(default=False, cast_to=bool)

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.8, P111_or_P212=0.9, G1=0.9, G2=0.9, G3=0.9, G4=0.9,
        inherit_W1=False, inherit_P111_or_P212=False, inherit_G1=False,
        inherit_G2=False, inherit_G3=False, inherit_G4=False, **kwargs):
        _AbstractProbability.setup(self, R=2)
        self.W1 = not_none(W1, 0.8)
        self.inherit_W1 = inherit_W1
        self.P111_or_P212 = not_none(P111_or_P212, 0.9)
        self.inherit_P111_or_P212 = inherit_P111_or_P212
        self.G1 = not_none(G1, 0.9)
        self.inherit_G1 = inherit_G1
        self.G2 = not_none(G2, 0.9)
        self.inherit_G2 = inherit_G2
        self.G3 = not_none(G3, 0.9)
        self.inherit_G3 = inherit_G3
        self.G4 = not_none(G4, 0.9)
        self.inherit_G4 = inherit_G4

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update(self):
        with self.data_changed.hold_and_emit():

            # calculate Wx's:
            self.mW[0] = self.W1
            self.mW[1] = (1.0 - self.mW[0]) * self.G1
            self.mW[2] = 1.0 - self.mW[0] - self.mW[1]

            # consequences of restrictions:
            self.mW[1, 1] = 0
            self.mW[1, 2] = 0
            self.mW[2, 1] = 0
            self.mW[2, 2] = 0
            self.mW[0, 1, 0] = self.mW[0, 1] = self.mW[1, 0] = self.mW[1]
            self.mW[0, 2, 0] = self.mW[0, 2] = self.mW[2, 0] = self.mW[2]
            self.mW[0, 0] = self.mW[0] - self.mW[0, 1] - self.mW[0, 2]

            # continue calculations:
            Wx = self.mW[1] + self.mW[2]
            if self.mW[0] < self.twothirds:
                self.mP[0, 0, 0] = self.P111_or_P212
                Px0x = 1 - (self.mW[0] - Wx) / Wx * (1 - self.mP[0, 0, 0]) if Wx != 0 else 0.0
            else:
                Px0x = self.P111_or_P212
                self.mP[0, 0, 0] = 1 - Wx / (self.mW[0] - Wx) * (1 - Px0x) if (self.mW[0] - Wx) != 0 else 0.0

            Wx0x = Wx * Px0x
            W10x = self.G2 * Wx0x
            W20x = Wx0x - W10x

            self.mW[1, 0, 1] = self.G3 * W10x
            self.mW[1, 0, 2] = (1 - self.G3) * W10x
            self.mW[1, 0, 0] = self.mW[1, 0] - self.mW[1, 0, 1] - self.mW[1, 0, 2]

            self.mW[2, 0, 1] = self.G4 * W20x
            self.mW[2, 0, 2] = (1 - self.G4) * W20x
            self.mW[2, 0, 0] = self.mW[2, 0] - self.mW[2, 0, 1] - self.mW[2, 0, 2]

            self.mW[0, 0, 0] = self.mW[0, 0] * self.mP[0, 0, 0]
            self.mW[0, 0, 1] = self.mW[0, 1] - self.mW[1, 0, 1] - self.mW[2, 0, 1]
            self.mW[0, 0, 2] = self.mW[0, 2] - self.mW[1, 0, 2] - self.mW[2, 0, 2]

            # Calculate remaining P:
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        self.mP[i, j, k] = self.mW[i, j, k] / self.mW[i, j] if self.mW[i, j] > 0 else 0.0

            self.solve()
            self.validate()

    pass # end of class
