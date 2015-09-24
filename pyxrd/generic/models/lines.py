# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
from pyxrd.generic.models.properties import InheritableMixin
from mvc.models.properties.tools import modify
logger = logging.getLogger(__name__)

import numpy as np
from scipy import stats
from scipy.interpolate import interp1d
from scipy.integrate import trapz

from mvc.models.xydata import XYData
from mvc.models.properties import *

from pyxrd.data import settings
from pyxrd.generic.io import storables, Storable
from pyxrd.generic.custom_math import smooth, add_noise

from pyxrd.generic.models.base import DataModel
from pyxrd.generic.utils import not_none
from pyxrd.generic.peak_detection import multi_peakdetect

#from pyxrd.file_parsers.ascii_parser import ASCIIParser

@storables.register()
class StorableXYData(DataModel, XYData, Storable):
    """
        A storable XYData model with additional I/O and CRUD abilities.
    """

    class Meta(XYData.Meta):
        store_id = "StorableXYData"

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for a PyXRDLine are:
                data: the actual data containing x and y values
                label: the label for this line
                color: the color of this line
                inherit_color: whether to use the parent-level color or its own
                lw: the line width of this line
                inherit_lw: whether to use the parent-level line width or its own
        """
        if "z_data" in kwargs: del kwargs["z_data"]
        if "xy_store" in kwargs:
            kwargs["data"] = kwargs.pop("xy_store")
        super(StorableXYData, self).__init__(*args, **kwargs)

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def json_properties(self):
        props = super(XYData, self).json_properties()
        props["data"] = self._serialize_data()
        return props

    def apply_correction(self, correction):
        self.data_y = self.data_y * correction[:, np.newaxis]

    def save_data(self, parser, filename, **kwargs):
        if self.data_y.shape[1] > 1:
            kwargs["header"] = ["2θ", ] + (not_none(self.y_names, []))
        parser.write(filename, self.data_x, self._data_y.transpose(), **kwargs)

    def load_data(self, parser, filename, clear=True):
        """
            Loads data using passed filename and parser, which are passed on to
            the load_data_from_generator method.
            If clear=True the x-y data is cleared first.
        """
        xrdfiles = parser.parse(filename)
        if xrdfiles:
            self.load_data_from_generator(xrdfiles[0].data, clear=clear)
            
    def load_data_from_generator(self, generator, clear=True):
        with self.data_changed.hold_and_emit():
            super(StorableXYData, self).load_data_from_generator(generator, clear=clear)

    def set_data(self, x, y):
        """
            Sets data using the supplied x, y1, ..., yn arrays.
        """
        with self.data_changed.hold_and_emit():
            super(StorableXYData, self).set_data(x, y)

    def set_value(self, i, j, value):
        with self.data_changed.hold_and_emit():
            super(StorableXYData, self).set_value(i, j, value)

    def append(self, x, y):
        """
            Appends data using the supplied x, y1, ..., yn arrays.
        """
        with self.data_changed.hold_and_emit():
            super(StorableXYData, self).append(x, y)

    def insert(self, pos, x, y):
        """
            Inserts data using the supplied x, y1, ..., yn arrays at the given
            position.
        """
        with self.data_changed.hold_and_emit():
            super(StorableXYData, self).insert(pos, x, y)

    def remove_from_indeces(self, *indeces):
        with self.data_changed.hold_and_emit():
            super(StorableXYData, self).remove_from_indeces(*indeces)

    pass # end of class

@storables.register()
class PyXRDLine(StorableXYData):
    """
        A PyXRDLine is an abstract attribute holder for a real 'Line' object,
        whatever the plotting library used may be. Attributes are line width and
        color.        
    """

    # MODEL INTEL:
    class Meta(StorableXYData.Meta):
        store_id = "PyXRDLine"

    # OBSERVABLE PROPERTIES:

    #: The line label
    label = StringProperty(
        default="", text="Label", persistent=True
    )

    #: The line color
    color = StringProperty(
        default="#000000", text="Label",
        visible=True, persistent=True, widget_type="color",
        inherit_flag="inherit_color", inherit_from="parent.parent.display_exp_color",
        signal_name="visuals_changed",
        mix_with=(InheritableMixin, SignalMixin)
    )

    #: Flag indicating whether to use the grandparents color yes/no
    inherit_color = BoolProperty(
        default=True, text="Inherit color",
        visible=True, persistent=True,
        signal_name="visuals_changed", mix_with=(SignalMixin,)
    )

    #: The linewidth in points
    lw = FloatProperty(
        default=2.0, text="Linewidth",
        visible=True, persistent=True, widget_type="spin",
        inherit_flag="inherit_lw", inherit_from="parent.parent.display_exp_lw",
        signal_name="visuals_changed",
        mix_with=(InheritableMixin, SignalMixin),
    )

    #: Flag indicating whether to use the grandparents linewidth yes/no
    inherit_lw = BoolProperty(
        default=True, text="Inherit linewidth",
        visible=True, persistent=True,
        signal_name="visuals_changed", mix_with=(SignalMixin,),
    )

    #: A short string describing the (matplotlib) linestyle
    ls = StringChoiceProperty(
        default=settings.EXPERIMENTAL_LINESTYLE, text="Linestyle",
        visible=True, persistent=True, choices=settings.PATTERN_LINE_STYLES,
        mix_with=(InheritableMixin, SignalMixin,), signal_name="visuals_changed",
        inherit_flag="inherit_ls", inherit_from="parent.parent.display_exp_ls",
    )

    #: Flag indicating whether to use the grandparents linestyle yes/no
    inherit_ls = BoolProperty(
        default=True, text="Inherit linestyle",
        visible=True, persistent=True,
        mix_with=(SignalMixin,), signal_name="visuals_changed"
    )

    #: A short string describing the (matplotlib) marker
    marker = StringChoiceProperty(
        default=settings.EXPERIMENTAL_MARKER, text="Marker",
        visible=True, persistent=True, choices=settings.PATTERN_MARKERS,
        mix_with=(InheritableMixin, SignalMixin,), signal_name="visuals_changed",
        inherit_flag="inherit_marker", inherit_from="parent.parent.display_exp_marker",
    )

    #: Flag indicating whether to use the grandparents linewidth yes/no
    inherit_marker = BoolProperty(
        default=True, text="Inherit marker",
        visible=True, persistent=True,
        mix_with=(SignalMixin,), signal_name="visuals_changed",
    )

    # REGULAR PROPERTIES:
    @property
    def max_intensity(self):
        return self.max_y

    @property
    def min_intensity(self):
        return self.min_y

    @property
    def abs_max_intensity(self):
        return self.abs_max_y

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for a PyXRDLine are:
                data: the actual data containing x and y values
                label: the label for this line
                color: the color of this line
                inherit_color: whether to use the parent-level color or its own
                lw: the line width of this line
                inherit_lw: whether to use the parent-level line width or its own
                ls: the line style of this line
                inherit_ls: whether to use the parent-level line style or its own
                marker: the line marker of this line
                inherit_marker: whether to use the parent-level line marker or its own
        """
        my_kwargs = self.pop_kwargs(kwargs,
            *[prop.label for prop in PyXRDLine.Meta.get_local_persistent_properties()]
        )
        super(PyXRDLine, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.visuals_changed.hold():
            self.label = self.get_kwarg(kwargs, self.label, "label")
            self.color = self.get_kwarg(kwargs, self.color, "color")
            self.inherit_color = bool(self.get_kwarg(kwargs, self.inherit_color, "inherit_color"))
            self.lw = float(self.get_kwarg(kwargs, self.lw, "lw"))
            self.inherit_lw = bool(self.get_kwarg(kwargs, self.inherit_lw, "inherit_lw"))
            self.ls = self.get_kwarg(kwargs, self.ls, "ls")
            self.inherit_ls = bool(self.get_kwarg(kwargs, self.inherit_ls, "inherit_ls"))
            self.marker = self.get_kwarg(kwargs, self.marker, "marker")
            self.inherit_marker = bool(self.get_kwarg(kwargs, self.inherit_marker, "inherit_marker"))

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    @classmethod
    def from_json(cls, **kwargs): # @ReservedAssignment
        if "xy_store" in kwargs:
            if "type" in kwargs["xy_store"]:
                kwargs["data"] = kwargs["xy_store"]["properties"]["data"]
        elif "xy_data" in kwargs:
            if "type" in kwargs["xy_data"]:
                kwargs["data"] = kwargs["xy_data"]["properties"]["data"]
            kwargs["label"] = kwargs["data_label"]
            del kwargs["data_name"]
            del kwargs["data_label"]
            del kwargs["xy_data"]
        return cls(**kwargs)

    # ------------------------------------------------------------
    #      Convenience Methods & Functions
    # ------------------------------------------------------------
    def interpolate(self, *x_vals, **kwargs):
        """
            Returns a list of (x, y) tuples for the passed x values. An optional
            column keyword argument can be passed to select a column, by default
            the first y-column is used. Returned y-values are interpolated. 
        """
        column = kwargs.get("column", 0)
        f = interp1d(self.data_x, self.data_y[:, column])
        return zip(x_vals, f(x_vals))

    def get_plotted_y_at_x(self, x):
        """
            Gets the (interpolated) plotted value at the given x position.
            If this line has not been plotted (or does not have
            access to a '__plot_line' attribute set by the plotting routines)
            it will return 0.
        """
        try:
            xdata, ydata = getattr(self, "__plot_line").get_data()
        except AttributeError:
            logging.exception("Attribute error when trying to get plotter data at x position!")
        else:
            if len(xdata) > 0 and len(ydata) > 0:
                return np.interp(x, xdata, ydata)
        return 0

    def calculate_npeaks_for(self, max_threshold, steps):
        """
            Calculates the number of peaks for `steps` threshold values between
            0 and `max_threshold`. Returns a tuple containing two lists with the
            threshold values and the corresponding number of peaks. 
        """
        length = self.data_x.size

        resolution = length / (self.data_x[-1] - self.data_x[0])
        delta_angle = 0.05
        window = int(delta_angle * resolution)
        window += (window % 2) * 2

        steps = max(steps, 2) - 1
        factor = max_threshold / steps

        deltas = [i * factor for i in range(0, steps)]

        numpeaks = []

        maxtabs, mintabs = multi_peakdetect(self.data_y[:, 0], self.data_x, 5, deltas)
        for maxtab, _ in zip(maxtabs, mintabs):
            numpeak = len(maxtab)
            numpeaks.append(numpeak)
        numpeaks = map(float, numpeaks)

        return deltas, numpeaks

    def get_best_threshold(self, max_threshold=None, steps=None):
        """
            Estimates the best threshold for peak detection using an
            iterative algorithm. Assumes there is a linear contribution from noise.
            Returns a 4-tuple containing the selected threshold, the maximum
            threshold, a list of threshold values and a list with the corresponding
            number of peaks.
        """
        length = self.data_x.size
        steps = not_none(steps, 20)
        threshold = 0.1
        max_threshold = not_none(max_threshold, threshold * 3.2)

        def get_new_threshold(threshold, deltas, num_peaks, ln):
            # Left side line:
            x = deltas[:ln]
            y = num_peaks[:ln]
            slope, intercept, R, _, _ = stats.linregress(x, y)
            return R, -intercept / slope

        if length > 2:
            # Adjust the first distribution:
            deltas, num_peaks = self.calculate_npeaks_for(max_threshold, steps)

            #  Fit several lines with increasing number of points from the
            #  generated threshold / marker count graph. Stop when the
            #  R-coefficiënt drops below 0.95 (past linear increase from noise)
            #  Then repeat this by increasing the resolution of data points
            #  and continue until the result does not change anymore

            last_threshold = None
            solution = False
            max_iters = 10
            min_iters = 3
            itercount = 0
            while not solution:
                # Number of points to use for the lin regress:
                ln = 4
                # Maximum number of points to use:
                max_ln = len(deltas)
                # Flag indicating if we can stop searching for the linear part
                stop = False
                while not stop:
                    R, threshold = get_new_threshold(threshold, deltas, num_peaks, ln)
                    max_threshold = threshold * 3.2
                    if abs(R) < 0.98 or ln >= max_ln:
                        stop = True
                    else:
                        ln += 1
                itercount += 1 # Increase # of iterations
                if last_threshold:
                    # Check if we have run at least `min_iters`, at most `max_iters`
                    # and have not reached an equilibrium.
                    solution = bool(
                        itercount > min_iters and not
                        (
                            itercount <= max_iters and
                            last_threshold - threshold >= 0.001
                        )
                    )
                    if not solution:
                        deltas, num_peaks = self.calculate_npeaks_for(max_threshold, steps)
                last_threshold = threshold

            return (deltas, num_peaks), threshold, max_threshold
        else:
            return ([], []), threshold, max_threshold


    pass # end of class

@storables.register()
class CalculatedLine(PyXRDLine):

    # MODEL INTEL:
    class Meta(PyXRDLine.Meta):
        store_id = "CalculatedLine"
        inherit_format = "display_calc_%s"

    specimen = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:

    phase_colors = ListProperty(
        default=[], test="Phase colors",
        mix_with=(SignalMixin,),
        signal_name="visuals_changed",
    )

    #: The line color
    color = modify(PyXRDLine.color,
        default=settings.CALCULATED_COLOR,
        inherit_from="parent.parent.display_calc_color"
    )

    #: The linewidth in points
    lw = modify(PyXRDLine.lw,
        default=settings.CALCULATED_LINEWIDTH,
        inherit_from="parent.parent.display_calc_lw"
    )

    #: A short string describing the (matplotlib) linestyle
    ls = modify(PyXRDLine.ls,
        default=settings.CALCULATED_LINESTYLE,
        inherit_from="parent.parent.display_calc_ls"
    )

    #: A short string describing the (matplotlib) marker
    marker = modify(PyXRDLine.marker,
        default=settings.CALCULATED_MARKER,
        inherit_from="parent.parent.display_calc_marker"
    )

    pass # end of class

@storables.register()
class ExperimentalLine(PyXRDLine):

    # MODEL INTEL:
    class Meta(PyXRDLine.Meta):
        store_id = "ExperimentalLine"

    specimen = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:

    #: The line color
    color = modify(PyXRDLine.color,
        default=settings.EXPERIMENTAL_COLOR,
        inherit_from="parent.parent.display_exp_color"
    )
    #: The linewidth in points
    lw = modify(PyXRDLine.lw,
        default=settings.EXPERIMENTAL_LINEWIDTH,
        inherit_from="parent.parent.display_exp_lw"
    )

    #: A short string describing the (matplotlib) linestyle
    ls = modify(PyXRDLine.ls,
        default=settings.EXPERIMENTAL_LINESTYLE,
        inherit_from="parent.parent.display_exp_ls"
    )

    #: A short string describing the (matplotlib) marker
    marker = modify(PyXRDLine.marker,
        default=settings.EXPERIMENTAL_MARKER,
        inherit_from="parent.parent.display_exp_marker"
    )

    #: The value to cap the pattern at (in raw values)
    cap_value = FloatProperty(
        default=0.0, text="Cap value",
        persistent=True, visible=True, widget_type="float_entry",
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    @property
    def max_intensity(self):
        max_value = super(ExperimentalLine, self).max_intensity
        if self.cap_value > 0:
            max_value = min(max_value, self.cap_value)
        return max_value

    ###########################################################################

    #: The background offset value
    bg_position = FloatProperty(
        default=0.0, text="Background offset",
        persistent=False, visible=True, widget_type="float_entry",
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: The background scale
    bg_scale = FloatProperty(
        default=1.0, text="Background scale",
        persistent=False, visible=True, widget_type="float_entry",
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: The background pattern or None for linear patterns
    bg_pattern = LabeledProperty(
        default=None, text="Background pattern",
        persistent=False, visible=False,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: The background type: pattern or linear
    bg_type = IntegerChoiceProperty(
        default=0, text="Background type", choices=settings.PATTERN_BG_TYPES,
        persistent=False, visible=True,
        signal_name="visuals_changed", set_action_name="find_bg_position",
        mix_with=(SignalMixin, SetActionMixin,)
    )

    def get_bg_type_lbl(self):
        return settings.PATTERN_BG_TYPES[self.bg_type]

    ###########################################################################

    #: Pattern smoothing type
    smooth_type = IntegerChoiceProperty(
        default=0, text="Smooth type", choices=settings.PATTERN_SMOOTH_TYPES,
        persistent=False, visible=True,
        signal_name="visuals_changed", set_action_name="setup_smooth_variables",
        mix_with=(SignalMixin, SetActionMixin,)
    )

    smooth_pattern = None

    #: The smooth degree
    smooth_degree = IntegerProperty(
        default=0, text="Smooth degree",
        persistent=False, visible=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    ###########################################################################

    #: The noise fraction to add
    noise_fraction = FloatProperty(
        default=0.0, text="Noise fraction",
        persistent=False, visible=True, widget_type="spin",
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    ###########################################################################

    #: The pattern shift correction value
    shift_value = FloatProperty(
        default=0.0, text="Shift value",
        persistent=False, visible=True, widget_type="float_entry",
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: Shift reference position
    shift_position = FloatChoiceProperty(
        default=0.42574, text="Shift position", choices=settings.PATTERN_SMOOTH_TYPES,
        persistent=False, visible=True,
        signal_name="visuals_changed", set_action_name="setup_shift_variables",
        mix_with=(SignalMixin, SetActionMixin,)
    )

    ###########################################################################

    #: The peak area calculation start position
    area_startx = FloatProperty(
        default=0.0, text="Peak area start position",
        persistent=False, visible=True, widget_type="float_entry",
        set_action_name="update_area_pattern",
        mix_with=(SetActionMixin,)
    )

    #: The peak area calculation end position
    area_endx = FloatProperty(
        default=0.0, text="Peak area end position",
        persistent=False, visible=True, widget_type="float_entry",
        action_name="update_area_pattern",
        mix_with=(SetActionMixin,)
    )

    #: The peak area value
    area_result = FloatProperty(
        default=0.0, text="Peak area value",
        persistent=False, visible=True, widget_type="label",
    )

    #: The pattern where a peak area was calculated for
    area_pattern = LabeledProperty(
        default=None, text="Peak area pattern",
        persistent=False, visible=False,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    ###########################################################################

    #: The strip peak start position
    strip_startx = FloatProperty(
        default=0.0, text="Strip peak start position",
        persistent=False, visible=True, widget_type="float_entry",
        set_action_name="update_strip_pattern",
        mix_with=(SetActionMixin,)
    )

    #: The strip peak end position
    strip_endx = FloatProperty(
        default=0.0, text="Strip peak end position",
        persistent=False, visible=True, widget_type="float_entry",
        set_action_name="update_strip_pattern",
        mix_with=(SetActionMixin,)
    )

    #: The stripped peak pattern
    stripped_pattern = LabeledProperty(
        default=None, text="Strip peak pattern",
        persistent=False, visible=False,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: The stripped peak pattern noise
    noise_level = FloatProperty(
        default=0.0, text="Strip peak noise level",
        persistent=False, visible=True, widget_type="float_entry",
        set_action_name="update_strip_pattern_noise",
        mix_with=(SetActionMixin,)
    )

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, cap_value=0.0, *args, **kwargs):
        """
            Valid keyword arguments for a ExperimentalLine are:
                cap_value: the value (in raw counts) at which to cap
                 the experimental pattern  
        """
        super(ExperimentalLine, self).__init__(*args, **kwargs)
        self.cap_value = cap_value

    # ------------------------------------------------------------
    #      Background Removal
    # ------------------------------------------------------------
    def remove_background(self):
        with self.data_changed.hold_and_emit():
            bg = None
            if self.bg_type == 0:
                bg = self.bg_position
            elif self.bg_type == 1 and self.bg_pattern is not None and not (self.bg_position == 0 and self.bg_scale == 0):
                bg = self.bg_pattern * self.bg_scale + self.bg_position
            if bg is not None:
                self.data_y[:, 0] -= bg
            self.clear_bg_variables()

    def find_bg_position(self):
        try:
            self.bg_position = np.min(self.data_y)
        except ValueError:
            return 0.0

    def clear_bg_variables(self):
        with self.visuals_changed.hold_and_emit():
            self.bg_pattern = None
            self.bg_scale = 0.0
            self.bg_position = 0.0

    # ------------------------------------------------------------
    #       Data Smoothing
    # ------------------------------------------------------------
    def smooth_data(self):
        with self.data_changed.hold_and_emit():
            if self.smooth_degree > 0:
                degree = int(self.smooth_degree)
                self.data_y[:, 0] = smooth(self.data_y[:, 0], degree)
            self.smooth_degree = 0.0

    def setup_smooth_variables(self):
        with self.visuals_changed.hold_and_emit():
            self.smooth_degree = 5.0

    def clear_smooth_variables(self):
        with self.visuals_changed.hold_and_emit():
            self.smooth_degree = 0.0

    # ------------------------------------------------------------
    #       Noise adding
    # ------------------------------------------------------------
    def add_noise(self):
        with self.data_changed.hold_and_emit():
            if self.noise_fraction > 0:
                noisified = add_noise(self.data_y[:, 0], self.noise_fraction)
                self.set_data(self.data_x, noisified)
            self.noise_fraction = 0.0

    def clear_noise_variables(self):
        with self.visuals_changed.hold_and_emit():
            self.noise_fraction = 0.0

    # ------------------------------------------------------------
    #       Data Shifting
    # ------------------------------------------------------------
    def shift_data(self):
        with self.data_changed.hold_and_emit():
            if self.shift_value != 0.0:
                if settings.PATTERN_SHIFT_TYPE == "Linear":
                    self.data_x = self.data_x - self.shift_value
                    if self.specimen is not None:
                        with self.specimen.visuals_changed.hold():
                            for marker in self.specimen.markers:
                                marker.position = marker.position - self.shift_value
                elif settings.PATTERN_SHIFT_TYPE == "Displacement":
                    position = self.specimen.goniometer.get_t_from_nm(self.shift_position)
                    displacement = 0.5 * self.specimen.goniometer.radius * self.shift_value / np.cos(position / 180 * np.pi)
                    correction = 2 * displacement * np.cos(self.data_x / 2 / 180 * np.pi) / self.specimen.goniometer.radius
                    self.data_x = self.data_x - correction

            self.shift_value = 0.0

    def setup_shift_variables(self):
        with self.visuals_changed.hold_and_emit():
            position = self.specimen.goniometer.get_2t_from_nm(self.shift_position)
            if position > 0.1:
                max_x = position + 0.5
                min_x = position - 0.5
                condition = (self.data_x >= min_x) & (self.data_x <= max_x)
                section_x, section_y = np.extract(condition, self.data_x), np.extract(condition, self.data_y[:, 0])
                try:
                    #TODO to exclude noise it'd be better to first interpolate
                    # or smooth the data and then find the max.
                    actual_position = section_x[np.argmax(section_y)]
                except ValueError:
                    actual_position = position
                self.shift_value = actual_position - position

    def clear_shift_variables(self):
        with self.visuals_changed.hold_and_emit():
            self.shift_value = 0

    # ------------------------------------------------------------
    #       Peak area calculation
    # ------------------------------------------------------------
    area_slope = 0.0
    avg_area_starty = 0.0
    avg_area_endy = 0.0
    def update_area_pattern(self):
        with self.visuals_changed.hold_and_emit():
            if self.area_endx < self.area_startx:
                self.area_endx = self.area_startx + 1.0
                return # previous line will have re-invoked this method

            # calculate average starting point y value
            condition = (self.data_x >= self.area_startx - 0.1) & (self.data_x <= self.area_startx + 0.1)
            section = np.extract(condition, self.data_y[:, 0])
            self.avg_area_starty = np.min(section)

            # calculate average ending point y value
            condition = (self.data_x >= self.area_endx - 0.1) & (self.data_x <= self.area_endx + 0.1)
            section = np.extract(condition, self.data_y[:, 0])
            self.avg_area_endy = np.min(section)

            # Calculate new bg slope
            self.area_slope = (self.avg_area_starty - self.avg_area_endy) / (self.area_startx - self.area_endx)

            # Get the x-values in between start and end point:
            condition = (self.data_x >= self.area_startx) & (self.data_x <= self.area_endx)
            section_x = np.extract(condition, self.data_x)
            section_y = np.extract(condition, self.data_y)
            bg_curve = (self.area_slope * (section_x - self.area_startx) + self.avg_area_starty)

            #Calculate the peak area:
            self.area_result = abs(trapz(section_y, x=section_x) - trapz(bg_curve, x=section_x))

            # Calculate the new y-values:
            self.area_pattern = (section_x, bg_curve, section_y)

    def clear_area_variables(self):
        with self.visuals_changed.hold_and_emit():
            self._area_startx = 0.0
            self._area_pattern = None
            self._area_endx = 0.0
            self.area_result = 0.0


    # ------------------------------------------------------------
    #       Peak stripping
    # ------------------------------------------------------------
    def strip_peak(self):
        with self.data_changed.hold_and_emit():
            if self.stripped_pattern is not None:
                stripx, stripy = self.stripped_pattern
                indeces = ((self.data_x >= self.strip_startx) & (self.data_x <= self.strip_endx)).nonzero()[0]
                np.put(self.data_y[:, 0], indeces, stripy)
            self._strip_startx = 0.0
            self._stripped_pattern = None
            self.strip_endx = 0.0

    strip_slope = 0.0
    avg_starty = 0.0
    avg_endy = 0.0
    block_strip = False

    def update_strip_pattern_noise(self):
        with self.visuals_changed.hold_and_emit():
            # Get the x-values in between start and end point:
            condition = (self.data_x >= self.strip_startx) & (self.data_x <= self.strip_endx)
            section_x = np.extract(condition, self.data_x)

            # Calculate the new y-values, add noise according to noise_level
            noise = self.avg_endy * 2 * (np.random.rand(*section_x.shape) - 0.5) * self.noise_level
            section_y = (self.strip_slope * (section_x - self.strip_startx) + self.avg_starty) + noise
            self.stripped_pattern = (section_x, section_y)

    def update_strip_pattern(self):
        with self.visuals_changed.hold_and_emit():
            if self.strip_endx < self.strip_startx:
                self.strip_endx = self.strip_startx + 1.0
                return # previous line will have re-invoked this method

            if not self.block_strip:
                self.block_strip = True

                # calculate average starting point y value
                condition = (self.data_x >= self.strip_startx - 0.1) & (self.data_x <= self.strip_startx + 0.1)
                section = np.extract(condition, self.data_y[:, 0])
                self.avg_starty = np.average(section)
                noise_starty = 2 * np.std(section) / self.avg_starty

                # calculate average ending point y value
                condition = (self.data_x >= self.strip_endx - 0.1) & (self.data_x <= self.strip_endx + 0.1)
                section = np.extract(condition, self.data_y[:, 0])
                self.avg_endy = np.average(section)
                noise_endy = 2 * np.std(section) / self.avg_starty

                # Calculate new slope and noise level
                self.strip_slope = (self.avg_starty - self.avg_endy) / (self.strip_startx - self.strip_endx)
                self.noise_level = (noise_starty + noise_endy) * 0.5

                self.update_strip_pattern_noise()

    def clear_strip_variables(self):
        with self.visuals_changed.hold_and_emit():
            self._strip_startx = 0.0
            self._strip_pattern = None
            self.strip_start_x = 0.0


    pass # end of class
