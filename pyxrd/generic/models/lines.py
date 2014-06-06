# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import numpy as np
from scipy.interpolate import interp1d
from scipy.integrate import trapz

from pyxrd.mvc import PropIntel, OptionPropIntel
from pyxrd.mvc.models.xydata import XYData

from pyxrd.data import settings
from pyxrd.generic.io import storables, Storable
from pyxrd.generic.custom_math import smooth, add_noise

from pyxrd.generic.models.base import DataModel
from pyxrd.generic.io.file_parsers import ASCIIParser
from pyxrd.generic.utils import not_none

@storables.register()
class StorableXYData(XYData, Storable):
    """
        A storable XYData model with additional I/O and CRUD abilities.
    """

    class Meta(XYData.Meta):
        store_id = "StorableXYData"
        properties = []

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

    def save_data(self, filename, header=""):
        if self.data_y.shape[1] > 1:
            names = ["2θ", header] + (not_none(self.y_names, []))
            header = u",".join(names)
        ASCIIParser.write(filename, header, self.data_x, self.data_y.transpose())

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
        with self.data_changed.hold():
            if clear: self.clear()
            for x, y in generator:
                self.append(x, y)


    pass # end of class

@storables.register()
class PyXRDLine(DataModel, StorableXYData):
    """
        A PyXRDLine is an attribute holder for a real 'Line' object, whatever the
        plotting library used may be. Attributes are line width and
        color. More attributes may be added in the future.        
    """

    # MODEL INTEL:
    class Meta(StorableXYData.Meta):
        properties = [
            PropIntel(name="label", data_type=unicode, storable=True),
            PropIntel(name="color", data_type=str, storable=True, has_widget=True, widget_type="color"),
            PropIntel(name="inherit_color", data_type=bool, storable=True, has_widget=True, widget_type="toggle"),
            PropIntel(name="lw", data_type=float, storable=True, has_widget=True, widget_type="spin"),
            PropIntel(name="inherit_lw", data_type=bool, storable=True, has_widget=True, widget_type="toggle"),
        ]
        store_id = "PyXRDLine"
        inherit_format = "display_exp_%s"

    # OBSERVABLE PROPERTIES:
    _label = ""
    def get_label(self): return self._label
    def set_label(self, value): self._label = value

    _color = "#000000"
    def get_color(self):
        if self.inherit_color:
            try:
                return getattr(self.parent.parent, self.__inherit_format__ % "color")
            except AttributeError: # occurs when e.g. a parent is None
                return self._color
        else:
            return self._color
    def set_color(self, value):
        if self._color != value:
            self._color = value
            self.visuals_changed.emit()

    _inherit_color = True
    def get_inherit_color(self):
        return self._inherit_color
    def set_inherit_color(self, value):
        if value != self._inherit_color:
            self._inherit_color = value
            self.visuals_changed.emit()

    _lw = 2.0
    def get_lw(self):
        if self.inherit_lw:
            try:
                return getattr(self.parent.parent, self.__inherit_format__ % "lw")
            except AttributeError: # occurs when e.g. a parent is None
                return self._lw
        else:
            return self._lw
    def set_lw(self, value):
        if self._lw != value:
            self._lw = value
            self.visuals_changed.emit()

    _inherit_lw = True
    def get_inherit_lw(self): return self._inherit_lw
    def set_inherit_lw(self, value):
        if value != self._inherit_lw:
            self._inherit_lw = value
            self.visuals_changed.emit()

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
        """
        my_kwargs = self.pop_kwargs(kwargs,
            *[names[0] for names in PyXRDLine.Meta.get_local_storable_properties()]
        )
        super(PyXRDLine, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.visuals_changed.hold():
            self.label = self.get_kwarg(kwargs, self.label, "label")
            self.color = self.get_kwarg(kwargs, self.color, "color")
            self.inherit_color = bool(self.get_kwarg(kwargs, self.inherit_color, "inherit_color"))
            self.lw = float(self.get_kwarg(kwargs, self.lw, "lw"))
            self.inherit_lw = bool(self.get_kwarg(kwargs, self.inherit_lw, "inherit_lw"))

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

    def set_data(self, x, y):
        """
            Sets data using the supplied x, y1, ..., yn arrays.
        """
        with self.data_changed.hold_and_emit():
            super(PyXRDLine, self).set_data(x, y)

    def set_value(self, i, j, value):
        with self.data_changed.hold_and_emit():
            super(PyXRDLine, self).set_value(i, j, value)

    def append(self, x, y):
        """
            Appends data using the supplied x, y1, ..., yn arrays.
        """
        with self.data_changed.hold_and_emit():
            super(PyXRDLine, self).append(x, y)

    def insert(self, pos, x, y):
        """
            Inserts data using the supplied x, y1, ..., yn arrays at the given
            position.
        """
        with self.data_changed.hold_and_emit():
            super(PyXRDLine, self).insert(pos, x, y)

    def remove_from_indeces(self, *indeces):
        with self.data_changed.hold_and_emit():
            super(PyXRDLine, self).remove_from_indeces(*indeces)

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
            if settings.DEBUG:
                from traceback import print_exc
                print_exc()
        else:
            if len(xdata) > 0 and len(ydata) > 0:
                return np.interp(x, xdata, ydata)
        return 0


    pass # end of class

@storables.register()
class CalculatedLine(PyXRDLine):

    # MODEL INTEL:
    class Meta(PyXRDLine.Meta):
        properties = [
            PropIntel(name="phase_colors", data_type=list),
        ]
        store_id = "CalculatedLine"
        inherit_format = "display_calc_%s"

    specimen = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:
    _color = settings.CALCULATED_COLOR
    _lw = settings.CALCULATED_LINEWIDTH

    _phase_colors = []
    def get_phase_colors(self): return self._phase_colors
    def set_phase_colors(self, value): self._phase_colors = value

    pass # end of class

@storables.register()
class ExperimentalLine(PyXRDLine):

    # MODEL INTEL:
    class Meta(PyXRDLine.Meta):
        properties = [
            PropIntel(name="bg_position", data_type=float, has_widget=True, widget_type="float_entry"),
            PropIntel(name="bg_scale", data_type=float, has_widget=True, widget_type="float_entry"),
            PropIntel(name="bg_pattern", data_type=object),
            OptionPropIntel(name="bg_type", data_type=int, has_widget=True, options=settings.PATTERN_BG_TYPES),
            PropIntel(name="smooth_degree", data_type=int, has_widget=True),
            OptionPropIntel(name="smooth_type", data_type=int, has_widget=True, options=settings.PATTERN_SMOOTH_TYPES),
            PropIntel(name="noise_fraction", data_type=float, has_widget=True, widget_type="spin"),
            PropIntel(name="shift_value", data_type=float, has_widget=True, widget_type="float_entry"),
            OptionPropIntel(name="shift_position", data_type=float, has_widget=True, options=settings.PATTERN_SHIFT_POSITIONS),
            PropIntel(name="cap_value", data_type=float, has_widget=True, storable=True, widget_type="float_entry"),
            PropIntel(name="area_startx", data_type=float, has_widget=True, widget_type="float_entry"),
            PropIntel(name="area_endx", data_type=float, has_widget=True, widget_type="float_entry"),
            PropIntel(name="area_pattern", data_type=object),
            PropIntel(name="area_result", data_type=float, has_widget=True, widget_type="label"),
            PropIntel(name="strip_startx", data_type=float, has_widget=True, widget_type="float_entry"),
            PropIntel(name="strip_endx", data_type=float, has_widget=True, widget_type="float_entry"),
            PropIntel(name="noise_level", data_type=float, has_widget=True, widget_type="float_entry"),
            PropIntel(name="stripped_pattern", data_type=object),
        ]
        store_id = "ExperimentalLine"

    specimen = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:
    _color = settings.EXPERIMENTAL_COLOR
    _lw = settings.EXPERIMENTAL_LINEWIDTH

    _cap_value = 0.0
    def get_cap_value(self): return self._cap_value
    def set_cap_value(self, value):
        try:
            self._cap_value = float(value)
            self.visuals_changed.emit()
        except ValueError:
            pass

    @property
    def max_intensity(self):
        max_value = super(ExperimentalLine, self).max_intensity
        if self.cap_value > 0:
            max_value = min(max_value, self.cap_value)
        return max_value

    _bg_position = 0
    def get_bg_position(self): return self._bg_position
    def set_bg_position(self, value):
        try:
            self._bg_position = float(value)
            self.visuals_changed.emit()
        except ValueError:
            pass

    _bg_scale = 1.0
    def get_bg_scale(self): return self._bg_scale
    def set_bg_scale(self, value):
        try:
            self._bg_scale = float(value)
            self.visuals_changed.emit()
        except ValueError:
            pass

    _bg_pattern = None
    def get_bg_pattern(self): return self._bg_pattern
    def set_bg_pattern(self, value):
        self._bg_pattern = value
        self.visuals_changed.emit()

    def get_bg_type_lbl(self):
        return self._bg_types[self._bg_type]
    def on_bgtype(self, prop_name, value):
        self.find_bg_position()

    _smooth_degree = 0
    smooth_pattern = None
    def get_smooth_degree(self): return self._smooth_degree
    def set_smooth_degree(self, value):
        self._smooth_degree = float(value)
        self.visuals_changed.emit()

    _noise_fraction = 0.0
    def get_noise_fraction(self): return self._noise_fraction
    def set_noise_fraction(self, value):
        try:
            self._noise_fraction = max(float(value), 0.0)
            self.visuals_changed.emit()
        except ValueError:
            pass

    _shift_value = 0.0
    def get_shift_value(self): return self._shift_value
    def set_shift_value(self, value):
        try:
            self._shift_value = float(value)
            self.visuals_changed.emit()
        except ValueError:
            pass

    _area_startx = 0.0
    def get_area_startx(self): return self._area_startx
    def set_area_startx(self, value):
        try:
            self._area_startx = float(value)
            if self._area_endx < self._area_startx:
                self.area_endx = self._area_startx + 1.0
            else: # update will be taken care of by endx's setter in the previous case
                self.update_area_pattern(new_pos=True)
        except ValueError:
            pass

    _area_endx = 0.0
    def get_area_endx(self): return self._area_endx
    def set_area_endx(self, value):
        try:
            self._area_endx = float(value)
            self.update_area_pattern(new_pos=True)
        except ValueError:
            pass

    _area_result = 0.0
    def get_area_result(self): return self._area_result
    def set_area_result(self, value):
        try:
            self._area_result = float(value)
        except ValueError:
            pass

    _area_pattern = None
    def get_area_pattern(self): return self._area_pattern
    def set_area_pattern(self, value):
        self._area_pattern = value
        self.visuals_changed.emit()

    _strip_startx = 0.0
    def get_strip_startx(self): return self._strip_startx
    def set_strip_startx(self, value):
        try:
            self._strip_startx = float(value)
            if self._strip_endx < self._strip_startx:
                self.strip_endx = self._strip_startx + 1.0
            else: # update will be taken care of by endx's setter in the previous case
                self.update_strip_pattern(new_pos=True)
        except ValueError:
            pass

    _strip_endx = 0.0
    def get_strip_endx(self): return self._strip_endx
    def set_strip_endx(self, value):
        try:
            self._strip_endx = float(value)
            self.update_strip_pattern(new_pos=True)
        except ValueError:
            pass

    _stripped_pattern = None
    def get_stripped_pattern(self): return self._stripped_pattern
    def set_stripped_pattern(self, value):
        self._stripped_pattern = value
        self.visuals_changed.emit()

    _noise_level = 0.0
    def get_noise_level(self): return self._noise_level
    def set_noise_level(self, value):
        self._noise_level = value
        self.update_strip_pattern()

    _shift_position = 0.42574
    def get_shift_position(self): return self._shift_position
    def set_shift_position(self, value):
        with self.visuals_changed.hold_and_emit():
            self._shift_position = value
            self.setup_shift_variables()

    _smooth_type = 0
    def get_smooth_type(self): return self._smooth_type
    def set_smooth_type(self, value):
        with self.visuals_changed.hold_and_emit():
            self._smooth_type = value

    _bg_type = 0
    def get_bg_type(self): return self._bg_type
    def set_bg_type(self, value):
        with self.visuals_changed.hold_and_emit():
            self._bg_type = value

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
                self.data_x = self.data_x - self.shift_value
                if self.specimen is not None:
                    with self.specimen.visuals_changed.hold():
                        for marker in self.specimen.markers:
                            marker.position = marker.position - self.shift_value
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
    def update_area_pattern(self, new_pos=True):
        with self.visuals_changed.hold_and_emit():
            if new_pos:
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
    def update_strip_pattern(self, new_pos=False):
        with self.visuals_changed.hold_and_emit():
            if not self.block_strip:
                self.block_strip = True

                if new_pos:
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

                # Get the x-values in between start and end point:
                condition = (self.data_x >= self.strip_startx) & (self.data_x <= self.strip_endx)
                section_x = np.extract(condition, self.data_x)

                # Calculate the new y-values, add noise according to noise_level
                noise = self.avg_endy * 2 * (np.random.rand(*section_x.shape) - 0.5) * self.noise_level
                section_y = (self.strip_slope * (section_x - self.strip_startx) + self.avg_starty) + noise
                self.stripped_pattern = (section_x, section_y)
                self.block_strip = False

    def clear_strip_variables(self):
        with self.visuals_changed.hold_and_emit():
            self._strip_startx = 0.0
            self._strip_pattern = None
            self.strip_start_x = 0.0


    pass # end of class
