# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from generic.custom_math import mmult
from generic.caching import cache

from generic.calculations.components import get_factors
from generic.calculations.goniometer import get_lorentz_polarisation_factor

@cache(64)
def get_structure_factors(range_stl, G, args_list):
    shape = range_stl.shape + (G,)
    SF = np.zeros(shape, dtype=np.complex_)
    PF = np.zeros(shape, dtype=np.complex_)
    for i, args in enumerate(args_list):
        SF[:,i], PF[:,i] = get_factors.func(range_stl, *args)
    return SF, PF

@cache(64)
def get_Q_matrices(Q, CSDS_max):
    Qn = np.zeros((CSDS_max,)+Q.shape, dtype=complex)
    Qn[0,...] = np.copy(Q)
    for n in range(1, CSDS_max):
        Qn[n,...] = mmult(Qn[n-1,...], Q)  
    return Qn

@cache(64)
def get_diffracted_intensity(
        range_theta, range_stl, lpf_args, correction_range, 
        valid_probs, sigma_star, abs_scale,
        CSDS_arr, CSDS_real_mean, CSDS_max, CSDS_min,
        G, W, P, sf_args_list):
    #Check probability model, if invalid return zeros instead of the actual pattern:
    if not valid_probs:
        return np.zeros_like(range_theta)
    else:            
        #Create a helper function to 'expand' certain arrays, for 
        # results which are independent of the 2-theta range
        stl_dim = range_stl.shape[0]
        repeat_to_stl = lambda arr: np.repeat(arr[np.newaxis,...], stl_dim, axis=0)
            
        #Repeat junction probabilities & weight fractions            
        W = repeat_to_stl(W).astype(np.complex_)
        P = repeat_to_stl(P).astype(np.complex_)

        #Repeat & get SFa and SFb (transpose conjugate) structure factor matrices:
        SF, PF = get_structure_factors.func(range_stl, G, sf_args_list)
        SFa = np.repeat(SF[...,np.newaxis,:], SF.shape[1], axis=1)
        SFb = np.transpose(np.conjugate(SFa), axes=(0,2,1))

        #Calculate the repition factor for R+ probabilities:
        rank = P.shape[1]
        reps = rank / G

        #Calculate the structure factor matrix:                                   
        F = np.repeat(np.repeat(np.multiply(SFb, SFa), reps, axis=2), reps, axis=1)

        #Create Q phase factor matrices:
        PF = np.repeat(PF[...,np.newaxis,:], reps, axis=1)
        Q = np.multiply(np.repeat(np.repeat(PF, reps, axis=2), reps, axis=1), P)
        Qn = get_Q_matrices.func(Q, CSDS_max)
        
        #Calculate the intensity:
        sub_total = np.zeros(Q.shape, dtype=np.complex)    
        for n in range(CSDS_min, CSDS_max):
            progression_factor = 0
            for m in range(n+1, CSDS_max):
                progression_factor += (m-n) * CSDS_arr[m]
            sub_total += 2 * progression_factor * Qn[n-1,...]
        
        CSDS_I = repeat_to_stl(np.identity(rank, dtype=np.complex) * CSDS_real_mean)
        sub_total = (CSDS_I + sub_total)
        sub_total = mmult(mmult(F, W), sub_total)
        intensity = np.real(np.trace(sub_total,  axis1=2, axis2=1))
            
        lpf = get_lorentz_polarisation_factor(range_theta, sigma_star, *lpf_args)
            
        return intensity * correction_range * abs_scale * lpf
