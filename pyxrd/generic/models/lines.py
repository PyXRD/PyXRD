# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from pyxrd.gtkmvc.model import Signal

from pyxrd.generic.io import storables, Storable, PyXRDDecoder
from pyxrd.generic.custom_math import smooth, add_noise

from properties import PropIntel, MultiProperty
from treemodels import XYListStore

from base import ChildModel

@storables.register()
class PyXRDLine(ChildModel, Storable):
    """
        A PyXRDLine is an attribute holder for a real 'Line' object, whatever the
        plotting library used may be. Internally it used an XYListStore to store
        the x-y values (xy_store attribute). Other attributes are linewidth and
        color. More attributes may be added in the future.
        
        The object also has a 'needs_update' signal, which is called whenever
        the presentation of the object should be updated.
    """

    # MODEL INTEL:
    __model_intel__ = [
        PropIntel(name="label", data_type=unicode, storable=True),
        PropIntel(name="xy_store", data_type=object, storable=True),
        PropIntel(name="color", data_type=str, observable=False),
        PropIntel(name="lw", data_type=float, observable=False),
        PropIntel(name="needs_update", data_type=object),
    ]
    __store_id__ = "PyXRDLine"

    # PROPERTIES:
    _xy_store = None
    def get_xy_store_value(self): return self._xy_store
    needs_update = None

    _label = ""
    def get_label_value(self): return self._label
    def set_label_value(self, value): self._label = value

    _color = "#000000"
    @property
    def color(self): return self._color
    @color.setter
    def color(self, value):
        self._color = value
        self.needs_update.emit()

    _lw = 2.0
    @property
    def lw(self): return self._lw
    @lw.setter
    def lw(self, value):
        self._lw = value
        self.needs_update.emit()

    @property
    def size(self):
        return len(self.xy_store._model_data_x)

    @property
    def max_intensity(self):
        if len(self.xy_store._model_data_x) > 1:
            return np.max(self.xy_store._model_data_y)
        else:
            return 0

    @property
    def min_intensity(self):
        if len(self.xy_store._model_data_x) > 1:
            return np.min(self.xy_store._model_data_y)
        else:
            return 0

    @property
    def abs_max_intensity(self):
        if len(self.xy_store._model_data_x) > 1:
            return np.max(np.absolute(self.xy_store._model_data_y))
        else:
            return 0

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, xy_store=None, label=None, color=None, lw=None, *args, **kwargs):
        self.init_xy_store(xy_store=xy_store)
        self.xy_store.connect('row-deleted', self.on_treestore_changed)
        self.xy_store.connect('row-inserted', self.on_treestore_changed)
        self.xy_store.connect('row-changed', self.on_treestore_changed)
        super(PyXRDLine, self).__init__(*args, **kwargs)

        self.needs_update = Signal()

        self.color = color if color != None else self.color
        self.label = label if label != None else self.label
        self.lw = lw if lw != None else self.lw

    def init_xy_store(self, xy_store=None):
        self._xy_store = xy_store or XYListStore()

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    @classmethod
    def from_json(type, **kwargs):
        if "xy_store" in kwargs:
            kwargs["xy_store"] = PyXRDDecoder().__pyxrd_decode__(kwargs["xy_store"])
        elif "xy_data" in kwargs:
            kwargs["xy_store"] = PyXRDDecoder().__pyxrd_decode__(kwargs["xy_data"])
            kwargs["label"] = kwargs["data_label"]
            del kwargs["data_name"]
            del kwargs["data_label"]
            del kwargs["xy_data"]
        return type(**kwargs)

    def save_data(self, filename):
        self.xy_store.save_data("%s %s" % (self.parent.name, self.parent.sample_name), filename)

    def load_data(self, parser, filename, clear=True):
        """
            Loads data using passed filename and parser, which are passed on to
            the internal XYListStore's load_data_from_generator method.
            If clear=True the xy_store data is cleared first.
        """
        xrdfiles = parser.parse(filename)
        self.xy_store.load_data_from_generator(xrdfiles[0].data, clear=clear)

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def on_treestore_changed(self, treemodel, path, *args):
        self.needs_update.emit()

    def set_data(self, x, *y, **kwargs):
        """
            Sets data using the supplied x, y1, ..., yn arrays.
            You can also pass in an optional 'names' keyword, containing
            the column names for y-value argument.
        """
        self.xy_store.update_from_data(x, *y, **kwargs)

    def get_plotted_y_at_x(self, x):
        try:
            xdata, ydata = getattr(self, "__plot_line").get_data()
            if len(xdata) > 0 and len(ydata) > 0:
                return np.interp(x, xdata, ydata)
            else:
                return 0
        except AttributeError:
            from traceback import print_exc
            print_exc()
            return 0

    def clear(self):
        self.xy_store.clear()

    pass # end of class

