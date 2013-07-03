# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from math import pi
from generic.caching import cache

from generic.calculations.goniometer import get_machine_correction_range
from generic.calculations.phases import get_diffracted_intensity

@cache(16)
def get_phase_intensities(range_theta, lpf_args, di_args_list, wavelength, mcr_args):
    """
        Gets phase intensities for the provided phases
        Returns a 2-tuple containing 2-theta values and phase intensities.
    """
    range_stl = 2 * np.sin(range_theta) / wavelength
        
    correction_range = get_machine_correction_range.func(range_theta, *mcr_args)
        
    return range_theta, np.array([
        get_diffracted_intensity.func(
            range_theta, range_stl, 
            lpf_args, correction_range, 
            *di_args
        ) for di_args in di_args_list
    ], dtype=np.float_)

def get_calculated_pattern(pi_args, fractions, abs_scale, bg_shift):
    """
        Convenience function for calculating the actual total diffraction
        pattern. Sums up the (scaled, using 'fractions') intensities for each
        phase represented by pi_args (for the format see get_phase_intensities)
        adds 'bg_shift' and scales the whole pattern using 'abs_scale'
    """
    #Get 2-theta values and phase intensities
    theta_range, intensities = get_phase_intensities(*pi_args)
    theta_range = theta_range * 360.0 / pi
    
    #Apply fractions, absolute scale and bg shift:
    fractions = np.array(fractions)[:,np.newaxis]
    phase_intensities = fractions*(intensities + bg_shift)*abs_scale
                
    #Sum the phase intensities:
    total_intensity = np.sum(phase_intensities, axis=0)
    
    return theta_range, total_intensity, phase_intensities
