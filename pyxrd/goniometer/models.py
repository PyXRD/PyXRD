# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from math import radians
import numpy as np

from pyxrd.mvc import PropIntel

from pyxrd.generic.models import DataModel
from pyxrd.generic.io import storables, Storable, get_case_insensitive_glob
from pyxrd.data import settings

from pyxrd.calculations.goniometer import (
    get_lorentz_polarisation_factor,
    get_machine_correction_range,
    get_nm_from_2t, get_nm_from_t,
    get_2t_from_nm, get_t_from_nm,
)
from pyxrd.calculations.data_objects import GonioData
from pyxrd.generic.io.utils import retrieve_lowercase_extension

@storables.register()
class Goniometer(DataModel, Storable):
    """
    The Goniometer class contains all the information related to the
    X-ray diffraction goniometer, e.g. wavelength, radius, slit sizes, ...
    """
    # MODEL INTEL:
    class Meta(DataModel.Meta):
        properties = [ # TODO add labels
            PropIntel(name="radius", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
            PropIntel(name="divergence", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
            PropIntel(name="soller1", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
            PropIntel(name="soller2", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
            PropIntel(name="min_2theta", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
            PropIntel(name="max_2theta", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
            PropIntel(name="steps", data_type=int, storable=True, has_widget=True),
            PropIntel(name="wavelength", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
            PropIntel(name="has_ads", data_type=bool, storable=True, has_widget=True),
            PropIntel(name="ads_fact", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
            PropIntel(name="ads_phase_fact", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
            PropIntel(name="ads_phase_shift", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
            PropIntel(name="ads_const", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
        ]
        store_id = "Goniometer"
        file_filters = [
            ("Goniometer files", get_case_insensitive_glob("*.GON")),
        ]

    _data_object = None
    @property
    def data_object(self):
        return self._data_object

    project = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:
    def _set_data_property(self, name, value):
        try: value = self.Meta.get_prop_intel_by_name(name).data_type(value)
        except ValueError: return # ignore faulty values
        setattr(self._data_object, name, value)
        self.data_changed.emit()

    @property
    def min_2theta(self):
        """Start angle (in °2-theta, only  used when calculating without 
        experimental data)"""
        return self._data_object.min_2theta
    @min_2theta.setter
    def min_2theta(self, value): self._set_data_property("min_2theta", value)

    @property
    def max_2theta(self):
        """End angle (in °2-theta, only  used when calculating without 
        experimental data)"""
        return self._data_object.max_2theta
    @max_2theta.setter
    def max_2theta(self, value): self._set_data_property("max_2theta", value)

    @property
    def steps(self):
        """The number of steps between start and end angle"""
        return self._data_object.steps
    @steps.setter
    def steps(self, value): self._set_data_property("steps", value)

    @property
    def wavelength(self):
        """The wavelength of the generated X-rays (in nm)"""
        return self._data_object.wavelength
    @wavelength.setter
    def wavelength(self, value): self._set_data_property("wavelength", value)

    @property
    def soller1(self):
        """The first Soller slit size (in °)"""
        return self._data_object.soller1
    @soller1.setter
    def soller1(self, value): self._set_data_property("soller1", value)

    @property
    def soller2(self):
        """The second Soller slit size (in °)"""
        return self._data_object.soller2
    @soller2.setter
    def soller2(self, value): self._set_data_property("soller2", value)

    @property
    def radius(self):
        """The radius of the goniometer (in cm)"""
        return self._data_object.radius
    @radius.setter
    def radius(self, value): self._set_data_property("radius", value)

    @property
    def divergence(self):
        """The divergence slit size of the goniometer (in °)"""
        return self._data_object.divergence
    @divergence.setter
    def divergence(self, value): self._set_data_property("divergence", value)

    @property
    def has_ads(self):
        """
        Flag indicating whether an automatic divergence slit was used, and a
        correction should be applied:
            I*(2t) = I(2t) * ((divergence * ads_fact) / (np.sin(ads_phase_fact * 2t + ads_phase_shift) - ads_const))
        Where I* is the corrected and I is the uncorrected intensity.
        """
        return self._data_object.has_ads
    @has_ads.setter
    def has_ads(self, value): self._set_data_property("has_ads", value)

    @property
    def ads_fact(self):
        """The factor in the ads equation (see `has_ads`)"""
        return self._data_object.ads_fact
    @ads_fact.setter
    def ads_fact(self, value): self._set_data_property("ads_fact", value)

    @property
    def ads_phase_fact(self):
        """The phase factor in the ads equation (see `has_ads`)"""
        return self._data_object.ads_phase_fact
    @ads_phase_fact.setter
    def ads_phase_fact(self, value): self._set_data_property("ads_phase_fact", value)

    @property
    def ads_phase_shift(self):
        """The phase shift (in °) in the ads equation (see `has_ads`)"""
        return self._data_object.ads_phase_shift
    @ads_phase_shift.setter
    def ads_phase_shift(self, value): self._set_data_property("ads_phase_shift", value)

    @property
    def ads_const(self):
        """The constant in the ads equation (see `has_ads`)"""
        return self._data_object.ads_const
    @ads_const.setter
    def ads_const(self, value): self._set_data_property("ads_const", value)

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Constructor takes any of its properties as a keyword argument.
            
            In addition to the above, the constructor still supports the 
            following deprecated keywords, mapping to a current keyword:
                - lambda: maps to wavelength
                
            Any other arguments or keywords are passed to the base class.
        """
        my_kwargs = self.pop_kwargs(kwargs,
            "data_radius", "data_divergence", "data_soller1", "data_soller2",
            "data_min_2theta", "data_max_2theta", "data_lambda", "lambda",
            *[names[0] for names in type(self).Meta.get_local_storable_properties()]
        )
        super(Goniometer, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        self._data_object = GonioData()

        with self.data_changed.hold():
            self.radius = self.get_kwarg(kwargs, 24.0, "radius", "data_radius")
            self.divergence = self.get_kwarg(kwargs, 0.5, "divergence", "data_divergence")
            self.has_ads = self.get_kwarg(kwargs, False, "has_ads")
            self.ads_fact = self.get_kwarg(kwargs, 1.0, "ads_fact")
            self.ads_phase_fact = self.get_kwarg(kwargs, 1.0, "ads_phase_fact")
            self.ads_phase_shift = self.get_kwarg(kwargs, 0.0, "ads_phase_shift")
            self.ads_const = self.get_kwarg(kwargs, 0.0, "ads_const")

            self.soller1 = self.get_kwarg(kwargs, 2.3, "soller1", "data_soller1")
            self.soller2 = self.get_kwarg(kwargs, 2.3, "soller2", "data_soller2")

            self.min_2theta = self.get_kwarg(kwargs, 3.0, "min_2theta", "data_min_2theta")
            self.max_2theta = self.get_kwarg(kwargs, 45.0, "max_2theta", "data_max_2theta")
            self.steps = self.get_kwarg(kwargs, 2500, "steps")
            self.wavelength = self.get_kwarg(kwargs, 0.154056, "wavelength", "data_lambda", "lambda")

    def __reduce__(self):
        return (type(self), ((), self.json_properties()))

    @classmethod
    def get_default_goniometers_path(cls):
        """
            Returns a tuple containing the location of the default Goniometer
            setup files and their file extension.
        """
        return (
            settings.DATA_REG.get_directory_path("DEFAULT_GONIOS"),
            retrieve_lowercase_extension(*cls.Meta.file_filters[0][1])
        )

    @classmethod
    def get_default_wavelengths_path(cls):
        """
            Returns the location of the default wavelengths file
        """
        return settings.DATA_REG.get_file_path("WAVELENGTHS")

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def reset_from_file(self, path):
        """
        Loads & sets the parameters from the goniometer JSON file
        specified by `path`
        """
        new_gonio = Goniometer.load_object(path, parent=None)
        with self.data_changed.hold():
            for prop in self.Meta.all_properties:
                if prop.storable and prop.name != "uuid":
                    setattr(self, prop.name, getattr(new_gonio, prop.name))

    def get_nm_from_t(self, theta):
        """Converts a theta position to a nanometer value"""
        return get_nm_from_t(
            theta,
            wavelength=self.wavelength, zero_for_inf=True
        )

    def get_nm_from_2t(self, twotheta):
        """Converts a 2-theta position to a nanometer value"""
        return get_nm_from_2t(
            twotheta,
            wavelength=self.wavelength, zero_for_inf=True
        )

    def get_t_from_nm(self, nm):
        """ Converts a nanometer value to a theta position"""
        return get_t_from_nm(nm, wavelength=self.wavelength)

    def get_2t_from_nm(self, nm):
        """ Converts a nanometer value to a 2-theta position"""
        return get_2t_from_nm(nm, wavelength=self.wavelength)

    def get_default_theta_range(self, as_radians=True):
        """
        Returns a numpy array containing the theta values as radians from
        `min_2theta` to `max_2theta` with `steps` controlling the interval.
        When `as_radians` is set to False the values are returned as degrees. 
        """
        def torad(val):
            if as_radians:
                return radians(val)
            else:
                return val
        min_theta = torad(self.min_2theta * 0.5)
        max_theta = torad(self.max_2theta * 0.5)
        delta_theta = float(max_theta - min_theta) / float(self.steps)
        theta_range = (min_theta + delta_theta * np.arange(0, self.steps, dtype=float)) + delta_theta * 0.5
        return theta_range

    def get_machine_correction_range(self, range_theta, sample_length, absorption):
        """
            Calculates correction factors for the given theta range, sample
            length and absorption using the information about the goniometer's
            geometry.
        """
        return get_machine_correction_range(
            range_theta, sample_length, absorption, self.data_object
        )

    def get_lorentz_polarisation_factor(self, range_theta, sigma_star):
        """
            Calculates Lorentz polarization factor for the given theta range
            and sigma-star value using the information about the goniometer's
            geometry.
        """
        return get_lorentz_polarisation_factor(
            range_theta, sigma_star, self.data_object
        )

    pass # end of class
