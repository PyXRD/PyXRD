# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from itertools import chain
from math import pi

import numpy as np

from pyxrd.generic.caching import cache
from pyxrd.calculations.atoms import get_structure_factor

def calculate_z(default_z, lattice_d, z_factor):
    return lattice_d + z_factor * (default_z - lattice_d)

@cache(64)
def get_factors(range_stl, component):
    """
        Returns a tuple containing the structure and phase factors for the given
        2*sin(θ) / λ values and the given component's layer and interlayer atoms.
    """

    z_factor = (component.d001 - component.lattice_d) / (component.default_c - component.lattice_d)

    num_layer_atoms = len(component.layer_atoms)

    sf_tot = 0.0 + 0.0j
    for i, atom in enumerate(chain(component.layer_atoms, component.interlayer_atoms)):
        atom.z = atom.default_z
        if i >= num_layer_atoms:
            atom.z = calculate_z(atom.z, component.lattice_d, z_factor)
        sf_tot += get_structure_factor(range_stl, atom)

    phi_tot = np.exp(2.*pi * range_stl * (component.d001 * 1j - pi * component.delta_c * range_stl))
    return sf_tot, phi_tot
