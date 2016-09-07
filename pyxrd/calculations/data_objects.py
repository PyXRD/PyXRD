# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

"""
    The following classes are not meant to be used directly, rather you should
    create the corresponding model instances and retrieve the DataObject from 
    them.
    
    The rationale behind not using the model instances directly is that
    they are difficult to serialize or pickle (memory-)efficiently.
    This is mainly due to all of the boiler-plate code that takes care of
    references, saving, loading, calculating properties from other properties
    etc. A lot of this is not needed for the actual calculation.    
    The data objects below, on the other hand, only contain the data needed to
    be able to calculate XRD patterns.
"""

class DataObject(object):
    """
    The base class for all DataObject instances.
    
    The constructor takes any number of keyword arguments it will set as
    attributes on the instance.
    """
    def __init__(self, **kwargs):
        for key, val in kwargs.iteritems():
            setattr(self, key, val)

    pass # end of class

class AtomTypeData(DataObject):
    """ The DataObject describing an AtomType. """

    #: a numpy array of `a` scattering factors
    par_a = None
    #: a numpy array of `b` scattering factors
    par_b = None
    #: the `c` scattering constant
    par_c = None
    #: the debye-waller temperature factor
    debye = None

    pass # end of class

class AtomData(DataObject):
    """ The DataObject describing an Atom. """

    #: an :class:`~AtomTypeData` instance
    atom_type = None
    #: the # of atoms projected to this z coordinate
    pn = None
    #: the default z coordinate
    default_z = None
    #: the actual z coordinate
    z = None

    pass # end of class

class ComponentData(DataObject):
    """ The DataObject describing an Atom """

    #: a list of :class:`~AtomData` instances
    layer_atoms = None

    #: a list of :class:`~AtomData` instances
    interlayer_atoms = None

    #: the component volume
    volume = None

    #: the component weight
    weight = None

    #: the d-spacing of the component
    d001 = None

    #: the default d-spacing of the component
    default_c = None

    #: the variation in d-spacing of the component
    delta_c = None

    #: the height of the silicate lattice (excluding the interlayer space)
    lattice_d = None

    pass # end of class

class CSDSData(DataObject):
    """ The DataObject describing the CSDS distribution. """

    #: average CSDS
    average = None

    #: maximum CSDS
    maximum = None

    #: minimum CSDS
    minimum = None

    #: the alpha scale factor for the log-normal distribution
    alpha_scale = None

    #: the alpha offset factor for the log-normal distribution
    alpha_offset = None

    #: the beta scale factor for the log-normal distribution
    beta_scale = None

    #: the beta offset factor for the log-normal distribution
    beta_offset = None

    pass # end of class

class GonioData(DataObject):
    """ The DataObject describing the Goniometer setup. """

    #: Lower 2-theta bound for calculated patterns
    min_2theta = None

    #: Upper 2-theta bound for calculated patterns
    max_2theta = None

    #: The number of steps in between the lower and upper 2-theta bounds
    steps = None

    #: The first soller slit size
    soller1 = None

    #: The second soller slit size
    soller2 = None

    #: The divergence size
    divergence = None

    #: Whether and Automatic Divergence Slit correction should be performed
    has_ads = None

    #: ADS Factor
    ads_fact = None

    #: ADS phase factor
    ads_phase_fact = None

    #: ADS phase shift
    ads_phase_shift = None

    #: ADS constant
    ads_const = None

    #: The goniometer radius
    radius = None

    #: The goniometer wavelength
    wavelength = None

    #: The goniometer wavelength distribution
    wavelength_distribution = None

    pass # end of class

class ProbabilityData(DataObject):
    """ The DataObject describing the layer stacking probabilities """

    #: Whether this probability is really a valid one
    valid = None

    #: The number of components this probability describes
    G = None

    #: The weight fractions matrix
    W = None

    #: The probabilities matrix
    P = None

    pass # end of class

class PhaseData(DataObject):
    """ The DataObject describing a phase """

    #: A flag indicating whether to apply Lorentz-polarization factor or not
    apply_lpf = True

    #: A flag indicating whether to apply machine corrections or not
    apply_correction = True

    #: A list of :class:`~ComponentData` instances
    components = None

    #: A :class:`~ProbabilityData` instance
    probability = None

    #: The sigma start value
    sigma_star = None

    #: A :class:`~CSDSData` instance
    csds = None

    pass # end of class

class SpecimenData(DataObject):
    """ The DataObject describing a specimen """

    #: A :class:`~GonioData` instance
    goniometer = None

    #: The sample length
    sample_length = None

    #: The sample absorption
    absorption = None

    #: A list of :class:`~PhaseData` instances
    phases = None

    #: A numpy array with the observed intensities
    observed_intensity = None

    #: A numpy array with the calculated intensity
    total_intensity = None

    #: A nummpy array with the calculated phase profiles
    phase_intensities = None

    #: A numpy array with a correction factor taking the sample & goniometer
    #  properties into account
    correction = None

    pass # end of class

class MixtureData(DataObject):
    """ The DataObject describing a mixture """

    #: A list of :class:`~SpecimenData` instances
    specimens = None

    #: A numpy array with the phase fractions
    fractions = None

    #: A numpy array with the specimen background shifts
    bgshifts = None

    #: A numpy array with the specimen absolute scales
    scales = None

    #: Whether this MixtureData object has been parsed (internal flag)
    parsed = False

    #: The number of specimens
    n = 0

    #: The number of phases
    m = 0


    pass # end of class

    pass # end of class

