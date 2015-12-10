# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

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

    intensity = get_diffracted_intensity(range_theta, range_stl, phase)
    if phase.apply_lpf:
        lpf = get_lorentz_polarisation_factor(
            range_theta,
            phase.sigma_star,
            soller1, soller2
        )
        return intensity * lpf
    else:
        return intensity

def calculate_phase_intensities(specimen):
    """
        Gets phase intensities for the provided phases
        Returns a 2-tuple containing 2-theta values and phase intensities.
    """
    range_stl = 2 * np.sin(specimen.range_theta) / specimen.goniometer.wavelength

    correction_range = get_machine_correction_range(specimen)

    def get_phase_intensities(phases):
        for phase in phases:
            if phase != None:
                correction = correction_range if phase.apply_correction else 1.0
                yield get_intensity(
                    specimen.range_theta, range_stl,
                    specimen.goniometer.soller1, specimen.goniometer.soller2,
                    phase
                ) * correction
            else:
                yield np.zeros_like(range_stl)

    return (
        correction_range,
        np.array([I for I in get_phase_intensities(specimen.phases)], dtype=np.float_)
     )

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
