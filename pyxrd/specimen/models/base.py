# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from math import pi, log

import numpy as np

from mvc.observers import ListObserver
from mvc.models.properties import (
    StringProperty, SignalMixin, ReadOnlyMixin, FloatProperty, LabeledProperty,
    ObserveMixin, ListProperty, BoolProperty
)

from pyxrd.data import settings

from pyxrd.generic.io import storables, Storable
from pyxrd.generic.models import ExperimentalLine, CalculatedLine, DataModel
from pyxrd.generic.utils import not_none
from pyxrd.generic.models.lines import PyXRDLine

from pyxrd.calculations.peak_detection import peakdetect
from pyxrd.calculations.data_objects import SpecimenData

from pyxrd.goniometer.models import Goniometer

from pyxrd.file_parsers.xrd_parsers import xrd_parsers
from pyxrd.file_parsers.exc_parsers import exc_parsers

from .markers import Marker
from .statistics import Statistics


@storables.register()
class Specimen(DataModel, Storable):
    # MODEL INTEL:
    class Meta(DataModel.Meta):
        store_id = "Specimen"

        export_filters = xrd_parsers.get_export_file_filters()
        excl_filters = exc_parsers.get_import_file_filters()

    _data_object = None
    @property
    def data_object(self):
        self._data_object.goniometer = self.goniometer.data_object
        self._data_object.range_theta = self.__get_range_theta()
        self._data_object.selected_range = self.get_exclusion_selector()
        self._data_object.z_list = self.get_z_list()
        try:
            self._data_object.observed_intensity = np.copy(self.experimental_pattern.data_y)
        except IndexError:
            self._data_object.observed_intensity = np.array([], dtype=float)
        return self._data_object

    def get_z_list(self):
        return list(self.experimental_pattern.z_data)

    project = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:

    #: The sample name
    sample_name = StringProperty(
        default="", text="Sample",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: The sample name
    name = StringProperty(
        default="", text="Name",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )


    @StringProperty(
        default="", text="Label",
        visible=False, persistent=False, tabular=True,
        mix_with=(ReadOnlyMixin,)
    )
    def label(self):
        if self.display_stats_in_lbl and (self.project is not None and self.project.layout_mode == "FULL"):
            label = self.sample_name
            label += "\nRp = %.1f%%" % not_none(self.statistics.Rp, 0.0)
            label += "\nRwp = %.1f%%" % not_none(self.statistics.Rwp, 0.0)
            return label
        else:
            return self.sample_name

    display_calculated = BoolProperty(
        default=True, text="Display calculated diffractogram",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    display_experimental = BoolProperty(
        default=True, text="Display experimental diffractogram",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    display_vshift = FloatProperty(
        default=0.0, text="Vertical shift of the plot",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed", widget_type="spin",
        mix_with=(SignalMixin,)
    )

    display_vscale = FloatProperty(
        default=0.0, text="Vertical scale of the plot",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed", widget_type="spin",
        mix_with=(SignalMixin,)
    )

    display_phases = BoolProperty(
        default=True, text="Display phases seperately",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    display_stats_in_lbl = BoolProperty(
        default=True, text="Display Rp in label",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    display_residuals = BoolProperty(
        default=True, text="Display residual patterns",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    display_residual_scale = FloatProperty(
        default=1.0, text="Residual pattern scale", minimum=0.0,
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed", widget_type="spin",
        mix_with=(SignalMixin,)
    )

    display_derivatives = BoolProperty(
        default=False, text="Display derivative patterns",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: A :class:`~pyxrd.generic.models.lines.CalculatedLine` instance
    calculated_pattern = LabeledProperty(
        default=None, text="Calculated diffractogram",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed", widget_type="xy_list_view",
        mix_with=(SignalMixin, ObserveMixin,)
    )

    #: A :class:`~pyxrd.generic.models.lines.ExperimentalLine` instance
    experimental_pattern = LabeledProperty(
        default=None, text="Experimental diffractogram",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed", widget_type="xy_list_view",
        mix_with=(SignalMixin, ObserveMixin,)
    )

    #: A list of 2-theta ranges to exclude for the calculation of the Rp factor
    exclusion_ranges = LabeledProperty(
        default=None, text="Excluded ranges",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed", widget_type="xy_list_view",
        mix_with=(SignalMixin, ObserveMixin)
    )

    #: A :class:`~pyxrd.goniometer.models.Goniometer` instance
    goniometer = LabeledProperty(
        default=None, text="Goniometer",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed",
        mix_with=(SignalMixin, ObserveMixin,)
    )

    #: A :class:`~pyxrd.specimen.models.Statistics` instance
    statistics = LabeledProperty(
        default=None, text="Markers",
        visible=False, persistent=False, tabular=True,
    )

    #: A list :class:`~pyxrd.specimen.models.Marker` instances
    markers = ListProperty(
        default=None, text="Markers", data_type=Marker,
        visible=False, persistent=True, tabular=True,
        signal_name="visuals_changed", widget_type="object_list_view",
        mix_with=(SignalMixin,)
    )

    @property
    def max_display_y(self):
        """
         The maximum intensity or z-value (display y axis) 
         of the current profile (both calculated and observed)
        """
        _max = 0.0
        if self.experimental_pattern is not None:
            _max = max(_max, np.max(self.experimental_pattern.max_display_y))
        if self.calculated_pattern is not None:
            _max = max(_max, np.max(self.calculated_pattern.max_display_y))
        return _max

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for a Specimen are:
                name: the name of the specimen
                sample_name: the sample name of the specimen
                calculated_pattern: the calculated pattern
                experimental_pattern: the experimental pattern
                exclusion_ranges: the exclusion ranges XYListStore
                goniometer: the goniometer used for recording data
                markers: the specimen's markers
                display_vshift: the patterns vertical shift from its default position
                display_vscale: the patterns vertical scale (default is 1.0)
                display_calculated: whether or not to show the calculated pattern
                display_experimental: whether or not to show the experimental pattern
                display_residuals: whether or not to show the residuals
                display_derivatives: whether or not to show the 1st derivative patterns
                display_phases: whether or not to show the separate phase patterns
                display_stats_in_lbl: whether or not to display the Rp values 
                 in the pattern label
        """

        my_kwargs = self.pop_kwargs(kwargs,
            "data_name", "data_sample", "data_sample_length",
            "data_calculated_pattern", "data_experimental_pattern",
            "calc_color", "calc_lw", "inherit_calc_color", "inherit_calc_lw",
            "exp_color", "exp_lw", "inherit_exp_color", "inherit_exp_lw",
            "project_goniometer", "data_markers", "bg_shift", "abs_scale",
            "exp_cap_value", "sample_length", "absorption", "sample_z_dev",
            *[prop.label for prop in Specimen.Meta.get_local_persistent_properties()]
        )
        super(Specimen, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        self._data_object = SpecimenData()

        with self.visuals_changed.hold_and_emit():
            with self.data_changed.hold_and_emit():
                self.name = self.get_kwarg(kwargs, "", "name", "data_name")
                sample_name = self.get_kwarg(kwargs, "", "sample_name", "data_sample")
                if isinstance(sample_name, bytes):
                    sample_name = sample_name.decode("utf-8", "ignore")
                self.sample_name = sample_name
                
                calc_pattern_old_kwargs = {}
                for kw in ("calc_color", "calc_lw", "inherit_calc_color", "inherit_calc_lw"):
                    if kw in kwargs:
                        calc_pattern_old_kwargs[kw.replace("calc_", "")] = kwargs.pop(kw)
                self.calculated_pattern = self.parse_init_arg(
                    self.get_kwarg(kwargs, None, "calculated_pattern", "data_calculated_pattern"),
                    CalculatedLine,
                    child=True, default_is_class=True,
                    label="Calculated Profile",
                    parent=self,
                    **calc_pattern_old_kwargs
                )

                exp_pattern_old_kwargs = {}
                for kw in ("exp_color", "exp_lw", "inherit_exp_color", "inherit_exp_lw"):
                    if kw in kwargs:
                        exp_pattern_old_kwargs[kw.replace("exp_", "")] = kwargs.pop(kw)
                self.experimental_pattern = self.parse_init_arg(
                    self.get_kwarg(kwargs, None, "experimental_pattern", "data_experimental_pattern"),
                    ExperimentalLine,
                    child=True, default_is_class=True,
                    label="Experimental Profile",
                    parent=self,
                    **exp_pattern_old_kwargs
                )

                self.exclusion_ranges = PyXRDLine(data=self.get_kwarg(kwargs, None, "exclusion_ranges"), parent=self)
                
                # Extract old kwargs if they are there:
                gonio_kwargs = {}
                sample_length = self.get_kwarg(kwargs, None, "sample_length", "data_sample_length")
                if sample_length is not None:
                    gonio_kwargs["sample_length"] = float(sample_length)
                absorption = self.get_kwarg(kwargs, None, "absorption")
                if absorption is not None: # assuming a surface density of at least 20 mg/cm²:
                    gonio_kwargs["absorption"] = float(absorption) / 0.02
                    
                # Initialize goniometer (with optional old kwargs):
                self.goniometer = self.parse_init_arg(
                    self.get_kwarg(kwargs, None, "goniometer", "project_goniometer"),
                    Goniometer, child=True, default_is_class=True,
                    parent=self, **gonio_kwargs
                )

                self.markers = self.get_list(kwargs, None, "markers", "data_markers", parent=self)
                for marker in self.markers:
                    self.observe_model(marker)
                self._specimens_observer = ListObserver(
                    self.on_marker_inserted,
                    self.on_marker_removed,
                    prop_name="markers",
                    model=self
                )

                self.display_vshift = float(self.get_kwarg(kwargs, 0.0, "display_vshift"))
                self.display_vscale = float(self.get_kwarg(kwargs, 1.0, "display_vscale"))
                self.display_calculated = bool(self.get_kwarg(kwargs, True, "display_calculated"))
                self.display_experimental = bool(self.get_kwarg(kwargs, True, "display_experimental"))
                self.display_residuals = bool(self.get_kwarg(kwargs, True, "display_residuals"))
                self.display_residual_scale = float(self.get_kwarg(kwargs, 1.0, "display_residual_scale"))
                self.display_derivatives = bool(self.get_kwarg(kwargs, False, "display_derivatives"))
                self.display_phases = bool(self.get_kwarg(kwargs, False, "display_phases"))
                self.display_stats_in_lbl = bool(self.get_kwarg(kwargs, True, "display_stats_in_lbl"))

                self.statistics = Statistics(parent=self)

                pass # end of with
            pass # end of with
        pass # end of __init__

    def __str__(self):
        return "<Specimen %s(%s)>" % (self.name, repr(self))

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @DataModel.observe("data_changed", signal=True)
    def notify_data_changed(self, model, prop_name, info):
        if model == self.calculated_pattern:
            self.visuals_changed.emit() # don't propagate this as data_changed
        else:
            self.data_changed.emit() # propagate signal

    @DataModel.observe("visuals_changed", signal=True)
    def notify_visuals_changed(self, model, prop_name, info):
        self.visuals_changed.emit() # propagate signal

    def on_marker_removed(self, item):
        with self.visuals_changed.hold_and_emit():
            self.relieve_model(item)
            item.parent = None

    def on_marker_inserted(self, item):
        with self.visuals_changed.hold_and_emit():
            self.observe_model(item)
            item.parent = self

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    @staticmethod
    def from_experimental_data(filename, parent, parser=xrd_parsers._group_parser, load_as_insitu=False):
        """
            Returns a list of new :class:`~.specimen.models.Specimen`'s loaded
            from `filename`, setting their parent to `parent` using the given
            parser. If the load_as_insitu flag is set to true, 
        """
        specimens = list()
        xrdfiles = parser.parse(filename)
        if len(xrdfiles):
            if getattr(xrdfiles[0], "relative_humidity_data", None) is not None: # we have relative humidity data
                specimen = None
                
                # Setup list variables:
                x_data = None
                y_datas = []
                rh_datas = []
                
                for xrdfile in xrdfiles:
                    # Get data we need:
                    name, sample, xy_data, rh_data = (
                        xrdfile.filename, xrdfile.name, 
                        xrdfile.data, xrdfile.relative_humidity_data
                    )
                    # Transform into numpy array for column selection
                    xy_data = np.array(xy_data)
                    rh_data = np.array(rh_data)
                    if specimen is None:
                        specimen = Specimen(parent=parent, name=name, sample_name=sample)
                        specimen.goniometer.reset_from_file(xrdfile.create_gon_file())
                        # Extract the 2-theta positions once:
                        x_data = np.copy(xy_data[:,0])
                    
                    # Add a new sub-pattern:
                    y_datas.append(np.copy(xy_data[:,1]))
                    
                    # Store the average RH for this pattern:
                    rh_datas.append(np.average(rh_data))
                    
                specimen.experimental_pattern.load_data_from_generator(zip(x_data, np.asanyarray(y_datas).transpose()), clear=True)
                specimen.experimental_pattern.y_names = ["%.1f" % f for f in rh_datas]
                specimen.experimental_pattern.z_data = rh_datas
                specimens.append(specimen)    
            else: # regular (might be multi-pattern) file
                for xrdfile in xrdfiles:
                    name, sample, generator = xrdfile.filename, xrdfile.name, xrdfile.data
                    specimen = Specimen(parent=parent, name=name, sample_name=sample)
                    # TODO FIXME:
                    specimen.experimental_pattern.load_data_from_generator(generator, clear=True)
                    specimen.goniometer.reset_from_file(xrdfile.create_gon_file())
                    specimens.append(specimen)
        return specimens

    def json_properties(self):
        props = Storable.json_properties(self)
        props["exclusion_ranges"] = self.exclusion_ranges._serialize_data()
        return props

    def get_export_meta_data(self):
        """ Returns a dictionary with common meta-data used in export functions
            for experimental or calculated data """
        return dict(
            sample=self.label + " " + self.sample_name,
            wavelength=self.goniometer.wavelength,
            radius=self.goniometer.radius,
            divergence=self.goniometer.divergence,
            soller1=self.goniometer.soller1,
            soller2=self.goniometer.soller2,
        )


    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def clear_markers(self):
        with self.visuals_changed.hold():
            for marker in list(self.markers)[::-1]:
                self.markers.remove(marker)

    def auto_add_peaks(self, tmodel):
        """
        Automagically add peak markers
        
        *tmodel* a :class:`~specimen.models.ThresholdSelector` model
        """
        threshold = tmodel.sel_threshold
        base = 1 if (tmodel.pattern == "exp") else 2
        data_x, data_y = tmodel.get_xy()
        maxtab, mintab = peakdetect(data_y, data_x, 5, threshold) # @UnusedVariable

        mpositions = [marker.position for marker in self.markers]

        with self.visuals_changed.hold():
            i = 1
            for x, y in maxtab: # @UnusedVariable
                if not x in mpositions:
                    nm = self.goniometer.get_nm_from_2t(x) if x != 0 else 0
                    new_marker = Marker(label="%%.%df" % (3 + min(int(log(nm, 10)), 0)) % nm, parent=self, position=x, base=base)
                    self.markers.append(new_marker)
                i += 1

    def get_exclusion_selector(self):
        """
        Get the numpy selector array for non-excluded data
        
        :rtype: a numpy ndarray
        """
        x = self.__get_range_theta() * 360.0 / pi # convert to degrees
        selector = np.ones(x.shape, dtype=bool)
        data = np.sort(np.asarray(self.exclusion_ranges.get_xy_data()), axis=0)
        for x0, x1 in zip(*data):
            new_selector = ((x < x0) | (x > x1))
            selector = selector & new_selector
        return selector

    def get_exclusion_xy(self):
        """
        Get an numpy array containing only non-excluded data X and Y data
                
        :rtype: a tuple containing 4 numpy ndarray's: the experimental X and Y
        data and the calculated X and Y data
        """
        ex, ey = self.experimental_pattern.get_xy_data()
        cx, cy = self.calculated_pattern.get_xy_data()
        selector = self.get_exclusion_selector(ex)
        return ex[selector], ey[selector], cx[selector], cy[selector]

    # ------------------------------------------------------------
    #      Draggable mix-in hook:
    # ------------------------------------------------------------
    def on_pattern_dragged(self, delta_y, button=1):
        if button == 1:
            self.display_vshift += delta_y
        elif button == 3:
            self.display_vscale += delta_y
        elif button == 2:
            self.project.display_plot_offset += delta_y
        pass

    def update_visuals(self, phases):
        """
            Update visual representation of phase patterns (if any)
        """
        if phases is not None:
            self.calculated_pattern.y_names = [
               phase.name if phase is not None else "" for phase in phases
            ]
            self.calculated_pattern.phase_colors = [
                phase.display_color if phase is not None else "#FF00FF" for phase in phases
            ]

    # ------------------------------------------------------------
    #      Intensity calculations:
    # ------------------------------------------------------------
    def update_pattern(self, total_intensity, phase_intensities, phases):
        """
        Update calculated patterns using the provided total and phase intensities
        """
        if len(phases) == 0:
            self.calculated_pattern.clear()
        else:
            maxZ = len(self.get_z_list())
            new_data = np.zeros((phase_intensities.shape[-1], maxZ + maxZ*len(phases))) 
            for z_index in range(maxZ):   
                # Set the total intensity for this z_index:
                new_data[:, z_index] = total_intensity[z_index]
                # Calculate phase intensity offsets:
                phase_start_index = maxZ + z_index * len(phases)
                phase_end_index = phase_start_index + len(phases)
                # Set phase intensities for this z_index:                
                new_data[:,phase_start_index:phase_end_index] = phase_intensities[:,z_index,:].transpose()
                # Store in pattern:
                self.calculated_pattern.set_data(
                    self.__get_range_theta() * 360. / pi,
                    new_data
                )
            self.update_visuals(phases)
        if settings.GUI_MODE:
            self.statistics.update_statistics(derived=self.display_derivatives)

    def convert_to_fixed(self):
        """
        Converts the experimental data from ADS to fixed slits in-place 
        (disregards the `has_ads` flag in the goniometer, but uses the settings
        otherwise) 
        """
        correction = self.goniometer.get_ADS_to_fixed_correction(self.__get_range_theta())
        self.experimental_pattern.apply_correction(correction)

    def convert_to_ads(self):
        """
        Converts the experimental data from fixed slits to ADS in-place 
        (disregards the `has_ads` flag in the goniometer, but uses the settings
        otherwise) 
        """
        correction = 1.0 / self.goniometer.get_ADS_to_fixed_correction(self.__get_range_theta())
        self.experimental_pattern.apply_correction(correction)

    def __get_range_theta(self):
        if len(self.experimental_pattern) <= 1:
            return self.goniometer.get_default_theta_range()
        else:
            return np.radians(self.experimental_pattern.data_x * 0.5)

    def __repr__(self):
        return "Specimen(name='%s')" % self.name

    pass # end of class