@storables.register()
class CalculatedLine(PyXRDLine):

    # MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [ ]
    __store_id__ = "CalculatedLine"
    __gtype_name__ = "PyXRDCalculatedLine"

    # PROPERTIES:
    phases = None

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.phases = []
        super(CalculatedLine, self).__init__(*args, **kwargs)

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def set_data(self, x, y, phase_patterns=[], phases=[]):
        self.phases = phases
        super(CalculatedLine, self).set_data(x, y, *phase_patterns, names=[phase.name if phase != None else "NOT SET" for phase in phases])

    pass # end of class

@storables.register()
class ExperimentalLine(PyXRDLine):

    # MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [
        PropIntel(name="bg_position", data_type=float, has_widget=True, widget_type="float_entry"),
        PropIntel(name="bg_scale", data_type=float, has_widget=True, widget_type="float_entry"),
        PropIntel(name="bg_pattern", data_type=object),
        PropIntel(name="bg_type", data_type=int, has_widget=True, widget_type="combo"),
        PropIntel(name="smooth_degree", data_type=int, has_widget=True),
        PropIntel(name="smooth_type", data_type=int, has_widget=True, widget_type="combo"),
        PropIntel(name="noise_fraction", data_type=float, has_widget=True, widget_type="spin"),
        PropIntel(name="shift_value", data_type=float, has_widget=True, widget_type="float_entry"),
        PropIntel(name="shift_position", data_type=float, has_widget=True, widget_type="combo"),
        PropIntel(name="cap_value", data_type=float, has_widget=True, widget_type="float_entry"),
        PropIntel(name="strip_startx", data_type=float, has_widget=True, widget_type="float_entry"),
        PropIntel(name="strip_endx", data_type=float, has_widget=True, widget_type="float_entry"),
        PropIntel(name="noise_level", data_type=float, has_widget=True, widget_type="float_entry"),
        PropIntel(name="stripped_pattern", data_type=object),
    ]
    __store_id__ = "ExperimentalLine"
    __gtype_name__ = "PyXRDExperimentalLine"

    # PROPERTIES:
    _cap_value = 0.0
    def get_cap_value_value(self): return self._cap_value
    def set_cap_value_value(self, value):
        try:
            self._cap_value = float(value)
            self.needs_update.emit()
        except ValueError:
            pass

    @property
    def max_intensity(self):
        max_value = super(ExperimentalLine, self).max_intensity
        if self.cap_value > 0:
            max_value = min(max_value, self.cap_value)
        return max_value

    _bg_position = 0
    def get_bg_position_value(self): return self._bg_position
    def set_bg_position_value(self, value):
        try:
            self._bg_position = float(value)
            self.needs_update.emit()
        except ValueError:
            pass

    _bg_scale = 1.0
    def get_bg_scale_value(self): return self._bg_scale
    def set_bg_scale_value(self, value):
        try:
            self._bg_scale = float(value)
            self.needs_update.emit()
        except ValueError:
            pass

    _bg_pattern = None
    def get_bg_pattern_value(self): return self._bg_pattern
    def set_bg_pattern_value(self, value):
        self._bg_pattern = value
        self.needs_update.emit()

    def get_bg_type_lbl(self):
        return self._bg_types[self._bg_type]
    def on_bgtype(self, prop_name, value):
        self.find_bg_position()

    _smooth_degree = 0
    smooth_pattern = None
    def get_smooth_degree_value(self): return self._smooth_degree
    def set_smooth_degree_value(self, value):
        self._smooth_degree = float(value)
        self.needs_update.emit()

    def on_sdtype(self, prop_name, value):
        self.needs_update.emit()

    _noise_fraction = 0.0
    def get_noise_fraction_value(self): return self._noise_fraction
    def set_noise_fraction_value(self, value):
        try:
            self._noise_fraction = max(float(value), 0.0)
            self.needs_update.emit()
        except ValueError:
            pass

    _shift_value = 0.0
    def get_shift_value_value(self): return self._shift_value
    def set_shift_value_value(self, value):
        try:
            self._shift_value = float(value)
            self.needs_update.emit()
        except ValueError:
            pass

    def on_shift(self, prop_name, value):
        self.find_shift_value()

    _strip_startx = 0.0
    def get_strip_startx_value(self): return self._strip_startx
    def set_strip_startx_value(self, value):
        try:
            self._strip_startx = float(value)
            if self._strip_endx < self._strip_startx:
                self.strip_endx = self._strip_startx + 1.0
            else: # update will be taken care of by endx's setter in the previous case
                self.update_strip_pattern(new_pos=True)
        except ValueError:
            pass

    _strip_endx = 0.0
    def get_strip_endx_value(self): return self._strip_endx
    def set_strip_endx_value(self, value):
        try:
            self._strip_endx = float(value)
            self.update_strip_pattern(new_pos=True)
        except ValueError:
            pass

    _stripped_pattern = None
    def get_stripped_pattern_value(self): return self._stripped_pattern
    def set_stripped_pattern_value(self, value):
        self._stripped_pattern = value
        self.needs_update.emit()

    _noise_level = 0.0
    def get_noise_level_value(self): return self._noise_level
    def set_noise_level_value(self, value):
        self._noise_level = value
        self.update_strip_pattern()

    shift_position = MultiProperty(0.42574, float, on_shift, {
        0.42574: "Quartz    0.42574   SiO2",
        0.3134:  "Silicon   0.3134    Si",
        0.2476:  "Zincite   0.2476    ZnO",
        0.2085:  "Corundum  0.2085    Al2O3"
    })
    smooth_type = MultiProperty(0, int, on_sdtype, { 0: "Moving Triangle" })
    bg_type = MultiProperty(0, int, on_bgtype, { 0: "Linear", 1: "Pattern" })

    # ------------------------------------------------------------
    #      Background Removal
    # ------------------------------------------------------------
    def remove_background(self):
        x_data, y_data = self.xy_store.get_raw_model_data()
        bg = None
        if self.bg_type == 0:
            bg = self.bg_position
        elif self.bg_type == 1 and self.bg_pattern != None and not (self.bg_position == 0 and self.bg_scale == 0):
            bg = self.bg_pattern * self.bg_scale + self.bg_position
        if bg != None:
            y_data -= bg
            self.set_data(x_data, y_data)
        self.clear_bg_variables()

    def find_bg_position(self):
        try:
            self.bg_position = np.min(self.xy_store.get_raw_model_data()[1])
        except ValueError:
            return 0.0

    def clear_bg_variables(self):
        self.bg_pattern = None
        self.bg_scale = 0.0
        self.bg_position = 0.0
        self.needs_update.emit()

    # ------------------------------------------------------------
    #       Data Smoothing
    # ------------------------------------------------------------
    def smooth_data(self):
        x_data, y_data = self.xy_store.get_raw_model_data()
        if self.smooth_degree > 0:
            degree = int(self.smooth_degree)
            smoothed = smooth(y_data, degree)
            self.set_data(x_data, smoothed)
        self.smooth_degree = 0.0
        self.needs_update.emit()

    def setup_smooth_variables(self):
        self.smooth_degree = 5.0

    def clear_smooth_variables(self):
        self.smooth_degree = 0.0

    # ------------------------------------------------------------
    #       Noise adding
    # ------------------------------------------------------------
    def add_noise(self):
        x_data, y_data = self.xy_store.get_raw_model_data()
        if self.noise_fraction > 0:
            noisified = add_noise(y_data, self.noise_fraction)
            self.set_data(x_data, noisified)
        self.noise_fraction = 0.0
        self.needs_update.emit()

    def clear_noise_variables(self):
        self.noise_fraction = 0.0
        self.needs_update.emit()

    # ------------------------------------------------------------
    #       Data Shifting
    # ------------------------------------------------------------
    def shift_data(self):
        x_data, y_data = self.xy_store.get_raw_model_data()
        if self.shift_value != 0.0:
            self.set_data(x_data - self.shift_value, y_data)
            if self.specimen:
                for marker in self.specimen.markers._model_data:
                    marker.position = marker.position - self.shift_value
        self.shift_value = 0.0
        self.needs_update.emit()

    def find_shift_value(self):
        position = self.parent.goniometer.get_2t_from_nm(self.shift_position)
        if position > 0.1:
            x_data, y_data = self.xy_store.get_raw_model_data()
            max_x = position + 0.5
            min_x = position - 0.5
            condition = (x_data >= min_x) & (x_data <= max_x)
            section_x, section_y = np.extract(condition, x_data), np.extract(condition, y_data)
            try:
                actual_position = section_x[np.argmax(section_y)]
            except ValueError:
                actual_position = position
            self.shift_value = actual_position - position

    def clear_shift_variables(self):
        self.shift_value = 0

    # ------------------------------------------------------------
    #       Peak stripping
    # ------------------------------------------------------------
    def strip_peak(self):
        x_data, y_data = self.xy_store.get_raw_model_data()
        if self.stripped_pattern != None:
            stripx, stripy = self.stripped_pattern
            indeces = ((x_data >= self.strip_startx) & (x_data <= self.strip_endx)).nonzero()[0]
            np.put(y_data, indeces, stripy)
            self.set_data(x_data, y_data)
        self._strip_startx = 0.0
        self._stripped_pattern = None
        self.strip_endx = 0.0

    strip_slope = 0.0
    avg_starty = 0.0
    avg_endy = 0.0
    block_strip = False
    def update_strip_pattern(self, new_pos=False):
        if not self.block_strip:
            self.block_strip = True
            x_data, y_data = self.xy_store.get_raw_model_data()

            if new_pos:
                # calculate average starting point y value
                condition = (x_data >= self.strip_startx - 0.1) & (x_data <= self.strip_startx + 0.1)
                section = np.extract(condition, y_data)
                self.avg_starty = np.average(section)
                noise_starty = 2 * np.std(section) / self.avg_starty

                # calculate average ending point y value
                condition = (x_data >= self.strip_endx - 0.1) & (x_data <= self.strip_endx + 0.1)
                section = np.extract(condition, y_data)
                self.avg_endy = np.average(section)
                noise_endy = 2 * np.std(section) / self.avg_starty

                # Calculate new slope and noise level
                self.strip_slope = (self.avg_starty - self.avg_endy) / (self.strip_startx - self.strip_endx)
                self.noise_level = (noise_starty + noise_endy) * 0.5

            # Get the x-values in between start and end point:
            condition = (x_data >= self.strip_startx) & (x_data <= self.strip_endx)
            section_x = np.extract(condition, x_data)

            # Calculate the new y-values, add noise according to noise_level
            noise = self.avg_endy * 2 * (np.random.rand(*section_x.shape) - 0.5) * self.noise_level
            section_y = (self.strip_slope * (section_x - self.strip_startx) + self.avg_starty) + noise
            self.stripped_pattern = (section_x, section_y)
            self.block_strip = False

    def clear_strip_variables(self):
        self._strip_startx = 0.0
        self._strip_pattern = None
        self.strip_start_x = 0.0
        self.needs_update.emit()

    pass # end of class
