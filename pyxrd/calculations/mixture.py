# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.


import time
import logging
logger = logging.getLogger(__name__)

import numpy as np
from scipy.optimize import fmin_l_bfgs_b

from pyxrd.data import settings

from .specimen import calculate_phase_intensities, calculate_scaled_intensities, get_clipped_intensities
from .exceptions import wrap_exceptions
from .statistics import Rp, Rpw, Rpder, Rphase

__residual_method_map = {
    "Rp" : Rp,
    "Rpw" : Rpw,
    "Rpder": Rpder,
    "Rphase": Rphase
}

#===============================================================================
# Solution vector handling:
#===============================================================================
def parse_solution(x, mixture):
    # Get the original solution   
    fractions = mixture.fractions
    scales = mixture.scales
    bgshifts = mixture.bgshifts
    
    # We normalize the new fractions so the sum of all fractions
    # (including static fractions) is always 1
    scaled_fracs = x[:mixture.m] * (1.0 - mixture.sum_static_fractions) / np.sum(x[:mixture.m])
    
    # Store the variables in the right positions:
    np.put(fractions, mixture.selected_fractions, scaled_fracs)
    np.put(scales, mixture.selected_scales, x[mixture.m:mixture.m + mixture.n])
    np.put(bgshifts, mixture.selected_bgshifts, x[-mixture.o:])
    
    # Return the complete arrays (including static factors)
    return fractions, scales, bgshifts

def get_solution(mixture):
    return np.concatenate((
        np.take(mixture.fractions, mixture.selected_fractions),
        np.take(mixture.scales, mixture.selected_scales),
        np.take(mixture.bgshifts, mixture.selected_bgshifts)
    ))    

def set_solution(x, mixture):
    mixture.fractions, mixture.scales, mixture.bgshifts = parse_solution(x, mixture)   

def get_zero_solution(mixture):
    # Create complete solution array
    x0 = np.ones(shape=(mixture.m+mixture.n+mixture.o,))
    # Set all bg shifts to zero   
    x0[-mixture.o:] = 0.0
    # Set all fractions to equal size (of the remainder)
    x0[:mixture.m] = 1.0 / (1.0 - mixture.sum_static_fractions)
    
    return x0

#===============================================================================
# Solution bounds handling:
#===============================================================================
def get_bounds(mixture):
    bounds = [(0., 1.) for _ in range(mixture.m)] # allow zero fractions
    bounds += [(1e-3, None) for _ in range(mixture.n)] # don't allow zero scales
    bounds += [(0., None) for _ in range(mixture.o)]
    return bounds

#===============================================================================
# Residual calculations:
#===============================================================================
def _get_specimen_residual(specimen):
    """
        Returns the residual error for the given specimen and the (otionally)
        given calculated data. If no calculated data is passed, the calculated
        data stored in the specimen object is used (and assumed to be set).
    """
    exp, cal = get_clipped_intensities(specimen)
    return __residual_method_map[settings.RESIDUAL_METHOD](exp, cal)   

def _get_residuals(x, mixture):
    set_solution(x, mixture)
    mixture = calculate_mixture(mixture)
    return mixture.residuals

def get_residual(mixture):
    return _get_residuals(get_solution(mixture), mixture)

#===============================================================================
# Mixture calculations:
#===============================================================================

def parse_mixture(mixture, force=False):
    """
        This calculates the phase intensities.
    """
    if not mixture.parsed or force:
        mixture.parsed = False
        # Sanity checks:
        assert mixture.n > 0, "Need at least 1 specimen to optimize phase fractions, scales and background."
        assert mixture.n == len(mixture.specimens), "Invalid specimen count on mixture data object."
        assert mixture.m > 0, "Need at least 1 phase in one of the specimen to optimize phase fractions, scales and background."
        
        # We have some fixed fractions:
        mixture.selected_fractions = np.asanyarray(np.nonzero(mixture.fractions_mask)).flatten()
        mixture.selected_scales = np.asanyarray(np.nonzero(mixture.scales_mask)).flatten()
        mixture.selected_bgshifts = np.asanyarray(np.nonzero(mixture.bgshifts_mask)).flatten()
        mixture.real_m = mixture.m
        mixture.real_n = mixture.n
        mixture.real_o = mixture.n
        mixture.m = len(mixture.selected_fractions)
        mixture.n = len(mixture.selected_scales)
        mixture.o = len(mixture.selected_bgshifts)
        
        # The first term should be 1.0, unless the user entered a custom fraction
        sm = np.sum(mixture.fractions)
        mixture.sum_static_fractions = sm - np.sum(np.take(mixture.fractions, mixture.selected_fractions))
        if sm != 1.0 and mixture.sum_static_fractions < 0.0 or mixture.sum_static_fractions > 1.0:
            mixture.fractions = mixture.fractions / sm
            sm = 1.0
        mixture.sum_static_fractions = sm - np.sum(np.take(mixture.fractions, mixture.selected_fractions))
            
        
        mixture.z = 0
        for specimen in mixture.specimens:
            if specimen is not None:
                mixture.z = len(specimen.z_list)
                break
        assert mixture.z > 0, "Need at least 1 pattern in one of the specimens to optimize phase fractions, scales and background."

        for specimen in mixture.specimens:
            if specimen is not None:
                specimen.correction, specimen.phase_intensities = \
                    calculate_phase_intensities(specimen)
            else:
                logger.warning("parse_mixture reports: 'None found!'")
                
        mixture.parsed = True

