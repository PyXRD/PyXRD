# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.mvc import PropIntel
from pyxrd.generic.mathtext_support import mt_range
from pyxrd.generic.io import storables

from .base_models import _AbstractProbability
from pyxrd.probabilities.models.properties import ProbabilityProperty

__all__ = [
    "R2G2Model",
    "R2G3Model"
]

@storables.register()
class R2G2Model(_AbstractProbability):
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

    # MODEL METADATA:
    class Meta(_AbstractProbability.Meta):
        store_id = "R2G2Model"
        ind_properties = [
            PropIntel(name="W1", label="W1", math_label=r"$W_1$",
                stor_name="_W1", inh_name="inherit_W1", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="P112_or_P211", label="P112_or_P211",
                stor_name="_P112_or_P211", inh_name="inherit_P112_or_P211",
                 inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$P_{112} %s$ or $\newlineP_{211} %s$" % (
                    mt_range(0.0, "W_1", 2.0 / 3.0),
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
            self.W1 = W1
            self.inherit_W1 = inherit_W1
            self.P112_or_P211 = P112_or_P211
            self.inherit_P112_or_P211 = inherit_P112_or_P211
            self.P21 = P21
            self.inherit_P21 = inherit_P21
            self.P122_or_P221 = P122_or_P221
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
    """
    Reichweite = 2 / Components = 3
    independent variables = 6 -> restricted model!
    W0
    W1 / (W1 + W2) = G1
    P000 (0.5<W0<2/3) of P101 (2/3<W0<1)
    (W101+W102) / (W101+W102+W201+W202) = G2
    W101 / (W101+W102) = G3
    W201 / (W201+W202) = G4
    
    Restriction:
    - no 1 or 2 type layer can follow or precede another 1 or 2 type layer:
    P11 = P12 = 0
    P10 = 1
    P21 = P22 = 0
    P20 = 1
    
    P011 = P012 = 0
    P010 = 1
    P021 = P022 = 0
    P020 = 1
    P111 = P112 = 0
    P110 = 1
    P121 = P122 = 0
    P120 = 1
    P211 = P212 = 0
    P210 = 1
    P221 = P222 = 0
    P220 = 1
    
    Consequences:
    - weight fraction of a type X layer following or preceding a type 0 layer
      equals the weight fraction of (single) X type layers:
    W10 = W01 = W1
    W20 = W02 = W2
    W00 = W0
    
    W1 = G1 * (1 - W0)
    W2 = 1 - W0 - W1
    
    If P000 given:
        P101 = (G2*G1 / W1) * [W00*(P000-1)+2]
        
    P102 = P101 * (1/G3 - 1)
    W101 = P101 * W10 = P101 * W1
    W102 = P102 * W1
    W100 = 1 - W101 - W102
    
    W201 + W202 = (1-G2) / (G2*G3) * W101
    W201 = G4 * (W201+W202)
    W202 = (1/G4 - 1) * W201
    W200 = 1 - W201 - W202
    
    W000 = W00 - W100 - W200
    W001 = W01 - W101 - W201
    W002 = 1 - W000 - W001
    
    Pxxx's are calculated from dividing Wxxx's with Wx's
    
    indexes are NOT zero-based in external property names!
    """

    # MODEL METADATA:
    class Meta(_AbstractProbability.Meta):
        store_id = "R2G3Model"
        ind_properties = [
            PropIntel(name="W1", label="W1", math_label=r"$W_1$",
                stor_name="_W1", inh_name="inherit_W1", inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                minimum=0.0, maximum=1.0, data_type=float, **PropIntel.REF_ST_WID),
            PropIntel(name="P111_or_P212", label="P111_or_P212",
                stor_name="_P111_or_P212", inh_name="inherit_P111_or_P212",
                inh_from="parent.based_on.probabilities",
                is_independent=True, # flag for the view creation
                math_label=r"$P_{111} %s$ or $\newline P_{212} %s$" % (
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

    W1 = ProbabilityProperty(default=0.75, minimum=0.5, clamp=True, cast_to=float)
    inherit_W1 = ProbabilityProperty(default=False, cast_to=bool)

    P111_or_P212 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)
    inherit_P111_or_P212 = ProbabilityProperty(default=False, cast_to=bool)

    G1 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)
    inherit_G1 = ProbabilityProperty(default=False, cast_to=bool)

    G2 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)
    inherit_G2 = ProbabilityProperty(default=False, cast_to=bool)

    G3 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)
    inherit_G3 = ProbabilityProperty(default=False, cast_to=bool)

    G4 = ProbabilityProperty(default=0.0, clamp=True, cast_to=float)
    inherit_G4 = ProbabilityProperty(default=False, cast_to=bool)

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.75, P111_or_P212=0.5, G1=0.5, G2=0.5, G3=0.5, G4=0.5,
        inherit_W1=False, inherit_P111_or_P212=False, inherit_G1=False,
        inherit_G2=False, inherit_G3=False, inherit_G4=False, **kwargs):
        _AbstractProbability.setup(self, R=2)
        self.W1 = W1
        self.inherit_W1 = inherit_W1
        self.P111_or_P212 = P111_or_P212
        self.inherit_P111_or_P212 = inherit_P111_or_P212
        self.G1 = G1
        self.inherit_G1 = inherit_G1
        self.G2 = G2
        self.inherit_G2 = inherit_G2
        self.G3 = G3
        self.inherit_G3 = inherit_G3
        self.G4 = G4
        self.inherit_G4 = inherit_G4

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update(self):
        with self.data_changed.hold_and_emit():
            # G2inv = (1.0 / self.G2) - 1.0 if self.G2 > 0 else 0.0
            # G3inv = (1.0 / self.G3) - 1.0 if self.G3 > 0 else 0.0
            # G4inv = (1.0 / self.G4) - 1.0 if self.G4 > 0 else 0.0

            # calculate Wx's (0-based!!):
            self.mW[0] = self.W1
            self.mW[1] = (1.0 - self.mW[0]) * self.G1
            self.mW[2] = 1.0 - self.mW[0] - self.mW[1]

            # consequences of restrictions:
            self.mW[1, 0] = self.mW[0, 1] = self.mW[1]
            self.mW[2, 0] = self.mW[0, 2] = self.mW[2]
            self.mW[0, 0] = 2.0 * self.mW[0] - 1.0

            # continue calculations:
            if self.mW[0] < self.twothirds:
                self.mP[0, 0, 0] = self.P111_or_P212
                if self.mW[1] == 0:
                    self.mP[1, 0, 1] = 0.0
                else:
                    self.mP[1, 0, 1] = self.G2 * self.G3 * (self.mW[0, 0] * (self.mP[0, 0, 0] - 1.0) + 2.0) / self.mW[1]
            else:
                self.mP[1, 0, 1] = self.P111_or_P212
            self.mP[1, 0, 2] = (self.mP[1, 0, 1] * ((1.0 / self.G3) - 1.0)) if self.G3 > 0 else 1.0
            # self.mP[0,0,0] = 1.0 - self.mP[1,0,1] - self.mP[1,0,2]

            self.mW[1, 0, 1] = self.mP[1, 0, 1] * self.mW[1]
            self.mW[1, 0, 2] = self.mP[1, 0, 2] * self.mW[1]
            self.mW[1, 0, 0] = self.mW[1, 0] - self.mW[1, 0, 1] - self.mW[1, 0, 2]

            self.mW[2, 0, 1] = (self.G4 * (1.0 - self.G2) / (self.G2 * self.G3) * self.mW[1, 0, 1]) if (self.G2 * self.G3) > 0 else 0.0
            self.mW[2, 0, 2] = (self.mW[2, 0, 1] * ((1.0 / self.G4) - 1.0)) if self.G4 > 0 else 1.0
            self.mW[2, 0, 0] = self.mW[2, 0] - self.mW[2, 0, 1] - self.mW[2, 0, 2]
            for i in range(3):
                self.mP[2, 0, i] = self.mW[2, 0, i] / self.mW[2, 0] if self.mW[2, 0] > 0 else 0.0

            self.mW[0, 0, 0] = self.mW[0, 0] - self.mW[1, 0, 0] - self.mW[2, 0, 0]
            self.mW[0, 0, 1] = self.mW[0, 1] - self.mW[1, 0, 1] - self.mW[2, 0, 1]
            self.mW[0, 0, 2] = self.mW[0, 2] - self.mW[1, 0, 2] - self.mW[2, 0, 2]
            for i in range(3):
                self.mP[0, 0, i] = self.mW[0, 0, i] / self.mW[0, 0] if self.mW[0, 0] > 0 else 0.0
                pass

            # restrictions:
            for i in range(3):
                for j in range(1, 3):
                    for k in range(3):
                        self.mP[i, j, k] = 0.0 if k > 0 else 1.0

            self.solve()
            self.validate()

    pass # end of class
