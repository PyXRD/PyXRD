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
    r"""
    Returns a tuple containing the structure factor and phase difference for
        - range_stl: numpy array of 2*sin(θ) / λ values
        - component: a :class:`~pyxrd.calculations.data_objects.ComponentData`
          instance containing two lists of layer and interlayer
          :class:`~pyxrd.calculations.data_objects.Atom`'s.
          
    This function calls 
    :meth:`~pyxrd.calculations.atoms.get_structure_factor` for each
    atom in the layer and interlayer list of the component data object and
    sums the result to obtain the component's structure factors.
    
    The component's phase differences are calculated as follows:
      
    .. math::
        :nowrap:
        
        \begin{flalign*}
            & \psi = e^ { 2 \pi \cdot { \frac { 2 \cdot sin(\theta)} {\lambda} } \cdot \left( d_{001} \cdot i - \pi \cdot \delta d_{001} \cdot { \frac {2 \cdot sin(\theta)} {\lambda} } \right) } 
        \end{flalign*} 
        
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
