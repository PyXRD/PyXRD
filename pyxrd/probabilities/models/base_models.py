# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from itertools import product

import numpy as np

from pyxrd.generic.io import Storable
from pyxrd.generic.models import DataModel
from pyxrd.generic.models.properties import IndexProperty

from pyxrd.generic.refinement.mixins import RefinementGroup
from pyxrd.generic.refinement.metaclasses import PyXRDRefinableMeta
from mvc import PropIntel

class _AbstractProbability(DataModel, Storable, RefinementGroup):

    # MODEL INTEL:
    __metaclass__ = PyXRDRefinableMeta
    class Meta(DataModel.Meta):
        independent_label_map = []
        properties = [
            PropIntel(name="name", inh_name=None, label="Probabilities", data_type=unicode),
            PropIntel(name="W_valid", inh_name=None, label="Valid W matrix", data_type=object),
            PropIntel(name="P_valid", inh_name=None, label="Valid P matrix", data_type=object),
        ]

    phase = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:
    name = "Probabilities"
    W_valid = None
    W_valid_mask = None
    P_valid = None
    P_valid_mask = None

    _R = -1
    @property
    def R(self):
        return self._R

    @property
    def rank(self):
        return self.G ** max(self.R, 1)

    _G = 0
    @property
    def G(self):
        return self._G

    _W = None
    _P = None

    @IndexProperty
    def mP(self, indeces):
        r, ind = self._get_Pxy_from_indeces(indeces)
        return self._lP[r][ind]
    @mP.setter
    def mP(self, indeces, value):
        r, ind = self._get_Pxy_from_indeces(indeces)
        self._lP[r][ind] = value

    @IndexProperty
    def mW(self, indeces):
        r, ind = self._get_Wxy_from_indeces(indeces)
        return self._lW[r][ind]
    @mW.setter
    def mW(self, indeces, value):
        r, ind = self._get_Wxy_from_indeces(indeces)
        self._lW[r][ind] = value

    # REFINEMENT GROUP IMPLEMENTATION:
    @property
    def refine_title(self):
        return self.name

    @property
    def refine_descriptor_data(self):
        return dict(
            phase_name=self.phase.name,
            component_name="*"
        )

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        my_kwargs = self.pop_kwargs(kwargs, *[names[0] for names in type(self).Meta.get_local_storable_properties()])
        super(_AbstractProbability, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        self.setup(**kwargs)
        self.update()

    def setup(self, R=-1, **kwargs):
        self._R = R
        self._create_matrices()

    def _create_matrices(self):
        """
            Creates a list of matrices for different 'levels' of R:
                e.g. when R=3 with g layers there can be 4 different W matrixes:
                    Wi = gxg matrix
                    Wij = g²xg² matrix
                    Wijk = g³xg³ matrix
                    Wijkl = another g³xg³ matrix (= Wijk * Pijkl)
                and 3 different P matrices:
                    Pij = gxg matrix
                    Pijk = g²xg² matrix
                    Pijkl = g³xg³ matrix
        """
        R = max(self.R, 1)
        self._lW = [None] * (R + 1)
        self._lP = [None] * R
        for r in range(R):
            lrank = self.G ** (r + 1)
            self._lW[r] = np.zeros(shape=(lrank, lrank), dtype=float)
            self._lP[r] = np.zeros(shape=(lrank, lrank), dtype=float)
        self._lW[-1] = np.zeros(shape=(lrank, lrank), dtype=float)
        self._W = self._lW[-2]
        self._P = self._lP[-1]

        # validity matrices:
        self.W_valid = np.array([False] * (R + 1))
        self.W_valid_mask = np.array([None] * (R + 1))
        self.P_valid = np.array([False] * R)
        self.P_valid_mask = np.array([None] * R)

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_prob_descriptions(self):
        for prop, name in self.Meta.independent_label_map: # @UnusedVariable
            yield "%s: %.3f" % (prop, getattr(self, prop))

    def update(self):
        raise NotImplementedError

    def _clamp_set_and_update(self, name, value, minimum=0.0, maximum=1.0):
        clamped = min(max(value, minimum), maximum)
        if getattr(self, name) != clamped:
            setattr(self, name, clamped)
            self.update()

    def solve(self):
        """
            This 'solves' the other W and P matrices using the 'top' P and W
            matrix calculated in the update method.
        """

        for num in range(1, self.R):
            # W matrices:
            for base in product(range(self.G), repeat=num):
                self.mW[base] = 0
                for i in range(self.G):
                    self.mW[base] += self.mW[(i,) + base]
            # P matrices:
            p_num = num + 1
            for base in product(range(self.G), repeat=p_num):
                W = self.mW[base[:-1]]
                self.mP[base] = self.mW[base] / W if W > 0 else 0.0

        # one extra W matrix:
        self._lW[-1][:] = np.dot(self._W, self._P)



    def validate(self):
        """
            Checks wether the calculated matrices are valid, and stores the
            validation results in 'masks': matrices of the same size, in which
            the values correspond with 1 minus the number of validation rules
            that specific W or P value has failed for.
        """
        def _validate_WW(W, R):
            """Validation rules for the product of a W and P matrix"""
            W_valid_mask = np.ones_like(W)
            rank = self.G ** max(R, 1)

            # sum of the cols (W...x's) need to equal W...
            for i in range(rank):
                if abs(np.sum(W[..., i]) - self._W[i, i]) > 1e4:
                    W_valid_mask[..., i] -= 1

            # sum of the entire matrix must equal one:
            if abs(np.sum(W) - 1.0) > 1e4:
                W_valid_mask -= 1

            # values need to be between 0 and 1
            for i in range(rank):
                for j in range(rank):
                    if W[i, j] < 0.0 or W[i, j] > 1.0:
                        W_valid_mask[i, i] -= 1

            # if the sum of the mask values equals the square of the rank,
            # no rules have been broken:
            W_valid = (np.sum(W_valid_mask) == rank ** 2)

            return W_valid, W_valid_mask

        def _validate_W(W, R):
            """Validation rules for a diagonal W matrix"""
            W_valid_mask = np.ones_like(W)
            rank = self.G ** max(R, 1)

            # sum of the diagonal nees to be one
            if abs(np.sum(W) - 1.0) > 1e6:
                for i in range(rank):
                    W_valid_mask[i, i] -= 1

            # values need to be between 0 and 1
            for i in range(rank):
                for j in range(rank):
                    if W[i, j] < 0.0 or W[i, j] > 1.0:
                        W_valid_mask[i, i] -= 1

            # if the sum of the mask values equals the square of the rank,
            # no rules have been broken:
            W_valid = (np.sum(W_valid_mask) == rank ** 2)

            return W_valid, W_valid_mask

        def _validate_P(P, R):
            P_valid_mask = np.ones_like(P)
            rank = self.G ** max(R, 1)

            # sum of the rows need to be one
            for i in range(rank):
                if abs(np.sum(P[i, ...]) - 1.0) > 1e6:
                    P_valid_mask[i, ...] -= 1

            # values need to be between 0 and 1
            for i in range(rank):
                for j in range(rank):
                    if P[i, j] < 0.0 or P[i, j] > 1.0:
                        P_valid_mask[i, j] -= 1

            # if the sum of the mask values equals the square of the rank,
            # no rules have been broken:
            P_valid = (np.sum(P_valid_mask) == rank ** 2)

            return P_valid, P_valid_mask

        for i in range(max(self.R, 1)):
            self.W_valid[i], self.W_valid_mask[i] = _validate_W(self._lW[i], i + 1)
            self.P_valid[i], self.P_valid_mask[i] = _validate_P(self._lP[i], i + 1)

        # the extra W matrix validates differently:
        self.W_valid[-1], self.W_valid_mask[-1] = _validate_WW(self._lW[-1], self.R)

    def _get_Pxy_from_indeces(self, indeces):
        if not hasattr(indeces, "__iter__"):
            indeces = [indeces]
        l = len(indeces)
        assert(l > 1), "Two or more indeces needed to acces P elements, not %s" % indeces
        assert(l <= max(self.R, 1) + 1), "Too many indeces for an R%d model: %s" % (self.R, indeces)
        R = max(l - 1, 1)
        x, y = 0, 0
        for i in range(1, R + 1):
            f = self.G ** (R - i)
            x += indeces[i - 1] * f
            y += indeces[i] * f
        return (l - 2), (x, y)

    def _get_Wxy_from_indeces(self, indeces):
        if not hasattr(indeces, "__iter__"):
            indeces = [indeces]
        l = len(indeces)
        assert(l > 0), "One or more indeces needed to acces W elements"
        assert(l <= max(self.R, 1) + 1), "Too many indeces for an R%d model: %s" % (self.R, indeces)
        if l == (max(self.R, 1) + 1):
            R = max(l - 1, 1)
            x, y = 0, 0
            for i in range(1, R + 1):
                f = self.G ** (R - i)
                x += indeces[i - 1] * f
                y += indeces[i] * f
            return (l - 1), (x, y)
        else:
            R = max(l, 1)
            x = 0
            for i in range(R):
                x += indeces[i] * self.G ** (R - (i + 1))
            return (l - 1), (x, x)

    def get_all_matrices(self): return self._lW, self._lP

    def get_distribution_matrix(self): return self._W

    def get_distribution_array(self): return np.diag(self._W)

    def get_probability_matrix(self): return self._P

    def get_independent_label_map(self): return self.Meta.independent_label_map

    pass # end of class
