# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from scipy.special import erf
from math import sqrt, radians, tan

from pyxrd.generic.custom_math import sqrt2pi, sqrt8
from pyxrd.generic.caching import cache

def get_S(soller1, soller2):
    _S = sqrt((soller1 * 0.5) ** 2 + (soller2 * 0.5) ** 2)
    _S1S2 = soller1 * soller2
    return _S, _S1S2

@cache(16)
def get_lorentz_polarisation_factor(range_theta, sigma_star, soller1, soller2):
    """
        Get the lorentz polarisation factor for the given sigma-star value,
        soller slits and the given theta range
    """
    sigma_star = float(max(sigma_star, 1e-18))
    S, _ = get_S(soller1, soller2)
    range_st = np.sin(range_theta)
    Q = S / (sqrt8 * range_st * sigma_star)
    T = erf(Q) * sqrt2pi / (2.0 * sigma_star * S) - 2.0 * range_st * (1.0 - np.exp(-(Q ** 2.0))) / (S ** 2.0)
    return (1.0 + np.cos(2.0 * range_theta) ** 2) * T / range_st

@cache(16)
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
        ads = (np.sin(goniometer.ads_phase_fact * specimen.range_theta + radians(goniometer.ads_phase_shift)) - goniometer.ads_const) / goniometer.ads_fact
        correction_range *= ads
    # Then correct for sample absorption:
    if specimen.absorption > 0.0:
        correction_range *= np.minimum(1.0 - np.exp(-2.0 * specimen.absorption / range_st), 1.0)
    # And finally correct for sample length:
    L_Rta = specimen.sample_length / (goniometer.radius * tan(radians(goniometer.divergence)))
    correction_range *= np.minimum(range_st * L_Rta, 1)
    return correction_range

def get_nm_from_t(theta, wavelength=0.154056, zero_for_inf=False):
    """
        Convert the given theta angles (scalar or np array) to
        nanometer spacings using the given wavelength
    """
    return get_nm_from_2t(2.0 * theta, wavelength=wavelength, zero_for_inf=zero_for_inf)

def get_nm_from_2t(twotheta, wavelength=0.154056, zero_for_inf=False):
    """
        Convert the given 2-theta angles (scalar or np array) to
        nanometer spacings using the given wavelength
    """
    if twotheta == 0:
        return 0. if zero_for_inf else 1e16
    else:
        return wavelength / (2.0 * np.sin(np.radians(twotheta / 2.0)))

def get_t_from_nm(nm, wavelength=0.154056):
    """
        Convert the given nanometer spacings (scalar or np array) to
        theta angles using the given wavelength
    """
    return get_2t_from_nm(nm, wavelength=wavelength) / 2

def get_2t_from_nm(nm, wavelength=0.154056):
    """
        Convert the given nanometer spacings (scalar or np array) to
        2-theta angles using the given wavelength
    """
    twotheta = 0.0
    if nm != 0:
        twotheta = np.degrees(np.arcsin(max(-1.0, min(1.0, wavelength / (2.0 * nm))))) * 2.0
    return twotheta