@wrap_exceptions
def optimize_mixture(mixture, force=False):
    """
        Optimizes the mixture fractions, scales and bg shifts.
        Returns the mixture data object.
    """
    if not mixture.optimized or force:
        # 0. Calculate phase intensitities
        try:
            parse_mixture(mixture)
        except AssertionError:
            if settings.DEBUG:
                raise
            return mixture # ignore and return the original object back
    
        # 1. setup start point:
        x0 = get_zero_solution(mixture)
        bounds = get_bounds(mixture)
    
        # 2. Define target function:        
        def _get_average_residual(x):
            # Reset this flag so we actually recalculated stuff: 
            mixture.calculated = False
            res = _get_residuals(x, mixture)[0]
            return res
    
        # 3. Optimize:
        t1 = time.time()
        lastx, residual, info = fmin_l_bfgs_b(
            _get_average_residual,
            x0,
            approx_grad=True,
            bounds=bounds,
            iprint=-1
        )
        if np.isscalar(residual): # Make sure this is an array:
            residual = np.array([residual])
    
        t2 = time.time()
        logger.debug('%s took %0.3f ms' % ("optimize_mixture", (t2 - t1) * 1000.0))
        logger.debug(' Solution: %s' % lastx)
        logger.debug(' Average residual: %s' % residual)
        logger.debug(' Info dict: %s' % info)
    
        # 4. rescale scales and fractions so they fit into [0-1] range,
        #    and round them to have 6 digits max:
        fractions, scales, bgshifts = parse_solution(lastx, mixture)
        fractions = fractions.flatten()
    
        sum_frac = np.sum(fractions)
        if sum_frac == 0.0 and len(fractions) > 0: # prevent NaN errors
            fractions[0] = 1.0
            sum_frac = 1.0
        fractions = np.around((fractions / sum_frac), 6)
        scales *= sum_frac
        scales = scales.round(6)
    
        # 5. Set properties on data object 
        mixture.fractions = fractions
        mixture.scales = scales
        mixture.bgshifts = bgshifts
        mixture.residual = residual

        # We still need to recalculated with the last solution
        mixture.calculated = False 
        
        # But we do have optimized fractions etc.
        mixture.optimized = True

    return mixture

@wrap_exceptions
def calculate_mixture(mixture, force=False):
    """
        Calculates total intensities for the current mixture, without optimizing
        fractions, scales & background shifts.
        Returns the mixture data object.
    """
    if not mixture.calculated or force:
        try:
            parse_mixture(mixture)
        except AssertionError:
            for specimen in mixture.specimens:
                if specimen is not None:
                    specimen.total_intensity = None # clear pattern
                    specimen.scaled_phase_intensities = None # clear pattern
            return mixture
        
        fractions = np.asanyarray(mixture.fractions)
    
        # This will contain the following residuals:
        # Average, Specimen1, Specimen2, ...
        mixture.residuals = [0.0, ]
        for scale, bgshift, specimen in zip(mixture.scales, mixture.bgshifts, mixture.specimens):
            specimen_residual = 0.0
            if specimen is not None:
                bgshift = bgshift if settings.BGSHIFT else 0.0
                specimen = calculate_scaled_intensities(specimen, scale, fractions, bgshift)
                if specimen.observed_intensity.size > 0:
                    specimen_residual = _get_specimen_residual(specimen)
                else:
                    logger.warning("calculate_mixture reports: 'Zero observations found!'")
            mixture.residuals.append(specimen_residual)
        mixture.residuals[0] = np.average(mixture.residuals[1:])
        
        mixture.calculated = True
        
    return mixture

@wrap_exceptions
def calculate_and_optimize_mixture(mixture):
    """
        Calculates total intensities for the current mixture, after optimizing
        fractions, scales & background shifts.
        Returns the mixture data object.
    """
    return calculate_mixture(optimize_mixture(mixture))

@wrap_exceptions
def get_optimized_residual(mixture):
    """
        Calculates total intensities for the current mixture, after optimizing
        fractions, scales & background shifts.
        Returns the average residual instead of the mixture data object.
    """
    mixture = calculate_and_optimize_mixture(mixture)
    return mixture.residual
    