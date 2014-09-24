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
    r"""
    Calculates the atomic scatter factor for 
        - angstrom_range: numpy array of (2*sin(θ) / λ)² values (= 1/A² units)
        - atom_type: an :class:`~pyxrd.calculations.data_objects.AtomTypeData`
          instance
          
    The atomic scattering factor is calculated as follows:
    
    .. math::
        :nowrap:
        
        \begin{flalign*}
            & ASF = \left[ c + \sum_{i=1}^{5}{ \left( a_i \cdot e ^ { - b_i \cdot {\left(2 \cdot \frac{sin(\theta)}{\lambda}\right)}^2 } \right) } \right] 
            \cdot e ^ { B \cdot {\left(2 \cdot \frac{sin(\theta)}{\lambda}\right)}^2 }  
        \end{flalign*}
        
    Where a_i, b_i and c are the scattering factors taken from `atom_type`
    """
    if atom_type is not None:
        asf = np.sum(atom_type.par_a * np.exp(-atom_type.par_b * angstrom_range[..., np.newaxis]), axis=1) + atom_type.par_c
        asf = asf * np.exp(-atom_type.debye * angstrom_range)
        return asf
    else:
        logger.warning("get_atomic_scattering_factor reports: 'None found!'")
        return np.zeros_like(angstrom_range)

def get_structure_factor(range_stl, atom):
    r"""
    Calculates the atom's structure factor for
        - range_stl: numpy array of 2*sin(θ) / λ values (= 1/nm units)
        - atom_type: an :class:`~pyxrd.calculations.data_objects.AtomData`
          instance 
          
    The structure factor is calculated using the atomic scattering factor ASF
    (calculated by :meth:`~pyxrd.calculations.atoms.get_atomic_scattering_factor`)
    as follows:

    .. math::
        :nowrap:
        
        \begin{flalign*}
            & SF = ASF \cdot p \cdot e ^ { 2 \cdot \pi \cdot z \cdot i \cdot \frac{2 \cdot sin(\theta)}{\lambda} }
        \end{flalign*}
       
    """
    if atom is not None and atom.atom_type is not None:
        angstrom_range = ((range_stl * 0.05) ** 2)

        asf = get_atomic_scattering_factor(angstrom_range, atom.atom_type)

        return asf * atom.pn * np.exp(2 * pi * atom.z * range_stl * 1j)
    else:
        logger.warning("get_structure_factor reports: 'None found!'")
        return np.zeros_like(range_stl)
