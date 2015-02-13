# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from pyxrd.generic.caching import cache

from pyxrd.calculations.goniometer import (
    get_machine_correction_range,
    get_lorentz_polarisation_factor
)
from pyxrd.calculations.phases import get_diffracted_intensity

def get_intensity(range_theta, range_stl, soller1, soller2, phase):
    """
        Gets intensity for a single taking the
        lorentz polarization factor into account.
    """
    intensity = get_diffracted_intensity(range_stl, phase)
    lpf = get_lorentz_polarisation_factor(
        range_theta,
        phase.sigma_star,
        soller1, soller2
    )
    return intensity * lpf

@cache(16)
def calculate_phase_intensities(specimen):
    """
        Gets phase intensities for the provided phases
        Returns a 2-tuple containing 2-theta values and phase intensities.
    """
    range_stl = 2 * np.sin(specimen.range_theta) / specimen.goniometer.wavelength

    correction_range = get_machine_correction_range.func(specimen)

    return correction_range, correction_range * np.array([
        get_intensity(
            specimen.range_theta, range_stl,
            specimen.goniometer.soller1, specimen.goniometer.soller2,
            phase
        )  if phase != None else np.zeros_like(range_stl) for phase in specimen.phases
    ], dtype=np.float_)

def get_summed_intensities(specimen, scale, fractions, bgshift):
    """
        Returns the total or summed intensity of all phases in the given 
        specimen, with the given scale, phase fractions and background shift
        value. Does not re-calculate phases or corrections and assumes
        these are calculated and stored in the specimen object.
    """
    summed = np.sum((fractions * specimen.phase_intensities.transpose()).transpose(), axis=0)
    result = scale * summed + bgshift * specimen.correction
    return result
