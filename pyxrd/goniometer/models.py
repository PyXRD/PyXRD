# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from math import sin, radians, degrees, asin
import numpy as np

from pyxrd.mvc import PropIntel

from pyxrd.generic.models import DataModel
from pyxrd.generic.io import storables, Storable, get_case_insensitive_glob
from pyxrd.data import settings

from pyxrd.generic.calculations.goniometer import (
    get_lorentz_polarisation_factor,
    get_machine_correction_range
)
from pyxrd.generic.calculations.data_objects import GonioData
from pyxrd.generic.io.utils import retrieve_lowercase_extension

@storables.register()
class Goniometer(DataModel, Storable):
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

    def get_min_2theta(self): return self._data_object.min_2theta
    def set_min_2theta(self, value): self._set_data_property("min_2theta", value)

    def get_max_2theta(self): return self._data_object.max_2theta
    def set_max_2theta(self, value): self._set_data_property("max_2theta", value)

    def get_steps(self): return self._data_object.steps
    def set_steps(self, value): self._set_data_property("steps", value)

    def get_wavelength(self): return self._data_object.wavelength
    def set_wavelength(self, value): self._set_data_property("wavelength", value)

    def get_soller1(self): return self._data_object.soller1
    def set_soller1(self, value): self._set_data_property("soller1", value)

    def get_soller2(self): return self._data_object.soller2
    def set_soller2(self, value): self._set_data_property("soller2", value)

    def get_radius(self): return self._data_object.radius
    def set_radius(self, value): self._set_data_property("radius", value)

    def get_divergence(self): return self._data_object.divergence
    def set_divergence(self, value): self._set_data_property("divergence", value)

    def get_has_ads(self): return self._data_object.has_ads
    def set_has_ads(self, value): self._set_data_property("has_ads", value)

    def get_ads_fact(self): return self._data_object.ads_fact
    def set_ads_fact(self, value): self._set_data_property("ads_fact", value)

    def get_ads_phase_fact(self): return self._data_object.ads_phase_fact
    def set_ads_phase_fact(self, value): self._set_data_property("ads_phase_fact", value)

    def get_ads_phase_shift(self): return self._data_object.ads_phase_shift
    def set_ads_phase_shift(self, value): self._set_data_property("ads_phase_shift", value)

    def get_ads_const(self): return self._data_object.ads_const
    def set_ads_const(self, value): self._set_data_property("ads_const", value)

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for a Goniometer are:
                radius: the radius of the goniometer
                divergence: the divergence slit size of the goniometer (in °)
                has_ads: flag indicating whether an automatic divergence slit is used
                ads_fact: the factor in the ads equation (see below) 
                ads_phase_fact: the phase factor in the ads equation (see below
                ads_phase_shift: the phase shift in the ads equation (see below)
                ads_const: the constant in the ads equation (see below)
                soller1: the first Soller slit
                soller2: the second Soller slit
                min_2theta: the starting angle
                max_2theta: the ending angle
                steps: the number of steps between start and end angle
                wavelength: the wavelength of the generated X-rays
                
            The ADS equation is defined as follows:
            I*(2theta) = I(2theta) * ((divergence * ads_fact) / 
                (np.sin(ads_phase_fact * 2theta + radians(ads_phase_shift)) - ads_const))
        """
        super(Goniometer, self).__init__(*args, **kwargs)

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
        new_gonio = Goniometer.load_object(path, parent=None)
        with self.data_changed.hold():
            for prop in self.Meta.all_properties:
                if prop.storable and prop.name != "uuid":
                    setattr(self, prop.name, getattr(new_gonio, prop.name))

    def get_nm_from_t(self, theta):
        return self.get_nm_from_2t(2 * theta)

    def get_nm_from_2t(self, twotheta):
        if twotheta != 0:
            return self.wavelength / (2.0 * sin(radians(twotheta / 2.0)))
        else:
            return 0.0

    def get_t_from_nm(self, nm):
        return self.get_2t_from_nm(nm) / 2

    def get_2t_from_nm(self, nm):
        twotheta = 0.0
        if nm != 0:
            twotheta = degrees(asin(max(-1.0, min(1.0, self.wavelength / (2.0 * nm))))) * 2.0
        return twotheta

    def get_default_theta_range(self, as_radians=True):
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
