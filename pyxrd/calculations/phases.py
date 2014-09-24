# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from pyxrd.generic.custom_math import mmult
from pyxrd.generic.caching import cache

from pyxrd.calculations.CSDS import calculate_distribution
from pyxrd.calculations.components import get_factors
import logging
logger = logging.getLogger(__name__)

@cache(64)
def get_structure_factors(range_stl, G, comp_list):
    """
        Calculates the structure factor and phase factor for:
        
            - range_stl: numpy array of 2*sin(θ) / λ values
            - G: the number of components (layer types)
            - comp_list: list of 
              :class:`~pyxrd.calculations.data_objects.ComponentData` instances
               
        This function calls :meth:`~pyxrd.calculations.components.get_factors`
        for each component in `comp_list` and stores the returned structure 
        factors and phase difference factors in a numpy array (of type complex)
        with shape (X, G) where X is expanded to fit the shape of `range_stl`.
    """
    shape = range_stl.shape + (G,)
    SF = np.zeros(shape, dtype=np.complex_)
    PF = np.zeros(shape, dtype=np.complex_)
    for i, comp in enumerate(comp_list):
        SF[:, i], PF[:, i] = get_factors.func(range_stl, comp) # @UndefinedVariable
    return SF, PF

@cache(64)
def get_Q_matrices(Q, CSDS_max):
    Qn = np.zeros((CSDS_max + 1,) + Q.shape, dtype=complex)
    Qn[0, ...] = np.copy(Q)
    for n in range(1, CSDS_max + 1):
        Qn[n, ...] = mmult(Qn[n - 1, ...], Q)
    return Qn

def get_absolute_scale(components, CSDS_real_mean, W):
    W = np.diag(W)
    mean_volume = 0.0
    mean_d001 = 0.0
    mean_density = 0.0

    for i, comp in enumerate(components):
        if comp != None:
            mean_volume += comp.volume * W[i]
            mean_d001 += comp.d001 * W[i]
            mean_density += (comp.weight * W[i] / comp.volume)
        else:
            logger.debug("- calc: get_absolute_scale reports: 'Zero observations found!'")

    mean_mass = (CSDS_real_mean * mean_volume ** 2 * mean_density)
    if mean_mass != 0.0:
        return mean_d001 / mean_mass
    else:
        return 0.0

@cache(64)
def get_diffracted_intensity(range_stl, phase):
    # Check probability model, if invalid return zeros instead of the actual pattern:
    if not phase.valid_probs:
        logger.debug("- calc: get_diffracted_intensity reports: 'Invalid probability found!'")
        return np.zeros_like(range_stl)
    else:
        # Calculate CSDS distribution
        CSDS_arr, CSDS_real_mean = calculate_distribution(phase.CSDS)

        # Get absolute scale
        abs_scale = get_absolute_scale(phase.components, CSDS_real_mean, phase.W)

        # Create a helper function to 'expand' certain arrays, for
        # results which are independent of the 2-theta range
        stl_dim = range_stl.shape[0]
        repeat_to_stl = lambda arr: np.repeat(arr[np.newaxis, ...], stl_dim, axis=0)

        # Repeat junction probabilities & weight fractions
        W = repeat_to_stl(phase.W).astype(np.complex_)
        P = repeat_to_stl(phase.P).astype(np.complex_)

        # Repeat & get SFa and SFb (transpose conjugate) structure factor matrices:
        SF, PF = get_structure_factors.func(range_stl, phase.G, phase.components)
        SFa = np.repeat(SF[..., np.newaxis, :], SF.shape[1], axis=1)
        SFb = np.transpose(np.conjugate(SFa), axes=(0, 2, 1))

        # Calculate the repetition factor for R+ probabilities:
        rank = P.shape[1]
        reps = rank / phase.G

        # Calculate the structure factor matrix:
        F = np.repeat(np.repeat(np.multiply(SFb, SFa), reps, axis=2), reps, axis=1)

        # Create Q phase factor matrices:
        PF = np.repeat(PF[..., np.newaxis, :], PF.shape[1], axis=1)
        Q = np.multiply(np.repeat(np.repeat(PF, reps, axis=2), reps, axis=1), P)
        Qn = get_Q_matrices.func(Q, phase.CSDS.maximum)

        # Calculate the intensity:
        sub_total = np.zeros(Q.shape, dtype=np.complex)
        for n in range(phase.CSDS.minimum, phase.CSDS.maximum + 1):
            progression_factor = 0
            for m in range(n + 1, phase.CSDS.maximum + 1):
                progression_factor += (m - n) * CSDS_arr[m]
            sub_total += 2 * progression_factor * Qn[n - 1, ...]

        CSDS_I = repeat_to_stl(np.identity(rank, dtype=np.complex) * CSDS_real_mean)
        sub_total = (CSDS_I + sub_total)
        sub_total = mmult(mmult(F, W), sub_total)
        intensity = np.real(np.trace(sub_total, axis1=2, axis2=1))

        return intensity * abs_scale
