# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import time
from itertools import izip

import numpy as np
from scipy.optimize import fmin_l_bfgs_b

from pyxrd.data import settings
settings.apply_runtime_settings()
import logging
logger = logging.getLogger(__name__)

from .specimen import get_phase_intensities
from .exceptions import wrap_exceptions
from .statistics import Rp, Rpder

__residual_method_map = {
    "Rp" : Rp,
    "Rpder": Rpder
}

def parse_solution(x, mixture):
    fractions = np.asanyarray(x[:mixture.m])[:, np.newaxis]
    scales = np.asanyarray(x[mixture.m:mixture.m + mixture.n])
    if mixture.auto_bg:
        bgshifts = np.asanyarray(x[-mixture.n:])
    else:
        bgshifts = mixture.bgshifts
    return fractions, scales, bgshifts

def get_solution(mixture):
    if mixture.auto_bg:
        return np.concatenate((mixture.fractions, mixture.scales, mixture.bgshifts))
    else:
        return np.concatenate((mixture.fractions, mixture.scales))

def get_zero_solution(mixture):
    if mixture.auto_bg:
        x0 = np.ones(shape=(mixture.m + mixture.n * 2,))
        x0[-mixture.n:] = 0.0 # set bg at zero
    else:
        x0 = np.ones(shape=(mixture.m + mixture.n * 1,))
    x0[:mixture.m] = 1.0 / mixture.m
    return x0

def _get_residuals(x, mixture):
    fractions, scales, bgshifts = parse_solution(x, mixture)
    rps = [0.0, ]
    for scale, bgshift, specimen in izip(scales, bgshifts, mixture.specimens):
        if specimen is not None:
            if specimen.phase_intensities is not None:
                calc = (scale * np.sum(specimen.phase_intensities * fractions, axis=0)) + bgshift
            else:
                logger.warning("_get_residual reports: 'No phases found!'")
                calc = np.zeros_like(specimen.observed_intensity)
            if specimen.observed_intensity.size > 0:
                exp = specimen.observed_intensity[specimen.selected_range]
                cal = calc[specimen.selected_range]
                rp = __residual_method_map[settings.RESIDUAL_METHOD](exp, cal)
                rps.append(rp)
            else:
                logger.warning("_get_residual reports: 'Zero observations found!'")
        else:
            logger.warning("_get_residual reports: 'None found!'")
    rps[0] = np.average(rps[1:])
    return tuple(rps)

def _get_average_residual(x, mixture):
    return _get_residuals(x, mixture)[0]

def get_residual(mixture, parsed=False):
    parse_mixture(mixture, parsed=parsed)
    return _get_residuals(get_solution(mixture), mixture)

def parse_mixture(mixture, parsed=False):
    if not parsed:
        # Sanity check:
        n = len(mixture.specimens)
        assert n > 0, "Need at least 1 specimen to optimize phase fractions, scales and background."
        m = 0
        for specimen in mixture.specimens:
            if specimen is not None:
                m = len(specimen.phases)
                break
        assert m > 0, "Need at least 1 phase in each specimen to optimize phase fractions, scales and background."

        mixture.n = n
        mixture.m = m

        for specimen in mixture.specimens:
            if specimen is not None:
                specimen.phase_intensities = get_phase_intensities(specimen)
            else:
                logger.warning("parse_mixture reports: 'None found!'")

@wrap_exceptions
def optimize_mixture(mixture, parsed=False):
    """
        Optimizes the mixture fractions, scales and bg shifts.
        Returns the mixture data object.
    """
    # 0. Calculate phase intensitities
    try:
        parse_mixture(mixture, parsed=parsed)
    except AssertionError:
        if settings.DEBUG:
            raise
        return mixture # ignore and return the original object back

    # 1. setup start point:
    x0 = get_zero_solution(mixture)
    bounds = [(0, None) for i in range(len(x0))] # @UnusedVariable

    # 2. Optimize:
    t1 = time.time()
    lastx, residual, info = fmin_l_bfgs_b(
        _get_average_residual,
        x0,
        args=(mixture,),
        approx_grad=True,
        bounds=bounds,
        iprint=-1
    )

    t2 = time.time()
    logger.debug('%s took %0.3f ms' % ("optimize_mixture", (t2 - t1) * 1000.0))
    logger.debug(' Solution: %s' % lastx)
    logger.debug(' Average residual: %s' % residual)
    logger.debug(' Info dict: %s' % info)

    # 3. rescale scales and fractions so they fit into [0-1] range,
    #    and round them to have 6 digits max:
    fractions, scales, bgshifts = parse_solution(lastx, mixture)
    fractions = fractions.flatten()
    # if mixture.BGSHIFT:
    #    bgshifts = bgshifts.round(6)

    sum_frac = np.sum(fractions)
    if sum_frac == 0.0 and len(fractions) > 0: # prevent NaN errors
        fractions[0] = 1.0
        sum_frac = 1.0
    fractions = np.around((fractions / sum_frac), 6)
    scales *= sum_frac
    scales = scales.round(6)

    mixture.fractions = fractions
    mixture.scales = scales
    mixture.bgshifts = bgshifts
    mixture.residual = residual

    return mixture

@wrap_exceptions
def calculate_mixture(mixture, parsed=False):
    """
        Calculates total intensities for the current mixture, without optimizing
        fractions, scales & background shifts.
        Returns the mixture data object.
    """
    try:
        parse_mixture(mixture, parsed=parsed)
    except AssertionError:
        for specimen in mixture.specimens:
            if specimen is not None:
                specimen.total_intensity = None # clear pattern
        return mixture
    fractions = np.asanyarray(mixture.fractions)

    mixture.residuals = [0.0, ]
    for scale, bgshift, specimen in izip(mixture.scales, mixture.bgshifts, mixture.specimens):
        if specimen is not None:
            specimen.total_intensity = scale * np.sum(fractions[:, np.newaxis] * specimen.phase_intensities, axis=0) + (bgshift if settings.BGSHIFT else 0.0)
            if specimen.observed_intensity.size > 0:
                exp = specimen.observed_intensity[specimen.selected_range]
                cal = specimen.total_intensity[specimen.selected_range]
                rp = __residual_method_map[settings.RESIDUAL_METHOD](exp, cal)
                mixture.residuals.append(rp)
    mixture.residuals[0] = np.average(mixture.residuals[1:])

    return mixture

@wrap_exceptions
def get_optimized_mixture(mixture):
    """
        Calculates total intensities for the current mixture, after optimizing
        fractions, scales & background shifts.
        Returns the mixture data object.
    """
    parse_mixture(mixture)
    optimize_mixture(mixture, parsed=True)
    calculate_mixture(mixture, parsed=True)
    return mixture

@wrap_exceptions
def get_optimized_residual(mixture):
    """
        Calculates total intensities for the current mixture, after optimizing
        fractions, scales & background shifts.
        Returns the average residual instead of the mixture data object.
    """
    return get_optimized_mixture(mixture).residual

