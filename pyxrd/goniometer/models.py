# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from math import radians
import numpy as np

from mvc.models.properties import (
    FloatProperty, IntegerProperty, BoolProperty,
    SignalMixin
, LabeledProperty)

from pyxrd.refinement.refinables.properties import DataMixin

from pyxrd.generic.models import DataModel
from pyxrd.generic.io import storables, Storable, get_case_insensitive_glob
from pyxrd.file_parsers.json_parser import JSONParser
from pyxrd.data import settings
from pyxrd.generic.io.utils import retrieve_lowercase_extension

from pyxrd.generic.io.utils import retrieve_lowercase_extension
from pyxrd.generic.models.lines import StorableXYData

from pyxrd.calculations.goniometer import (
    get_lorentz_polarisation_factor,
    get_fixed_to_ads_correction_range,
    get_nm_from_2t, get_nm_from_t,
    get_2t_from_nm, get_t_from_nm,
)
from pyxrd.calculations.data_objects import GonioData


@storables.register()
class Goniometer(DataModel, Storable):
    """
    The Goniometer class contains all the information related to the
    X-ray diffraction goniometer, e.g. wavelength, radius, slit sizes, ...
    """
    # MODEL INTEL:
    class Meta(DataModel.Meta):
        store_id = "Goniometer"

    _data_object = None
    @property
    def data_object(self):
        self._data_object.wavelength = self.wavelength
        x, y = self.wavelength_distribution.get_xy_data()
        self._data_object.wavelength_distribution = zip(x.tolist(), y.tolist())
        return self._data_object

    project = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:

    #: Start angle (in °2-theta, only  used when calculating without
    #: experimental data)
    min_2theta = FloatProperty(
        default=3.0, text="Start angle", minimum=0.0, maximum=180.0,
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    #: End angle (in °2-theta, only  used when calculating without
    #: experimental data)
    max_2theta = FloatProperty(
        default=3.0, text="End angle", minimum=0.0, maximum=180.0,
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    #: The number of steps between start and end angle
    steps = IntegerProperty(
        default=2500, text="Steps", minimum=0,
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    #: The wavelength distribution
    wavelength_distribution = LabeledProperty(
        default=None, text="Wavelength distribution",
        tabular=False, persistent=True, visible=False, 
        signal_name="data_changed", widget_type="xy_list_view",
        mix_with=(SignalMixin)
    )

    #: The wavelength of the generated X-rays (in nm)
    wavelength = FloatProperty(
        default=0.154056, text="Wavelength", minimum=0.0,
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    #: The first Soller slit size (in °)
    soller1 = FloatProperty(
        default=2.3, text="Soller 1", minimum=0,
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    #: The second Soller slit size (in °)
    soller2 = FloatProperty(
        default=2.3, text="Soller 2", minimum=0,
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    #: The radius of the goniometer (in cm)
    radius = FloatProperty(
        default=24.0, text="Radius", minimum=0,
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    #: The divergence slit size of the goniometer (in °)
    divergence = FloatProperty(
        default=0.5, text="Divergence", minimum=0,
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    #: Flag indicating whether an automatic divergence slit was used, and a
    #: correction should be applied:
    #:     I*(2t) = I(2t) * ((divergence * ads_fact) / (np.sin(ads_phase_fact * 2t + ads_phase_shift) - ads_const))
    #: Where I* is the corrected and I is the uncorrected intensity.
    has_ads = BoolProperty(
        default=False, text="Has ADS",
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    #: The factor in the ads equation (see :attr:`has_ads`)
    ads_fact = FloatProperty(
        default=1.0, text="ADS Factor",
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    #: The phase factor in the ads equation (see :attr:`has_ads`)
    ads_phase_fact = FloatProperty(
        default=1.0, text="ADS Phase Factor",
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    #: The phase shift in the ads equation (see :attr:`has_ads`)
    ads_phase_shift = FloatProperty(
        default=0.0, text="ADS Phase Shift",
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    #: The constant in the ads equation (see :attr:`has_ads`)
    ads_const = FloatProperty(
        default=0.0, text="ADS Constant",
        tabular=True, persistent=True, visible=False,
        signal_name="data_changed",
        mix_with=(DataMixin, SignalMixin)
    )

    # ------------------------------------------------------------
    #      Initialization and other internals
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
            "wavelength",
            *[prop.label for prop in Goniometer.Meta.get_local_persistent_properties()]
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
            
            wavelength = self.get_kwarg(kwargs, None, "wavelength", "data_lambda", "lambda")
            if not "wavelength_distribution" in kwargs and wavelength is not None:
                default_wld = [ [wavelength,1.0], ]
            else:
                # A Cu wld:
                default_wld = [
                    [0.1544426,0.955148885],
                    [0.153475,0.044851115],
                ]                
            self._wavelength_distribution = StorableXYData(
               data=self.get_kwarg(kwargs, zip(*default_wld), "wavelength_distribution")
            )           

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def __reduce__(self):
        return (type(self), ((), self.json_properties()))

    def json_properties(self):
        props = Storable.json_properties(self)
        props["wavelength_distribution"] = self.wavelength_distribution._serialize_data()
        return props

    def reset_from_file(self, gonfile):
        """
        Loads & sets the parameters from the goniometer JSON file
        specified by `gonfile`, can be a filename or a file-like object.
        """
        new_gonio = JSONParser.parse(gonfile)
        with self.data_changed.hold():
            for prop in self.Meta.all_properties:
                if prop.persistent:
                    if prop.label == "wavelength_distribution":
                        self.wavelength_distribution.clear()
                        self.wavelength_distribution.set_data(
                            *new_gonio.wavelength_distribution.get_xy_data())  
                    elif prop.label != "uuid":
                        setattr(self, prop.label, getattr(new_gonio, prop.label))
                        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
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

    def get_lorentz_polarisation_factor(self, range_theta, sigma_star):
        """
            Calculates Lorentz polarization factor for the given theta range
            and sigma-star value using the information about the goniometer's
            geometry.
        """
        return get_lorentz_polarisation_factor(
            range_theta, sigma_star, self.soller1, self.soller2, self.mcr_2theta
        )

    def get_ADS_to_fixed_correction(self, range_theta):
        """
            Returns a correction range that will convert ADS data to fixed slit
            data. Use with caution.
        """
        return 1.0 / get_fixed_to_ads_correction_range(range_theta, self.data_object)

    pass # end of class
