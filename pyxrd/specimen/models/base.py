# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from math import pi, log

from mvc import PropIntel
from mvc.observers import ListObserver

import numpy as np

from pyxrd.data import settings

from pyxrd.generic.io import storables, Storable
from pyxrd.generic.models import ExperimentalLine, CalculatedLine, DataModel
from pyxrd.generic.peak_detection import peakdetect
from pyxrd.generic.utils import not_none
from pyxrd.generic.models.lines import PyXRDLine

from pyxrd.calculations.specimen import calculate_phase_intensities
from pyxrd.calculations.data_objects import SpecimenData

from pyxrd.goniometer.models import Goniometer

from markers import Marker
from statistics import Statistics

from pyxrd.file_parsers.xrd_parsers import xrd_parsers
from pyxrd.file_parsers.exc_parsers import exc_parsers

@storables.register()
class Specimen(DataModel, Storable):
    # MODEL INTEL:
    class Meta(DataModel.Meta):
        properties = [
            PropIntel(name="name", label="Name", data_type=unicode, is_column=True, storable=True, has_widget=True),
            PropIntel(name="sample_name", label="Sample", data_type=unicode, is_column=True, storable=True, has_widget=True),
            PropIntel(name="label", label="Label", data_type=unicode, is_column=True),
            PropIntel(name="sample_length", label="Sample length [cm]", data_type=float, minimum=0.0, is_column=True, storable=True, has_widget=True, widget_type="spin"),
            PropIntel(name="absorption", label="Absorption coeff. (µ*g)", data_type=float, minimum=0.0, is_column=True, storable=True, has_widget=True, widget_type="spin"),
            PropIntel(name="display_calculated", label="Display calculated diffractogram", data_type=bool, is_column=True, storable=True, has_widget=True),
            PropIntel(name="display_experimental", label="Display experimental diffractogram", data_type=bool, is_column=True, storable=True, has_widget=True),
            PropIntel(name="display_phases", label="Display phases seperately", data_type=bool, is_column=True, storable=True, has_widget=True),
            PropIntel(name="display_stats_in_lbl", label="Display Rp in label", data_type=bool, is_column=True, storable=True, has_widget=True),
            PropIntel(name="display_vshift", label="Vertical shift of the plot", data_type=float, is_column=True, storable=True, has_widget=True, widget_type="spin"),
            PropIntel(name="display_vscale", label="Vertical scale of the plot", data_type=float, is_column=True, storable=True, has_widget=True, widget_type="spin"),
            PropIntel(name="display_residuals", label="Display residual patterns", data_type=bool, is_column=True, storable=True, has_widget=True),
            PropIntel(name="display_residual_scale", label="Residual pattern scale", data_type=float, minimum=0.0, is_column=True, storable=True, has_widget=True, widget_type="spin"),
            PropIntel(name="display_derivatives", label="Display derivative patterns", data_type=bool, is_column=True, storable=True, has_widget=True),
            PropIntel(name="goniometer", label="Goniometer", data_type=object, is_column=True, storable=True, has_widget=True, widget_type="custom"),
            PropIntel(name="calculated_pattern", label="Calculated diffractogram", data_type=object, is_column=True, storable=True, has_widget=True, widget_type="xy_list_view"),
            PropIntel(name="experimental_pattern", label="Experimental diffractogram", data_type=object, is_column=True, storable=True, has_widget=True, widget_type="xy_list_view"),
            PropIntel(name="exclusion_ranges", label="Excluded ranges", data_type=object, is_column=True, storable=True, has_widget=True, widget_type="xy_list_view"),
            PropIntel(name="markers", label="Markers", data_type=object, is_column=True, storable=True, widget_type="object_list_view", class_type=Marker),
            PropIntel(name="statistics", label="Statistics", data_type=object, is_column=True),
        ]
        store_id = "Specimen"

        export_filters = xrd_parsers.get_export_file_filters()
        excl_filters = exc_parsers.get_import_file_filters()

    _data_object = None
    @property
    def data_object(self):
        # self._data_object.phases = None #clear this
        self._data_object.goniometer = self.goniometer.data_object
        self._data_object.range_theta = self.__get_range_theta()
        self._data_object.selected_range = self.get_exclusion_selector()
        try:
            self._data_object.observed_intensity = self.experimental_pattern.data_y[:, 0]
        except IndexError:
            self._data_object.observed_intensity = np.array([], dtype=float)
        return self._data_object

    project = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:
    _sample_name = u""
    def get_sample_name(self): return self._sample_name
    def set_sample_name(self, value):
        self._sample_name = value
        self.visuals_changed.emit()

    _name = u""
    def get_name(self): return self._name
    def set_name(self, value):
        self._name = value
        self.visuals_changed.emit()

    _display_calculated = True
    def get_display_calculated(self): return self._display_calculated
    def set_display_calculated(self, value):
        self._display_calculated = bool(value)
        self.visuals_changed.emit()

    _display_experimental = True
    def get_display_experimental(self): return self._display_experimental
    def set_display_experimental(self, value):
        self._display_experimental = bool(value)
        self.visuals_changed.emit()

    _display_vshift = 0.0
    def get_display_vshift(self): return self._display_vshift
    def set_display_vshift(self, value):
        self._display_vshift = float(value)
        self.visuals_changed.emit()

    _display_vscale = 0.0
    def get_display_vscale(self): return self._display_vscale
    def set_display_vscale(self, value):
        self._display_vscale = float(value)
        self.visuals_changed.emit()

    _display_phases = False
    def get_display_phases(self): return self._display_phases
    def set_display_phases(self, value):
        self._display_phases = bool(value)
        self.visuals_changed.emit()

    _display_stats_in_lbl = True
    def get_display_stats_in_lbl(self): return self._display_stats_in_lbl
    def set_display_stats_in_lbl(self, value):
        self._display_stats_in_lbl = bool(value)
        self.visuals_changed.emit()

    _display_residuals = True
    def get_display_residuals(self): return self._display_residuals
    def set_display_residuals(self, value):
        self._display_residuals = bool(value)
        self.visuals_changed.emit()

    _display_derivatives = False
    def get_display_derivatives(self): return self._display_derivatives
    def set_display_derivatives(self, value):
        self._display_derivatives = bool(value)
        self.visuals_changed.emit()

    _display_residual_scale = 1.0
    def get_display_residual_scale(self): return self._display_residual_scale
    def set_display_residual_scale(self, value):
        self._display_residual_scale = float(value)
        self.visuals_changed.emit()

    def get_label(self):
        label = self.sample_name
        if (self.project is not None and self.project.layout_mode == "FULL"):
            if self.display_stats_in_lbl:
                label += "\nR$_p$ = %.1f%%" % not_none(self.statistics.Rp, 0.0)
                label += "\nR$_{wp}$ = %.1f%%" % not_none(self.statistics.Rwp, 0.0)
            if self.display_residual_scale != 1.0:
                label += "\n\nResidual x%0.1f " % not_none(self.display_residual_scale, 1.0)
        return label

    _calculated_pattern = None
    def get_calculated_pattern(self): return self._calculated_pattern
    def set_calculated_pattern(self, value):
        if value != self._calculated_pattern:
            with self.data_changed.hold_and_emit():
                if self._calculated_pattern is not None: self.relieve_model(self._calculated_pattern)
                self._calculated_pattern = value
                if self._calculated_pattern is not None:
                    self.observe_model(self._calculated_pattern)

    _experimental_pattern = None
    def get_experimental_pattern(self): return self._experimental_pattern
    def set_experimental_pattern(self, value):
        if value != self._experimental_pattern:
            with self.data_changed.hold_and_emit():
                if self._experimental_pattern is not None:
                    self.relieve_model(self._experimental_pattern)
                self._experimental_pattern = value
                if self._experimental_pattern is not None:
                    self.observe_model(self._experimental_pattern)

    _exclusion_ranges = None
    def get_exclusion_ranges(self): return self._exclusion_ranges
    def set_exclusion_ranges(self, value):
        if value != self._exclusion_ranges:
            with self.data_changed.hold_and_emit():
                if self._exclusion_ranges is not None:
                    self.relieve_model(self._exclusion_ranges)
                self._exclusion_ranges = value
                if self._exclusion_ranges is not None:
                    self.observe_model(self._exclusion_ranges)


    _goniometer = None
    def get_goniometer(self): return self._goniometer
    def set_goniometer(self, value):
        if value != self._goniometer:
            with self.data_changed.hold_and_emit():
                if self._goniometer is not None:
                    self.relieve_model(self._goniometer)
                self._goniometer = value
                if self._goniometer is not None:
                    self.observe_model(self._goniometer)

    def get_sample_length(self): return self._data_object.sample_length
    def set_sample_length(self, value):
        with self.data_changed.hold_and_emit():
            self._data_object.sample_length = float(value)

    def get_absorption(self): return self._data_object.absorption
    def set_absorption(self, value):
        with self.data_changed.hold_and_emit():
            self._data_object.absorption = float(value)

    statistics = None

    _markers = []
    def get_markers(self): return self._markers
    def set_markers(self, value):
        with self.visuals_changed.hold_and_emit():
            self._markers = value

    @property
    def max_intensity(self):
        """The maximum intensity of the current profile (both calculated and observed"""
        _max = 0.0
        if self.experimental_pattern is not None:
            _max = max(_max, np.max(self.experimental_pattern.max_intensity))
        if self.calculated_pattern is not None:
            _max = max(_max, np.max(self.calculated_pattern.max_intensity))
        return _max

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for a Specimen are:
                name: the name of the specimen
                sample_name: the sample name of the specimen
                sample_length: the sample length of the specimen
                absorption: the mass absorption of the specimen
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
            "exp_cap_value",
            *[names[0] for names in self.Meta.get_local_storable_properties()]
        )
        super(Specimen, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        self._data_object = SpecimenData()

        with self.visuals_changed.hold_and_emit():
            with self.data_changed.hold_and_emit():
                self.name = self.get_kwarg(kwargs, "", "name", "data_name")
                self.sample_name = self.get_kwarg(kwargs, "", "sample_name", "data_sample")
                self.sample_length = float(self.get_kwarg(kwargs, settings.SPECIMEN_SAMPLE_LENGTH, "sample_length", "data_sample_length"))
                self.absorption = float(self.get_kwarg(kwargs, 0.9, "absorption"))

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

                self.goniometer = self.parse_init_arg(
                    self.get_kwarg(kwargs, None, "goniometer", "project_goniometer"),
                    Goniometer, child=True, default_is_class=True,
                    parent=self,
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
    def from_experimental_data(filename, parent, parser=xrd_parsers._group_parser):
        """
            Returns a list of new :class:`~.specimen.models.Specimen`'s loaded
            from `filename`, setting their parent to `parent` using the given
            parser.
        """
        specimens = list()
        xrdfiles = parser.parse(filename)
        for xrdfile in xrdfiles:
            name, sample, generator = xrdfile.filename, xrdfile.name, xrdfile.data
            specimen = Specimen(parent=parent, name=name, sample_name=sample)
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
            self.markers[:] = []
            # for marker in list(self.markers)[::-1]:
            #    self.markers.remove(marker)

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
            self.calculated_pattern.set_data(
                 self.__get_range_theta() * 360. / pi,
                 np.vstack((total_intensity, phase_intensities)).transpose()
            )
            self.update_visuals(phases)
        if settings.GUI_MODE:
            self.statistics.update_statistics(derived=self.display_derivatives)

    def get_phase_intensities(self, phases):
        """
        Gets phase intensities for the provided phases
        
        *phases* a list of phases with length N
        
        :rtype: a 2-tuple containing 2-theta values and phase intensities
        """
        return calculate_phase_intensities(self.data_object, phases)

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
