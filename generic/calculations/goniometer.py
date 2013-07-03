# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from scipy.special import erf
from math import sin, cos, pi, sqrt, radians, degrees, asin, tan

from generic.custom_math import sqrt2pi, sqrt8
from generic.utils import get_md5_hash
from generic.caching import cache

@cache(16)
def get_S(soller1, soller2):
    _S = sqrt((soller1 * 0.5)**2 + (soller2 * 0.5)**2)
    _S1S2 = soller1 * soller2
    return _S, _S1S2

@cache(16)
def get_lorentz_polarisation_factor(range_theta, sigma_star, soller1, soller2):
    sigma_star = float(max(sigma_star, 1e-18))
    S, S1S2 = get_S(soller1, soller2)
    range_st = np.sin(range_theta)
    Q = S / (sqrt8 * range_st * sigma_star)
    T = erf(Q) * sqrt2pi / (2.0*sigma_star * S) - 2.0 * range_st * (1.0- np.exp(-(Q**2.0))) / (S**2.0)
    return (1.0 + np.cos(2.0*range_theta)**2) * T / range_st
    
@cache(16)
def get_machine_correction_range(
        range_theta, 
        sample_length, absorption, 
        radius, divergence, 
        has_ads, ads_fact, ads_phase_fact, ads_phase_shift, ads_const):
    """
        Calculate a correction factor for a certain sample length,
        sample absorption and machine setup.
    """
    range_st = np.sin(range_theta)
    correction_range = np.ones_like(range_theta)
    #Correct for automatic divergence slits first:
    if has_ads:
        ads = (divergence * ads_fact / (np.sin(ads_phase_fact*range_theta + radians(ads_phase_shift)) - ads_const))
        correction_range /= ads
    #Then correct for sample absorption:
    if absorption > 0.0:
        correction_range *= np.minimum(1.0 - np.exp(-2.0*absorption / range_st), 1.0)
    #And finally correct for sample length (only for fixed slits)
    if not has_ads:
        L_Rta =  sample_length / (radius * tan(radians(divergence)))
        correction_range *= np.minimum(range_st * L_Rta, 1)
    return correction_range
