# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.mvc import PropIntel

from pyxrd.generic.mathtext_support import mt_range
from pyxrd.generic.io import storables
from pyxrd.generic.utils import not_none

from .base_models import _AbstractProbability
from pyxrd.probabilities.models.properties import ProbabilityProperty

__all__ = [
    "R1G2Model",
    "R1G3Model",
    "R1G4Model",
]

@storables.register()
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

    # MODEL METADATA:
    class Meta(_AbstractProbability.Meta):
        ind_properties = [
            PropIntel(name="W1", label="W1", math_label=r"$W_1$",
                stor_name="_W1", inh_name="inherit_W1",
                inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="P11_or_P22", label="P11_or_P22",
                stor_name="_P11_or_P22", inh_name="inherit_P11_or_P22",
                inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$P_{11} %s$ or $\newline P_{22} %s$" % (
                    mt_range(0.0, "W_1", 0.5),
                    mt_range(0.5, "W_1", 1.0)),
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
        ]
        inh_properties = [
            PropIntel(name="inherit_%s" % prop.name, label="Inherit flag for %s" % prop.name,
                data_type=bool, refinable=False, storable=True, has_widget=True,
                widget_type="toggle") \
                for prop in ind_properties
        ]
        properties = ind_properties + inh_properties

        store_id = "R1G2Model"

    # PROPERTIES:
    _G = 2

    inherit_W1 = ProbabilityProperty(default=False, cast_to=bool)
    W1 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)

    inherit_P11_or_P22 = ProbabilityProperty(default=False, cast_to=bool)
    P11_or_P22 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.75, P11_or_P22=0.5, inherit_W1=False, inherit_P11_or_P22=False, **kwargs):
        _AbstractProbability.setup(self, R=1)
        self.W1 = not_none(W1, 0.75)
        self.inherit_W1 = inherit_W1
        self.P11_or_P22 = not_none(P11_or_P22, 0.5)
        self.inherit_P11_or_P22 = inherit_P11_or_P22

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update(self):
        with self.data_changed.hold_and_emit():
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

    # MODEL METADATA:
    class Meta(_AbstractProbability.Meta):
        ind_properties = [
            PropIntel(name="W1", label="W1", math_label=r"$W_1$",
                stor_name="_W1", inh_name="inherit_W1", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="P11_or_P22", label="P11_or_P22",
                stor_name="_P11_or_P22", inh_name="inherit_P11_or_P22",
                inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$P_{11} %s$ or $\newline P_{22} %s$" % (
                    mt_range(0.0, "W_1", 0.5),
                    mt_range(0.5, "W_1", 1.0)),
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G1", label="W2/(W2+W3)", math_label=r"$\large\frac{W_2}{W_3 + W_2}$",
                stor_name="_G1", inh_name="inherit_G1", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G2", label="(W22+W23)/(W22+W23+W32+W33)",
                stor_name="_G2", inh_name="inherit_G2", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$\large\frac{W_{22} + W_{23}}{W_{22} + W_{23} + W_{32} + W_{33}}$",
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G3", label="W22/(W22+W23)", math_label=r"$\large\frac{W_{22}}{W_{22} + W_{23}}$",
                stor_name="_G3", inh_name="inherit_G3", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G4", label="W23/(W32+W33)", math_label=r"$\large\frac{W_{22}}{W_{22} + W_{23}}$",
                stor_name="_G4", inh_name="inherit_G4", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID)
        ]
        inh_properties = [
            PropIntel(name="inherit_%s" % prop.name, label="Inherit flag for %s" % prop.name,
                data_type=bool, refinable=False, storable=True, has_widget=True,
                widget_type="toggle") \
                for prop in ind_properties
        ]
        properties = ind_properties + inh_properties
        store_id = "R1G3Model"

    # PROPERTIES
    _G = 3

    inherit_W1 = ProbabilityProperty(default=False, cast_to=bool)
    W1 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)

    inherit_P11_or_P22 = ProbabilityProperty(default=False, cast_to=bool)
    P11_or_P22 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)

    inherit_G1 = ProbabilityProperty(default=False, cast_to=bool)
    G1 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)

    inherit_G2 = ProbabilityProperty(default=False, cast_to=bool)
    G2 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)

    inherit_G3 = ProbabilityProperty(default=False, cast_to=bool)
    G3 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)

    inherit_G4 = ProbabilityProperty(default=False, cast_to=bool)
    G4 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.6, P11_or_P22=0.3, G1=0.5, G2=0.4, G3=0.5, G4=0.2,
            inherit_W1=False, inherit_P11_or_P22=False, inherit_G1=False,
            inherit_G2=False, inherit_G3=False, inherit_G4=False, **kwargs):
        _AbstractProbability.setup(self, R=1)
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

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update(self):
        with self.data_changed.hold_and_emit():
            G2inv = (1.0 / self.G2) - 1.0 if self.G2 > 0.0 else 0.0
            G3inv = (1.0 / self.G3) - 1.0 if self.G3 > 0.0 else 0.0
            G4inv = (1.0 / self.G4) - 1.0 if self.G4 > 0.0 else 0.0

            self.mW[0] = self.W1
            self.mW[1] = (1 - self.mW[0]) * self.G1
            self.mW[2] = 1.0 - self.mW[0] - self.mW[1]

            if self.mW[0] <= 0.5: # P00 given
                self.mP[0, 0] = self.P11_or_P22
                if self.mW[1] > 0.0:
                    self.mP[1, 1] = self.G2 * self.G3 * (self.mW[0] * (self.mP[0, 0] - 1.0) + self.mW[1] + self.mW[2]) / self.mW[1]
                else:
                    self.mP[1, 1] = 0.0
            else: # P11 given
                self.mP[0, 0] = 0.0 # mP[0,0] (aka P11) is derived further down
                self.mP[1, 1] = self.P11_or_P22

            self.mW[1, 1] = self.mP[1, 1] * self.mW[1]
            self.mW[1, 2] = self.mW[1, 1] * G3inv
            self.mW[2, 1] = self.G4 * G2inv * (self.mW[1, 1] + self.mW[1, 2])
            self.mW[2, 2] = G4inv * self.mW[2, 1]

            self.mP[1, 2] = (self.mW[1, 2] / self.mW[1]) if self.mW[1] > 0.0 else 0.0
            self.mP[1, 0] = 1 - self.mP[1, 1] - self.mP[1, 2]

            self.mP[2, 1] = (self.mW[2, 1] / self.mW[2]) if self.mW[2] > 0.0 else 0.0
            self.mP[2, 2] = (self.mW[2, 2] / self.mW[2]) if self.mW[2] > 0.0 else 0.0
            self.mP[2, 0] = 1 - self.mP[2, 1] - self.mP[2, 2]

            self.mP[0, 1] = ((self.mW[1] - self.mW[1, 1] - self.mW[2, 1]) / self.mW[0]) if self.mW[0] > 0.0 else 0.0
            self.mP[0, 2] = ((self.mW[2] - self.mW[1, 2] - self.mW[2, 2]) / self.mW[0]) if self.mW[0] > 0.0 else 0.0

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
    """
    Reichweite = 1 / Components = 4
    g*(g-1) independent variables = 12
    
    W0
    W1/(W1+W2+W3) = R1
    W2/(W2+W3) = R2

    P00 (W0<0,5) of P11 (W0>0,5)
    (W11+W12+W13) / sum{i:1-3;j:1-3}(Wij) = G1
    (W21+W22+W23) / sum{i:2-3;j:1-3}(Wij) = G2
    
    W11 / (W11 + W12 + W13) = G11
    W12/(W12+W13) = G12
    
    W21 / (W21 + W22 + W23) = G21
    W22/(W22+W23) = G22
    
    W31 / (W31 + W32 + W33) = G31
    W32/(W32+W33) = G32
        
    indexes are NOT zero-based in external property names!
    """

    # MODEL METADATA:
    class Meta(_AbstractProbability.Meta):
        ind_properties = [
            PropIntel(name="W1", label="W1", math_label=r"$W_1$",
                stor_name="_W1", inh_name="inherit_W1", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="P11_or_P22", label="P11_or_P22",
                stor_name="_P11_or_P22", inh_name="inherit_P11_or_P22", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$P_{11} %s$ or $\newline P_{22} %s$" % (
                    mt_range(0.0, "W_1", 0.5),
                    mt_range(0.5, "W_1", 1.0)),
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="R1", label="W2/(W2+W3+W4)", math_label=r"$\large\frac{W_2}{W_2 + W_3 + W_4}$",
                stor_name="_R1", inh_name="inherit_R1", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="R2", label="W3)/(W3+W4)", math_label=r"$\large\frac{W_3}{W_3 + W_4}$",
                stor_name="_R2", inh_name="inherit_R2", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G1", label="(W22+W23+W24)/(W22+W23+W24+W32+W33+W34+W42+W43+W44)",
                stor_name="_G1", inh_name="inherit_G1", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$\large\frac{\sum_{j=2}^{4} W_{2j}}{\sum_{i=2}^{4} \sum_{j=2}^{4} W_{ij}}$",
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G2", label="(W32+W33+W34)/(W32+W33+W34+W42+W43+W44)",
                stor_name="_G2", inh_name="inherit_G2", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$\large\frac{\sum_{j=2}^{4} W_{3j}}{\sum_{i=3}^{4} \sum_{j=2}^{4} W_{ij}}$",
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G11", label="W22/(W22+W23+W24)",
                stor_name="_G11", inh_name="inherit_G11", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$\large\frac{W_{22}}{\sum_{j=2}^{4} W_{2j}}$",
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G12", label="W23/(W23+W24)",
                stor_name="_G12", inh_name="inherit_G12", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$\large\frac{W_{23}}{\sum_{j=3}^{4} W_{2j}}$",
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G21", label="W32/(W32+W33+W34)",
                stor_name="_G21", inh_name="inherit_G21", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$\large\frac{W_{32}}{\sum_{j=2}^{4} W_{3j}}$",
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G22", label="W33/(W32+W34)",
                stor_name="_G22", inh_name="inherit_G22", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$\large\frac{W_{33}}{\sum_{j=3}^{4} W_{3j}}$",
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G31", label="W42/(W42+W43+W44)",
                stor_name="_G31", inh_name="inherit_G31", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$\large\frac{W_{42}}{\sum_{j=2}^{4} W_{4j}}$",
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="G32", label="W43/(W43+W44)",
                stor_name="_G32", inh_name="inherit_G32", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$\large\frac{W_{43}}{\sum_{j=3}^{4} W_{4j}}$",
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID)
        ]
        inh_properties = [
            PropIntel(name="inherit_%s" % prop.name, label="Inherit flag for %s" % prop.name,
                data_type=bool, refinable=False, storable=True, has_widget=True,
                widget_type="toggle") \
                for prop in ind_properties
        ]
        properties = ind_properties + inh_properties
        store_id = "R1G4Model"

    # PROPERTIES
    _G = 4

    inherit_W1 = ProbabilityProperty(default=False, cast_to=bool)
    W1 = ProbabilityProperty(default=0.6, clamp=True, cast_to=float)

    inherit_P11_or_P22 = ProbabilityProperty(default=False, cast_to=bool)
    P11_or_P22 = ProbabilityProperty(default=0.25, clamp=True, cast_to=float)

    inherit_R1 = ProbabilityProperty(default=False, cast_to=bool)
    R1 = ProbabilityProperty(default=0.5, clamp=True, cast_to=float)

    inherit_R2 = ProbabilityProperty(default=False, cast_to=bool)
    R2 = ProbabilityProperty(default=0.5, clamp=True, cast_to=float)

    inherit_G1 = ProbabilityProperty(default=False, cast_to=bool)
    G1 = ProbabilityProperty(default=0.5, clamp=True, cast_to=float)

    inherit_G2 = ProbabilityProperty(default=False, cast_to=bool)
    G2 = ProbabilityProperty(default=0.4, clamp=True, cast_to=float)

    inherit_G11 = ProbabilityProperty(default=False, cast_to=bool)
    G11 = ProbabilityProperty(default=0.5, clamp=True, cast_to=float)

    inherit_G12 = ProbabilityProperty(default=False, cast_to=bool)
    G12 = ProbabilityProperty(default=0.2, clamp=True, cast_to=float)

    inherit_G21 = ProbabilityProperty(default=False, cast_to=bool)
    G21 = ProbabilityProperty(default=0.80, clamp=True, cast_to=float)

    inherit_G22 = ProbabilityProperty(default=False, cast_to=bool)
    G22 = ProbabilityProperty(default=0.75, clamp=True, cast_to=float)

    inherit_G31 = ProbabilityProperty(default=False, cast_to=bool)
    G31 = ProbabilityProperty(default=0.7, clamp=True, cast_to=float)

    inherit_G32 = ProbabilityProperty(default=False, cast_to=bool)
    G32 = ProbabilityProperty(default=0.5, clamp=True, cast_to=float)

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.6, P11_or_P22=0.25, R1=0.5, R2=0.5, G1=0.5, G2=0.4,
            G11=0.5, G12=0.2, G21=0.8, G22=0.75, G31=0.7, G32=0.5,
            inherit_W1=False, inherit_P11_or_P22=False, inherit_R1=False,
            inherit_R2=False, inherit_G1=False, inherit_G2=False,
            inherit_G11=False, inherit_G12=False, inherit_G21=False,
            inherit_G22=False, inherit_G31=False, inherit_G32=False, **kwargs):
        _AbstractProbability.setup(self, R=1)
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
        self.G12 = not_none(G12, 0.2)
        self.inherit_G12 = inherit_G12
        self.G21 = not_none(G21, 0.8)
        self.inherit_G21 = inherit_G21
        self.G22 = not_none(G22, 0.75)
        self.inherit_G22 = inherit_G22
        self.G31 = not_none(G31, 0.7)
        self.inherit_G31 = inherit_G31
        self.G32 = not_none(G32, 0.5)
        self.inherit_G32 = inherit_G32


    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update(self):
        with self.data_changed.hold_and_emit():
            G1inv = (1.0 / self.G1) - 1.0 if self.G1 > 0 else 0.0

            G11inv = (1.0 / self.G11) - 1.0 if self.G11 > 0 else 0.0
            # G21inv = (1.0 / self.G21) - 1.0 if self.G21 > 0 else 0.0
            # G31inv = (1.0 / self.G31) - 1.0 if self.G31 > 0 else 0.0

            self.mW[0] = self.W1
            self.mW[1] = (1.0 - self.mW[0]) * self.R1
            self.mW[2] = (1.0 - self.mW[0] - self.mW[1]) * self.R2
            self.mW[3] = 1.0 - self.mW[0] - self.mW[1] - self.mW[2]

            W0inv = 1.0 / self.mW[0] if self.mW[0] > 0.0 else 0.0
            W1inv = 1.0 / self.mW[1] if self.mW[1] > 0.0 else 0.0
            W2inv = 1.0 / self.mW[1] if self.mW[1] > 0.0 else 0.0
            W3inv = 1.0 / self.mW[1] if self.mW[1] > 0.0 else 0.0

            if self.mW[0] < 0.5: # P11 is given
                self.mP[0, 0] = self.P11_or_P22
                self.mW[0, 0] = self.mW[0] * self.mP[0, 0]
                if (self.mW[1] * self.G1) > 0.0:
                    self.mP[1, 1] = self.G1 * self.G2 * (self.mW[0, 0] - 2 * self.mW[0] + 1.0)
                else:
                    self.mP[1, 1] = 0.0
            else: # P22 is given
                self.mP[0, 0] = 0.0 # mP[0,0] (aka P11) is derived further down
                self.mP[1, 1] = self.P11_or_P22

            self.mW[1, 1] = self.mP[1, 1] * self.mW[1]
            self.mW[1, 2] = self.mW[1, 1] * G11inv * self.G12
            self.mW[1, 3] = self.mW[1, 1] * G11inv * (1.0 - self.G12)
            SBi = self.mW[1, 1] + self.mW[1, 2] + self.mW[1, 3]

            SCi = G1inv * self.G2 * SBi
            self.mW[2, 1] = SCi * self.G21
            self.mW[2, 2] = (SCi - self.mW[2, 1]) * self.G22
            self.mW[2, 3] = SCi - self.mW[2, 1] - self.mW[2, 2]

            SDi = G1inv * (1.0 - self.G2) * SBi
            self.mW[3, 1] = SDi * self.G31
            self.mW[3, 2] = (SDi - self.mW[3, 1]) * self.G32
            self.mW[3, 3] = SDi - self.mW[3, 1] - self.mW[3, 2]

            self.mP[1, 2] = self.mW[1, 2] * W1inv
            self.mP[1, 3] = self.mW[1, 3] * W1inv
            self.mP[1, 0] = 1 - self.mP[1, 1] - self.mP[1, 2] - self.mP[1, 3]

            self.mP[2, 1] = self.mW[2, 1] * W2inv
            self.mP[2, 2] = self.mW[2, 2] * W2inv
            self.mP[2, 3] = self.mW[2, 3] * W2inv
            self.mP[2, 0] = 1 - self.mP[2, 1] - self.mP[2, 2] - self.mP[2, 3]

            self.mP[3, 1] = self.mW[3, 1] * W3inv
            self.mP[3, 2] = self.mW[3, 2] * W3inv
            self.mP[3, 3] = self.mW[3, 3] * W3inv
            self.mP[3, 0] = 1 - self.mP[3, 1] - self.mP[3, 2] - self.mP[3, 3]

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