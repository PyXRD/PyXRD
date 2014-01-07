# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.gtkmvc.support.propintel import PropIntel

from pyxrd.generic.mathtext_support import mt_range
from pyxrd.generic.io import storables
from pyxrd.probabilities.base_models import _AbstractProbability


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
        independent_label_map = [
            ("W1", r"$W_1$", [0.0, 1.0, ]),
            ("P11_or_P22", r"$P_{11} %s$ or $\newline P_{22} %s$" % (
                mt_range(0.0, "W_1", 0.5),
                mt_range(0.5, "W_1", 1.0)),
             [0.0, 1.0, ]),
         ]
        properties = [
            PropIntel(name=prop, label=label, minimum=0.0, maximum=1.0, data_type=float, refinable=True, storable=True, has_widget=True) \
                for prop, label, range in independent_label_map
        ]
        store_id = "R1G2Model"

    # PROPERTIES:
    def get_W1(self): return self.mW[0]
    def set_W1(self, value):
        value = min(max(value, 0.0), 1.0)
        if value != self.mW[0]:
            self.mW[0] = value
            self.update()

    _P00_P11 = 0.0
    def get_P11_or_P22(self): return self._P00_P11
    def set_P11_or_P22(self, value):  self._clamp_set_and_update("_P00_P11", value)

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.25, P11_or_P22=0.5, **kwargs):
        _AbstractProbability.setup(self, R=1)
        self.W1 = W1
        self.P11_or_P22 = P11_or_P22

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update(self):
        with self.data_changed.hold_and_emit():
            self.mW[1] = 1.0 - self.mW[0]
            if self.mW[0] <= 0.5:
                self.mP[0, 1] = 1.0 - self.mP[0, 0]
                self.mP[1, 0] = self.mW[0] * self.mP[0, 1] / self.mW[1]
                self.mP[1, 1] = 1.0 - self.mP[1, 0]
            else:
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
        independent_label_map = [
            ("W1", r"$W_1$", [0.0, 1.0, ]),
            ("P11_or_P22", r"$P_{11} %s$ or $\newline P_{22} %s$" % (
                mt_range(0.0, "W_1", 0.5),
                mt_range(0.5, "W_1", 1.0)),
             [0.0, 1.0, ]
            ),
            ("G1", r"$\large\frac{W_2}{W_3 + W_2}$", [0.0, 1.0, ]),
            ("G2", r"$\large\frac{W_{22} + W_{23}}{W_{22} + W_{23} + W_{32} + W_{33}}$", [0.0, 1.0, ]),
            ("G3", r"$\large\frac{W_{22}}{W_{22} + W_{23}}$", [0.0, 1.0, ]),
            ("G4", r"$\large\frac{W_{32}}{W_{32} + W_{33}}$", [0.0, 1.0, ]),
        ]
        properties = [
            PropIntel(name=prop, label=label, minimum=minimum, maximum=maximum, data_type=float, refinable=True, storable=True, has_widget=True) \
                for prop, label, (minimum, maximum) in independent_label_map
        ]
        store_id = "R1G3Model"

    # PROPERTIES
    def get_W1(self): return self.mW[0]
    def set_W1(self, value):
        value = min(max(value, 0.0), 1.0)
        if value != self.mW[0]:
            self.mW[0] = value
            self.update()

    _P00_P11 = 0.0
    def get_P11_or_P22(self): return self._P00_P11
    def set_P11_or_P22(self, value):  self._clamp_set_and_update("_P00_P11", value)

    _G1 = 0.0
    def get_G1(self): return self._G1
    def set_G1(self, value): self._clamp_set_and_update("_G1", value)

    _G2 = 0
    def get_G2(self): return self._G2
    def set_G2(self, value): self._clamp_set_and_update("_G2", value)

    _G3 = 0
    def get_G3(self): return self._G3
    def set_G3(self, value): self._clamp_set_and_update("_G3", value)

    _G4 = 0
    def get_G4(self): return self._G4
    def set_G4(self, value): self._clamp_set_and_update("_G4", value)

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.6, P11_or_P22=0.3, G1=0.5, G2=0.4, G3=0.5, G4=0.2, **kwargs):
        _AbstractProbability.setup(self, R=1)
        self.W1 = W1
        self.P11_or_P22 = P11_or_P22
        self.G1 = G1
        self.G2 = G2
        self.G3 = G3
        self.G4 = G4

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
        independent_label_map = [
            ("W1", r"$W_1$", [0.0, 1.0]),
            ("R1", r"$\large\frac{W_2}{W_2 + W_3 + W_4}$", [0.0, 1.0]),
            ("R2", r"$\large\frac{W_3}{W_3 + W_4}$", [0.0, 1.0]),
            ("P11_or_P22",
             r"$P_{11} %s$ or $\newline P_{22} %s$" % (
                mt_range(0.0, "W_1", 0.5),
                mt_range(0.5, "W_1", 1.0)
             ), [0.0, 1.0]),
            ("G1", r"$\large\frac{\sum_{j=2}^{4} W_{2j}}{\sum_{i=2}^{4} \sum_{j=2}^{4} W_{ij}}$", [0.0, 1.0]),
            ("G2", r"$\large\frac{\sum_{j=2}^{4} W_{3j}}{\sum_{i=3}^{4} \sum_{j=2}^{4} W_{ij}}$", [0.0, 1.0]),
            ("G11", r"$\large\frac{W_{22}}{\sum_{j=2}^{4} W_{2j}}$", [0.0, 1.0]),
            ("G12", r"$\large\frac{W_{23}}{\sum_{j=3}^{4} W_{2j}}$", [0.0, 1.0]),
            ("G21", r"$\large\frac{W_{32}}{\sum_{j=2}^{4} W_{3j}}$", [0.0, 1.0]),
            ("G22", r"$\large\frac{W_{33}}{\sum_{j=3}^{4} W_{3j}}$", [0.0, 1.0]),
            ("G31", r"$\large\frac{W_{42}}{\sum_{j=2}^{4} W_{4j}}$", [0.0, 1.0]),
            ("G32", r"$\large\frac{W_{43}}{\sum_{j=3}^{4} W_{4j}}$", [0.0, 1.0]),
        ]
        properties = [
            PropIntel(name=prop, label=label, minimum=rng[0], maximum=rng[1], data_type=float, refinable=True, storable=True, has_widget=True) \
                for prop, label, rng in independent_label_map
        ]
        store_id = "R1G4Model"

    # PROPERTIES
    _W0 = 0.0
    def get_W1(self): return self._W0
    def set_W1(self, value): self._clamp_set_and_update("_W0", value)

    _P00_P11 = 0.0
    def get_P11_or_P22(self): return self._P00_P11
    def set_P11_or_P22(self, value): self._clamp_set_and_update("_P00_P11", value)

    _R1 = 0
    def get_R1(self): return self._R1
    def set_R1(self, value): self._clamp_set_and_update("_R1", value)

    _R2 = 0
    def get_R2(self): return self._R2
    def set_R2(self, value): self._clamp_set_and_update("_R2", value)

    _G1 = 0
    def get_G1(self): return self._G1
    def set_G1(self, value): self._clamp_set_and_update("_G1", value)

    _G2 = 0
    def get_G2(self): return self._G2
    def set_G2(self, value): self._clamp_set_and_update("_G2", value)

    _G11 = 0
    def get_G11(self): return self._G11
    def set_G11(self, value): self._clamp_set_and_update("_G11", value)

    _G12 = 0
    def get_G12(self): return self._G12
    def set_G12(self, value): self._clamp_set_and_update("_G12", value)

    _G21 = 0
    def get_G21(self): return self._G21
    def set_G21(self, value): self._clamp_set_and_update("_G21", value)

    _G22 = 0
    def get_G22(self): return self._G22
    def set_G22(self, value): self._clamp_set_and_update("_G22", value)

    _G31 = 0
    def get_G31(self): return self._G31
    def set_G31(self, value): self._clamp_set_and_update("_G31", value)

    _G32 = 0
    def get_G32(self): return self._G32
    def set_G32(self, value): self._clamp_set_and_update("_G32", value)

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def setup(self, W1=0.6, P11_or_P22=0.25, R1=0.5, R2=0.5, G1=0.5, G2=0.4,
            G11=0.5, G12=0.2, G21=0.8, G22=0.75, G31=0.7, G32=0.5, **kwargs):
        _AbstractProbability.setup(self, R=1)
        self.W1 = W1
        self.P11_or_P22 = P11_or_P22
        self.R1 = R1
        self.R2 = R2
        self.G1 = G1
        self.G2 = G2
        self.G11 = G11
        self.G12 = G12
        self.G21 = G21
        self.G22 = G22
        self.G31 = G31
        self.G32 = G32


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
