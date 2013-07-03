# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from math import pi
from generic.caching import cache

from generic.calculations.phases import get_calculated_pattern
import settings


def parse_solution(x, n, m):
    fractions = x[:m][:,np.newaxis]
    scales = x[m:m+n]
    bgshifts = x[-n:] if settings.BGSHIFT else np.zeros(shape=(n,))
    return fractions, scales, bgshifts

def get_optimized_mixture(pi_args_list, observed_intensities, selected_ranges):
    """
        Optimizes the mixture fractions, scales and bg shifts.
            pi_args_list is a n x m-length list of phase intensity arguments
            observed_intensities is a n-length list of arrays of shape (2, x)
            and selected_ranges is a n-length list of arrays of shape (n, x)
            
            with m the number of phases, n the number of specimens and x
            the number of data points
    """
    # Sanity check:    
    n = len(observed_intensities)
    assert n > 0, "Need at least 1 array of observed data points to optimize phase fractions, scales and background."
    
    # Get phase intensities:
    phase_intensities = []
    for pi_args_sublist in pi_args_list:
        sub = []
        for pi_args in pi_args_sublist:
            sub.append(get_phase_intensities(*pi_args))
        phase_intensities.append(sub)
    
    # More sanity checks:
    assert len(phase_intensities) == n, "There is a mismatch in the number of phase intensity arrays and the number of observed intensities."
    assert len(selected_ranges) == n, "There is a mismatch in the selected ranges length and the observed intensities length."
    
    # 1. setup start point:
    m = phase_intensities.shape[0].shape[0]
    bounds = [(0,None) for i in range(m)] + [(0, None) for i in range(n*2)]
    x0 = np.ones(shape=(m+n+n,))
    x0[-n:] = 0.0 #set bg at zero
    
    # 2. Optimize:
    def get_residual(x):
        tot_rp = 0.0
        fractions, scales, bgshifts = parse_solution(x, n, m)
        for i in range(n):
            if phase_intensities[i]!=None and experimental[i].size > 0:
                calc = (scales[i] * np.sum(phase_intensities[i]*fractions, axis=0)) 
                if settings.BGSHIFT:
                    calc += bgshifts[i]
                exp = experimental[i][selected_ranges[i]]
                cal = calc[selected_ranges[i]]
                tot_rp += Statistics._calc_Rp(exp, cal)
        return tot_rp
    
    lastx, residual, info = scipy.optimize.fmin_l_bfgs_b(
        get_residual,
        x0,
        factr=1e-12,
        pgtol=1e-3,
        approx_grad=True,
        bounds=bounds,
        iprint=-1
    )
    
    # 3. rescale scales and fractions so they fit into [0-1] range, 
    #    and round them to have 6 digits max:
    fractions, scales, bgshifts = parse_solution(lastx, n, m)
    fractions = fractions.flatten()
    if settings.BGSHIFT:
        bgshifts = bgshifts.round(6)
    
    sum_frac = np.sum(fractions)
    if sum_frac == 0.0 and len(fractions) > 0: #prevent NaN errors
        fractions[0] = 1.0
        sum_frac = 1.0
    fractions = np.around((fractions / sum_frac), 6)
    scales *= sum_frac
    scales = scales.round(6)
    
    # 4. Calculate the total intensities
    total_intensities = [None] * n
    for i in range(n):
        calc = (scales[i] * np.sum(phase_intensities[i]*fractions, axis=0)) 
        if settings.BGSHIFT:
            calc += bgshifts[i]
        total_intensities[i] = calc
                
    return fractions, scales, bgshifts, phase_intensities, total_intensities, residual

