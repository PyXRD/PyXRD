# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from math import pi
import logging
logger = logging.getLogger(__name__)

def get_atomic_scattering_factor(angstrom_range, atom_type):
    """
        Calculates the atomic scatter factor for a given range of sin(θ) / λ values.
        Expects λ to be in Angström!
    """
    if atom_type is not None:
        return np.sum(atom_type.par_a * np.exp(-atom_type.par_b * angstrom_range[..., np.newaxis]), axis=1) + atom_type.par_c
    else:
        logger.warning("get_atomic_scattering_factor reports: 'None found!'")
        return np.zeros_like(angstrom_range)

def get_structure_factor(stl_range, atom):
    """
        Calculates the atom's structure factor for a given range of 2*sin(θ) / λ values.
        Expects λ to be in nanometers!
    """
    if atom is not None and atom.atom_type is not None:
        angstrom_range = ((stl_range * 0.05) ** 2)

        asf = get_atomic_scattering_factor(angstrom_range, atom.atom_type)
        asf = asf * np.exp(-atom.atom_type.debye * angstrom_range)

        return asf * atom.pn * np.exp(2 * pi * atom.z * stl_range * 1j)
    else:
        logger.warning("get_structure_factor reports: 'None found!'")
        return np.zeros_like(stl_range)
