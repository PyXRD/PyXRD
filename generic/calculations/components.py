# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from math import sin, cos, pi, sqrt, exp, radians, log

from generic.custom_math import mmult
from generic.caching import cache
from generic.calculations.atoms import get_structure_factor

@cache(64)
def get_factors(range_stl, d001, delta_c, args_list):    
    sf_tot = np.zeros(range_stl.shape, dtype=np.complex_)
    for args in args_list:
        sf_tot += get_structure_factor.func(range_stl, *args)
        
    return sf_tot, np.exp(2*pi*range_stl * (d001*1j - pi*delta_c*range_stl))
