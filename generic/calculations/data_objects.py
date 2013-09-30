# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

"""
    These are simple data-holders used in the calculation. They are not
    meant to be used directly, rather you should create the corresponding
    model instances and retrieve the DataObject from them.
    
    The rationale behind not using the model instances directly is that
    they are a pain in the a** to serialize/pickle (memory-)efficiently.
    This is mainly due to all of the boiler-plate code that takes care of
    references, saving, loading, calculating properties from other properties
    etc. These things do not matter to the actual calculation, only their output
    does. 
    The data objects below, on the other hand, do not contain these entanglements.
    Propably these complications can be avoided partially by refactoring the code,
    however, for now this is an easy and (fairly) clean solution.
"""

class DataObject(object):

    def __init__(self, **kwargs):
        for key, val in kwargs.iteritems():
            setattr(self, key, val)

    pass # end of class

class AtomTypeData(DataObject):
    par_a = None
    par_b = None
    par_c = None
    debye = None

    pass # end of class

class AtomData(DataObject):
    atom_type = None
    pn = None
    default_z = None
    z = None

    pass # end of class

class ComponentData(DataObject):
    layer_atoms = None
    interlayer_atoms = None
    volume = None
    weight = None
    d001 = None
    default_c = None
    delta_c = None
    lattice_d = None
    d001 = None
    delta_c = None

    pass # end of class

class CSDSData(DataObject):
    Tmean = None
    Tmax = None
    Tmin = None
    alpha_scale = None
    alpha_offset = None
    beta_scale = None
    beta_offset = None

    pass # end of class

class GonioData(DataObject):
    min_2theta = None
    max_2theta = None
    steps = None
    soller1 = None
    soller2 = None
    divergence = None
    has_ads = None
    ads_fact = None
    ads_phase_fact = None
    ads_phase_shift = None
    ads_const = None
    radius = None
    wavelength = None

    pass # end of class

class ProbabilityData(DataObject):
    valid = None
    G = None
    W = None
    P = None

    pass # end of class

class PhaseData(DataObject):
    components = None
    probability = None
    sigma_star = None

    pass # end of class

class SpecimenData(DataObject):
    goniometer = None
    sample_length = None
    absorption = None

    phases = None
    observed_intensity = None
    total_intensity = None
    phase_intensities = None

    pass # end of class

class MixtureData(DataObject):

    specimens = None
    fractions = None
    bgshifts = None
    scales = None

    parsed = False

    n, m = 0, 0
    pass # end of class

