# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from itertools import chain

import numpy as np

from math import sin, cos, pi, sqrt, exp, radians, log

from generic.custom_math import mmult
from generic.caching import cache
#from generic.calculations.atoms import get_structure_factor

def calculate_z(default_z, lattice_d, z_factor):
    return lattice_d + z_factor * (default_z - lattice_d)

#@cache(64)
def get_structure_factor(stl_range, atom):
    """
        Calculates the atomic scatter factor for a given range of 
        2*sin(θ) / λ values.
        Expects λ to be in nanometers, not Angström!
    """
        
    angstrom_range = ((stl_range*0.05)**2)
     
    asf = np.sum(atom.atom_type.par_a * np.exp(-atom.atom_type.par_b * angstrom_range[...,np.newaxis]), axis=1) + atom.atom_type.par_c
    asf = asf * np.exp(-atom.atom_type.debye * angstrom_range)
              
    return asf * atom.pn * np.exp(2 * pi * atom.z * stl_range * 1j)

@cache(64)
def get_factors(range_stl, component):

    z_factor = (component.d001 - component.lattice_d) / (component.default_c - component.lattice_d)    

    num_layer_atoms= len(component.layer_atoms)

    sf_tot = 0.0
    for i, atom in enumerate(chain(component.layer_atoms, component.interlayer_atoms)):
        atom.z = atom.default_z    
        if i >= num_layer_atoms:
            atom.z = calculate_z(atom.z, component.lattice_d, z_factor)      
        sf_tot += get_structure_factor(range_stl, atom)
        
    #sf_tot = get_structure_factor.func(range_stl, atoms_array)
    phi_tot = np.exp(2.*pi*range_stl * (component.d001*1j - pi*component.delta_c*range_stl))
    return sf_tot, phi_tot
