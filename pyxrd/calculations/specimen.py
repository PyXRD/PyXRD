# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from math import radians, tan
from scipy.interpolate.interpolate import interp1d

from pyxrd.calculations.goniometer import (
    get_fixed_to_ads_correction_range,
    
)
from pyxrd.calculations.phases import get_intensity


def get_machine_correction_range(specimen):
    """
        Calculate a correction factor for a certain sample length,
        sample absorption and machine setup.
    """
    goniometer = specimen.goniometer
    range_st = np.sin(specimen.range_theta)
    correction_range = np.ones_like(specimen.range_theta)
    
    # Correct for automatic divergence slits first:
    if bool(goniometer.has_ads):
        correction_range *= get_fixed_to_ads_correction_range(
            specimen.range_theta, goniometer)
    # Then correct for sample absorption:
    if specimen.absorption > 0.0:
        correction_range *= np.minimum(1.0 - np.exp(-2.0 * specimen.absorption / range_st), 1.0)
    # And finally correct for sample length:
    if not bool(goniometer.has_ads):
        L_Rta = specimen.sample_length / (goniometer.radius * tan(radians(goniometer.divergence)))
        correction_range *= np.minimum(range_st * L_Rta, 1)
    return correction_range

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

    def interpolate_wavelength(I, new_wavelength, fraction):
        new_theta = np.arcsin(range_stl * new_wavelength * 0.5)
        f = interp1d(new_theta, I * fraction, bounds_error=False, fill_value=0.0)
        return f(specimen.range_theta)

    def apply_wavelength_distribution(I):
        for new_wavelength, fraction in specimen.goniometer.wavelength_distribution:
            I += interpolate_wavelength(I, new_wavelength, fraction)
        return I

    return (
        correction_range,
        np.array([
            apply_wavelength_distribution(I) for I in get_phase_intensities(specimen.phases)
        ], dtype=np.float_)
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
