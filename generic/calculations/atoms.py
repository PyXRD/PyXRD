# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from math import pi

from generic.caching import cache

@cache(64)
def get_structure_factor(stl_range, atoms_array):
    """
        Calculates the atomic scatter factor for a given range of 
        2*sin(θ) / λ values.
        Expects λ to be in nanometers, not Angström!
    """
    #atoms_array.shape = (M,)    
        
    angstrom_range = ((stl_range*0.05)**2)[...,np.newaxis]
    #angstrom_range.shape = (N,1)
     
    asf = np.sum(atoms_array.par_a * np.exp(-atoms_array.par_b * angstrom_range[...,np.newaxis]), axis=2) + atoms_array.par_c
    asf = asf * np.exp(-atoms_array.debye * angstrom_range)
    # asf.shape = (N,M,)
              
    return np.sum(asf * atoms_array.pn * np.exp(2 * pi * atoms_array.z * stl_range[...,np.newaxis] * 1j), axis=1)
