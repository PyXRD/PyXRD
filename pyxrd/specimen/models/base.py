# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from math import pi, log

from pyxrd.gtkmvc.model import Observer

import numpy as np

from pyxrd.data import settings
from pyxrd.generic.io import storables, Storable
from pyxrd.generic.io.file_parsers import parsers
from pyxrd.generic.models import ExperimentalLine, CalculatedLine, DataModel, PropIntel
from pyxrd.generic.models.mixins import ObjectListStoreChildMixin, ObjectListStoreParentMixin
from pyxrd.generic.models.treemodels import ObjectListStore, XYListStore
from pyxrd.generic.peak_detection import peakdetect
from pyxrd.generic.calculations.specimen import get_phase_intensities
from pyxrd.generic.calculations.data_objects import SpecimenData

from pyxrd.goniometer.models import Goniometer
from markers import Marker
from statistics import Statistics

@storables.register()
class Specimen(DataModel, Storable, ObjectListStoreParentMixin, ObjectListStoreChildMixin):
    # MODEL INTEL:
    __parent_alias__ = 'project'
    __model_intel__ = [
        PropIntel(name="name", label="Name", data_type=unicode, is_column=True, storable=True, has_widget=True),
        PropIntel(name="sample_name", label="Sample", data_type=unicode, is_column=True, storable=True, has_widget=True),
        PropIntel(name="label", label="Label", data_type=unicode, is_column=True),
        PropIntel(name="sample_length", label="Sample length [cm]", data_type=float, minimum=0.0, is_column=True, storable=True, has_widget=True, widget_type="float_entry"),
        PropIntel(name="absorption", label="Absorption coeff. (µ*g)", data_type=float, minimum=0.0, is_column=True, storable=True, has_widget=True, widget_type="float_entry"),
        PropIntel(name="display_calculated", label="Display calculated diffractogram", data_type=bool, is_column=True, storable=True, has_widget=True),
        PropIntel(name="display_experimental", label="Display experimental diffractogram", data_type=bool, is_column=True, storable=True, has_widget=True),
        PropIntel(name="display_phases", label="Display phases seperately", data_type=bool, is_column=True, storable=True, has_widget=True),
        PropIntel(name="display_stats_in_lbl", label="Display Rp in label", data_type=bool, is_column=True, storable=True, has_widget=True),
        PropIntel(name="display_vshift", label="Vertical shift of the plot", data_type=float, is_column=True, storable=True, has_widget=True, widget_type="float_entry"),
        PropIntel(name="display_vscale", label="Vertical scale of the plot", data_type=float, is_column=True, storable=True, has_widget=True, widget_type="float_entry"),
        PropIntel(name="display_residuals", label="Display residual patterns", data_type=bool, is_column=True, storable=True, has_widget=True),
        PropIntel(name="display_derivatives", label="Display derivative patterns", data_type=bool, is_column=True, storable=True, has_widget=True),
        PropIntel(name="goniometer", label="Goniometer", data_type=object, is_column=True, storable=True, has_widget=True, widget_type="custom"),
        PropIntel(name="calculated_pattern", label="Calculated diffractogram", data_type=object, is_column=True, storable=True, has_widget=True, widget_type="tree_view"),
        PropIntel(name="experimental_pattern", label="Experimental diffractogram", data_type=object, is_column=True, storable=True, has_widget=True, widget_type="tree_view"),
        PropIntel(name="exclusion_ranges", label="Excluded ranges", data_type=object, is_column=True, storable=True, has_widget=True, widget_type="tree_view"),
        PropIntel(name="markers", label="Markers", data_type=object, is_column=True, storable=True),
        PropIntel(name="statistics", label="Statistics", data_type=object, is_column=True),
    ]
    __store_id__ = "Specimen"

    __file_filters__ = [parser.file_filter for parser in parsers["xrd"]]
    __export_filters__ = [parser.file_filter for parser in parsers["xrd"] if parser.can_write]
    __excl_filters__ = [parser.file_filter for parser in parsers["exc"]]

    _data_object = None
    @property
    def data_object(self):
        # self._data_object.phases = None #clear this
        self._data_object.goniometer = self.goniometer.data_object
        self._data_object.range_theta = self.__get_range_theta()
        self._data_object.selected_range = self.get_exclusion_selector(self._data_object.range_theta)
        try:
            self._data_object.observed_intensity = self.experimental_pattern.xy_store._model_data_y[0]
        except IndexError:
            self._data_object.observed_intensity = np.array([], dtype=float)
        return self._data_object

    # PROPERTIES:
    _sample_name = u""
    _name = u""
    _display_calculated = True
    _display_experimental = True
    _display_vshift = 0.0
    _display_vscale = 1.0
    _display_phases = False
    _display_stats_in_lbl = True
    _display_residuals = True
    _display_derivatives = True
    @DataModel.getter("sample_name", "name", "display_vshift", "display_vscale",
         "display_phases", "display_stats_in_lbl",
         "display_residuals", "display_derivatives",
         "display_calculated", "display_experimental")
    def get_visual(self, prop_name):
        return getattr(self, "_%s" % prop_name)
    @DataModel.setter("sample_name", "name", "display_vshift", "display_vscale",
        "display_phases", "display_stats_in_lbl",
        "display_residuals", "display_derivatives",
        "display_calculated", "display_experimental")
    def set_visual(self, prop_name, value):
        with self.visuals_changed.hold_and_emit():
            if self.get_prop_intel_by_name(prop_name).data_type == float:
                try: value = float(value)
                except ValueError: return
            setattr(self, "_%s" % prop_name, value)
            self.liststore_item_changed()

    def get_label_value(self):
        if self.display_stats_in_lbl and (self.project is not None and self.project.layout_mode == "FULL"):
            label = self.sample_name
            label += "\nRp = %.1f%%" % self.statistics.Rp
            label += "\nRp' = %.1f%%" % self.statistics.Rpder
            return label
        else:
            return self.sample_name

    _calculated_pattern = None
    def get_calculated_pattern_value(self): return self._calculated_pattern
    def set_calculated_pattern_value(self, value):
        if value != self._calculated_pattern:
            with self.data_changed.hold_and_emit():
                if self._calculated_pattern is not None: self.relieve_model(self._calculated_pattern)
                self._calculated_pattern = value
                if self._calculated_pattern is not None:
                    self.observe_model(self._calculated_pattern)

    _experimental_pattern = None
    def get_experimental_pattern_value(self): return self._experimental_pattern
    def set_experimental_pattern_value(self, value):
        if value != self._experimental_pattern:
            with self.data_changed.hold_and_emit():
                if self._experimental_pattern is not None:
                    self.relieve_model(self._experimental_pattern)
                self._experimental_pattern = value
                if self._experimental_pattern is not None:
                    self.observe_model(self._experimental_pattern)

    _exclusion_ranges = None
    def get_exclusion_ranges_value(self): return self._exclusion_ranges
    def set_exclusion_ranges_value(self, value):
        if value != self._exclusion_ranges:
            with self.data_changed.hold_and_emit():
                if self._exclusion_ranges is not None:
                    pass
                self._exclusion_ranges = value
                if self._exclusion_ranges is not None:
                    pass

    _goniometer = None
    def get_goniometer_value(self): return self._goniometer
    def set_goniometer_value(self, value):
        if value != self._goniometer:
            with self.data_changed.hold_and_emit():
                if self._goniometer is not None:
                    self.relieve_model(self._goniometer)
                self._goniometer = value
                if self._goniometer is not None:
                    self.observe_model(self._goniometer)

    @DataModel.getter("sample_length", "absorption")
    def get_sample_length_value(self, prop_name):
        return getattr(self._data_object, prop_name)
    @DataModel.setter("sample_length", "absorption")
    def set_sample_length_value(self, prop_name, value):
        with self.data_changed.hold_and_emit():
            setattr(self._data_object, prop_name, value)

    statistics = None

    _markers = None
    def get_markers_value(self): return self._markers

    @property
    def max_intensity(self):
        """The maximum intensity of the current profile (both calculated and observed"""
        if self.experimental_pattern and self.calculated_pattern:
            return max(np.max(self.experimental_pattern.max_intensity), np.max(self.calculated_pattern.max_intensity))
        else:
            return 0.0

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
        super(Specimen, self).__init__(*args, **kwargs)

        self._data_object = SpecimenData()

        with self.visuals_changed.hold_and_emit():
            with self.data_changed.hold_and_emit():
                self.name = self.get_kwarg(kwargs, "", "name", "data_name")
                self.sample_name = self.get_kwarg(kwargs, "", "sample_name", "data_sample")
                self.sample_length = float(self.get_kwarg(kwargs, 1.25, "sample_length", "data_sample_length"))
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

                calc_pattern_old_kwargs = {}
                for kw in ("exp_color", "exp_lw", "inherit_exp_color", "inherit_exp_lw"):
                    if kw in kwargs:
                        calc_pattern_old_kwargs[kw.replace("exp_", "")] = kwargs.pop(kw)
                self.experimental_pattern = self.parse_init_arg(
                    self.get_kwarg(kwargs, None, "experimental_pattern", "data_experimental_pattern"),
                    ExperimentalLine,
                    child=True, default_is_class=True,
                    label="Experimental Profile",
                    parent=self,
                    **calc_pattern_old_kwargs
                )

                exclusion_ranges = self.get_kwarg(kwargs, None, "exclusion_ranges", "data_exclusion_ranges")
                self.exclusion_ranges = self.parse_init_arg(exclusion_ranges, XYListStore())
                self.exclusion_ranges.connect("item-removed", self.on_exclusion_range_changed)
                self.exclusion_ranges.connect("item-inserted", self.on_exclusion_range_changed)
                self.exclusion_ranges.connect("row-changed", self.on_exclusion_range_changed)

                self.goniometer = self.parse_init_arg(
                    self.get_kwarg(kwargs, None, "goniometer", "project_goniometer"),
                    Goniometer(parent=self), child=True
                )

                markers = self.get_kwarg(kwargs, None, "markers", "data_markers")
                self._markers = self.parse_liststore_arg(markers, ObjectListStore, Marker)
                for marker in self._markers._model_data:
                    self.observe_model(marker)
                self.markers.connect("item-removed", self.on_marker_removed)
                self.markers.connect("item-inserted", self.on_marker_inserted)

                self.display_vshift = float(self.get_kwarg(kwargs, 0.0, "display_vshift"))
                self.display_vscale = float(self.get_kwarg(kwargs, 1.0, "display_vscale"))
                self.display_calculated = bool(self.get_kwarg(kwargs, True, "display_calculated"))
                self.display_experimental = bool(self.get_kwarg(kwargs, True, "display_experimental"))
                self.display_residuals = bool(self.get_kwarg(kwargs, True, "display_residuals"))
                self.display_derivatives = bool(self.get_kwarg(kwargs, True, "display_derivatives"))
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
    @Observer.observe("data_changed", signal=True)
    def notify_data_changed(self, model, prop_name, info):
        self.data_changed.emit() # propagate signal

    @Observer.observe("visuals_changed", signal=True)
    def notify_visuals_changed(self, model, prop_name, info):
        self.visuals_changed.emit() # propagate signal

    def on_exclusion_range_changed(self, model, item, *args):
        self.data_changed.emit() # propagate signal

    def on_marker_removed(self, model, item):
        with self.visuals_changed.hold_and_emit():
            self.relieve_model(item)
            item.parent = None

    def on_marker_inserted(self, model, item):
        with self.visuals_changed.hold_and_emit():
            self.observe_model(item)
            item.parent = self

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    @staticmethod
    def from_experimental_data(filename, parent, parser):
        specimens = list()
        xrdfiles = parser.parse(filename)
        for xrdfile in xrdfiles:
            name, sample, generator = xrdfile.filename, xrdfile.name, xrdfile.data
            specimen = Specimen(parent=parent, name=name, sample_name=sample)
            specimen.experimental_pattern.xy_store.load_data_from_generator(generator, clear=True)
            specimens.append(specimen)

        return specimens

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def auto_add_peaks(self, tmodel):
        """
        Automagically add peak markers
        
        *tmodel* a :class:`~specimen.models.ThresholdSelector` model
        """
        threshold = tmodel.sel_threshold
        base = 1 if (tmodel.pattern == "exp") else 2
        data_x, data_y = tmodel.get_xy()
        maxtab, mintab = peakdetect(data_y, data_x, 5, threshold) # @UnusedVariable

        mpositions = []
        for marker in self.markers._model_data:
            mpositions.append(marker.position)

        with self.visuals_changed.hold():
            i = 1
            for x, y in maxtab: # @UnusedVariable
                if not x in mpositions:
                    nm = self.goniometer.get_nm_from_2t(x) if x != 0 else 0
                    new_marker = Marker("%%.%df" % (3 + min(int(log(nm, 10)), 0)) % nm, parent=self, position=x, base=base)
                    self.markers.append(new_marker)
                i += 1

    def get_exclusion_selector(self, x):
        """
        Get the numpy selector array for non-excluded data
        
        *x* a numpy ndarray containing the 2-theta values (in radians)
        
        :rtype: a numpy ndarray
        """
        if x is not None:
            x = x * 360.0 / pi
            selector = np.ones(x.shape, dtype=bool)
            for x0, x1 in zip(*np.sort(np.asarray(self.exclusion_ranges.get_raw_model_data()), axis=0)):
                new_selector = ((x < x0) | (x > x1))
                selector = selector & new_selector
            return selector
        return None

    def get_exclusion_xy(self):
        """
        Get an numpy array containing only non-excluded data X and Y data
                
        :rtype: a tuple containing 4 numpy ndarray's: the experimental X and Y
        data and the calculated X and Y data
        """
        ex, ey = self.experimental_pattern.xy_store.get_raw_model_data()
        cx, cy = self.calculated_pattern.xy_store.get_raw_model_data()
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
                total_intensity,
                phase_intensities,
                phases
            )
        if settings.GUI_MODE:
            self.statistics.update_statistics()

    def get_phase_intensities(self, phases):
        """
        Gets phase intensities for the provided phases
        
        *phases* a list of phases with length N
        
        :rtype: a 2-tuple containing 2-theta values and phase intensities
        """
        return get_phase_intensities(self.data_object, phases)

    def __get_range_theta(self):
        if self.experimental_pattern.xy_store._model_data_x.size <= 1:
            return self.goniometer.get_default_theta_range()
        else:
            return np.radians(self.experimental_pattern.xy_store._model_data_x * 0.5)

    def __str__(self):
        return "<'%s' Specimen>" % self.name

    pass # end of class
