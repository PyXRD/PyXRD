# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from math import pi

from generic.caching import cache

@cache(64)
def get_atomic_scattering_factor(stl_range, a, b, c, deb): 
    """
        Calculates the atomic scatter factor for a given range of 
        2*sin(θ) / λ values.
        Expects λ to be in nanometers, not Angström!
    """
    f = np.zeros(stl_range.shape)
    angstrom_range = stl_range*0.05
    for i in range(0,5):
         f += a[i] * np.exp(-b[i]*(angstrom_range)**2)
    f += c
    f = f * np.exp(-float(deb) * (angstrom_range)**2)
    return f

@cache(64)
def get_structure_factor(stl_range, a, b, c, deb, z, pn):
    asf = get_atomic_scattering_factor.func(stl_range, a, b, c, deb)
    return asf * pn * np.exp(2 * pi * z * stl_range * 1j)
