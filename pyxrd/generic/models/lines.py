# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from scipy.interpolate import interp1d

from pyxrd.gtkmvc.support.propintel import PropIntel, OptionPropIntel

from pyxrd.data import settings
from pyxrd.generic.io import storables, Storable
from pyxrd.generic.custom_math import smooth, add_noise

from base import DataModel
import types
import json
from pyxrd.generic.io.file_parsers import ASCIIParser
from pyxrd.generic.utils import not_none

@storables.register()
class XYData(DataModel, Storable):
    """
        An XYData is data model holding a list of x-y numbers with additional
        I/O and CRUD abilities.  
        Its values can be indexed, e.g.:
         >>> xydata = XYData(data=([1, 2, 3], [[4, 5], [6, 7], [8, 9]]))
         >>> xydata[0]
         (1, [4, 5])
         
        and iterated:
         >>> xydata = XYData(data=([1, 2, 3], [[4, 5], [6, 7], [8, 9]]))
         >>> for row in xydata:
         ...  print row
         ...
         (1, [4, 5])
         (2, [6, 7])
         (3, [8, 9])
         
        You can also associate names with each column:
         >>> xydata = XYData(data=([1, 2, 3], [[4, 5], [6, 7], [8, 9]]))
         >>> xydata.y_names = ["First Column", "Second Column"]
         >>> xydata.y_names.get(0, "")
         'First Column'
         
         
    """
    # MODEL INTEL:
    class Meta(DataModel.Meta):
        properties = [
            PropIntel(name="data_x", data_type=object),
            PropIntel(name="data_y", data_type=object),
        ]
        store_id = "XYData"

    # OBSERVABLE PROPERTIES:
    _data_x = None
    def get_data_x(self): return self._data_x
    def set_data_x(self, value):
        self.set_data(value, self._data_y)
    _data_y = None
    def get_data_y(self): return self._data_y
    def set_data_y(self, value):
        self.set_data(self._data_x, value)

    # REGULAR PROPERTIES:
    _y_names = []
    @property
    def y_names(self):
        if len(self) < len(self._y_names): 
            return self._y_names[:len(self)]
        else:
            return self._y_names
    @y_names.setter
    def y_names(self, names):
        self._y_names = names    
    
    @property
    def size(self):
        return len(self)

    @property
    def num_columns(self):
        return 1 + self.data_y.shape[1]

    @property
    def max_y(self):
        if len(self.data_x) > 1:
            return np.max(self.data_y)
        else:
            return 0

    @property
    def min_y(self):
        if len(self.data_x) > 1:
            return np.min(self.data_y)
        else:
            return 0

    @property
    def abs_max_y(self):
        if len(self.data_x) > 1:
            return np.max(np.absolute(self.data_y))
        else:
            return 0

    @property
    def abs_min_y(self):
        if len(self.data_x) > 1:
            return np.min(np.absolute(self.data_y))
        else:
            return 0

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for an XYData are:
                data: the actual data containing x and y values, this can be a:
                 - JSON string: "[[x1, x2, ..., xn], [y11, y21, ..., yn1], ..., [y1m, y2m, ..., ynm]]"
                 - A dictionary from a (deprecated) XYObjectListStore, containing
                   a data property, which contains a JSON string as above.
                 - A 2D-numpy array, in which its first axes contains the 
                   data rows, and its second axes contains the columns, first 
                   column being the x-data, and following columns the y-data, e.g.:
                    np.array([[x1,y11,...,y1m],
                              [x2,y21,...,y2m],
                              ...,
                              [xn,yn1,...,ynm]])
                  - An iterable containing the x-data and y-data as if it would be
                    passed to set_data(*data), e.g.:
                     ([1, 2, 3], [[4, 5], [6, 7], [8, 9]])
                names: names for the y columns (optional)
        """
        self._data_x = np.array([], dtype=float)
        self._data_y = np.zeros(shape=(0, 0), dtype=float)
        
        super(XYData, self).__init__(*args, **kwargs)
        with self.visuals_changed.hold():
            self.y_names = self.get_kwarg(kwargs, self.y_names, "names")
            
            data = self.get_kwarg(kwargs, None, "xy_store", "data")
            if data is not None:
                if type(data) in types.StringTypes:
                    self._set_from_serial_data(data)
                elif type(data) is types.DictionaryType:
                    self._set_from_serial_data(data["properties"]["data"])
                elif isinstance(data, np.ndarray):
                    self.set_data(data[:,0], data[:,1:])
                elif hasattr(data, '__iter__'):
                    self.set_data(*data)
            else:
                self.clear()

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def json_properties(self):
        props = super(XYData, self).json_properties()
        props["data"] = self._serialize_data()
        return props

    def save_data(self, filename, header=""):
        if self.data_y.shape[0] > 1:
            names = ["2θ", header] + (not_none(self.y_names, []))
            header = u",".join(names)
        ASCIIParser.write(filename, header, self.data_x, self.data_y)

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

    def _serialize_data(self):
        """
            Internal method, should normally not be used!
            If you want to write data to a file, use the save_data method instead!
        """
        conc = np.insert(self.data_y, 0, self.data_x, axis=1)
        return "[" + ",".join(
                ["[" + ",".join(["%f" % val for val in row]) + "]" for row in conc]
            ) + "]"

    def _deserialize_data(self, data):
        """
            Internal method, should normally not be used!
            If you want to load data from a file, use the generic.io.file_parsers
            classes in combination with the load_data_from_generator instead!
            'data' argument should be a json string, containing a list of lists
            of x and y values, i.e.:
            [[x1, x2, ..., xn], [y11, y21, ..., yn1], ..., [y1m, y2m, ..., ynm]]
            If there are n data points and m+1 columns.
        """
        data = data.replace("nan", "0.0")
        data = json.JSONDecoder().decode(data)
        return data

    def _set_from_serial_data(self, data):
        """Internal method, do not use!"""
        data = self._deserialize_data(data)
        if data != []:
            data = np.array(data, dtype=float)
            try:
                x = data[:,0]
                y = data[:,1]
            except IndexError:
                if settings.DEBUG:
                    print "Failed to load xy-data from serial string!"
            else:
                self.set_data(x, y)

    # ------------------------------------------------------------
    #      X-Y Data Management Methods & Functions
    # ------------------------------------------------------------
    def _y_from_user(self, y_value):
        return np.array(y_value, ndmin=2, dtype=float)
    
    def set_data(self, x, y):
        """
            Sets data using the supplied x, y1, ..., yn arrays.
        """
        with self.data_changed.hold_and_emit():
            tempx = np.asanyarray(x)
            tempy = np.asanyarray(y)
            if tempy.ndim == 1:
                tempy = tempy.reshape((tempy.size, 1))
            if tempx.shape[0] != tempy.shape[0]:
                raise ValueError, "Shape mismatch: x (shape = %s) and y (shape = %s) data need to have compatible shapes!" % (tempx.shape, tempy.shape)
            self._data_x = tempx
            self._data_y = tempy
               
    def set_value(self, i, j, value):
        with self.data_changed.hold_and_emit():
            if i < len(self):
                if j == 0:
                    self.data_x[i] = value
                elif j >= 1:
                    self.data_y[i, j - 1] = np.array(value, dtype=float)
                else:
                    raise IndexError, "Column indices must be positive values (is '%d')!" % j
            else:
                raise IndexError, "Row index '%d' out of bound!" % i
               
    def append(self, x, y):
        """
            Appends data using the supplied x, y1, ..., yn arrays.
        """
        with self.data_changed.hold_and_emit():
            data_x = np.append(self.data_x, x)
            _y = self._y_from_user(y)
            if self.data_y.size == 0:
                data_y = _y
            else:
                data_y = np.append(self.data_y, _y, axis=0)
            self.set_data(data_x, data_y)
           
    def insert(self, pos, x, y):
        """
            Inserts data using the supplied x, y1, ..., yn arrays at the given
            position.
        """
        with self.data_changed.hold_and_emit():
            self.data_x = np.insert(self.data_x, pos, x)
            self.data_y = np.insert(self.data_y, pos, self._y_from_user(y), axis=0)
            
    def remove_from_indeces(self, *indeces):
        if indeces != []:
            indeces = np.sort(indeces)[::-1]
            with self.data_changed.hold_and_emit():
                for index in indeces:
                    self.set_data(
                        np.delete(self.data_x, index, axis=0),
                        np.delete(self.data_y, index, axis=0)
                    )

    def clear(self):
        """
            Clears all x and y values.
        """
        self.set_data(np.zeros((0,), dtype=float), np.zeros((0,0), dtype=float))

    # ------------------------------------------------------------
    #      Convenience Methods & Functions
    # ------------------------------------------------------------
    def get_xy_data(self, column=1):
        """
            Returns a two-tuple containing 1D-numpy arrays with the x-data and
            the y-data for a given column. If the column keyword is not passed, 
            the first column is returned.
        """
        if len(self) > 0:
            return self.data_x, self.data_y[:,column-1]
        else:
            return np.array([], dtype=float), np.array([], dtype=float)
    
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

    def get_y_at_x(self, x, column=0):
        """ 
            Get the (interpolated) value for the y-column 'column' for
            a given x value
        """
        if self._data_x.size:
            return np.interp(x, self._data_x, self._data_y[:,column])
        else:
            return 0

    def get_y_name(self, column):
        """
            Returns the name of the given column. If the y_names attribute is 
            not properly set (e.g. too small or empty), it will return an empty
            string. This method is 'safer' to use then directly accessing the
            y_names attribute (may result in an IndexError).
        """
        try:
            return self.y_names[column]
        except IndexError:
            return ""

    def interpolate(self, *x_vals, **kwargs):
        """
            Returns a list of (x, y) tuples for the passed x values. An optional
            column keyword argument can be passed to select a column, by default
            the first y-column is used. Returned y-values are interpolated. 
        """
        column = kwargs.get("column", 0)
        f = interp1d(self.data_x, self.data_y[:,column])
        return zip(x_vals, f(x_vals))

    # ------------------------------------------------------------
    #      Iterable & Indexable implementation
    # ------------------------------------------------------------
    def __len__(self):
        return len(self.data_x)
    
    def __getitem__(self, index):
        return self.data_x[index], self.data_y[index].tolist()
    
    def __iter__(self):
        for i in xrange(len(self)):
            yield self[i]
    
    pass # end of class


@storables.register()
class PyXRDLine(XYData):
    """
        A PyXRDLine is an attribute holder for a real 'Line' object, whatever the
        plotting library used may be. Attributes are line width and
        color. More attributes may be added in the future.        
    """

    # MODEL INTEL:
    class Meta(XYData.Meta):
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
        super(PyXRDLine, self).__init__(*args, **kwargs)
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

    pass # end of class

@storables.register()
class CalculatedLine(PyXRDLine):

    # MODEL INTEL:
    class Meta(PyXRDLine.Meta):
        parent_alias = 'specimen'
        properties = [
            PropIntel(name="phase_colors", data_type=list),
        ]       
        store_id = "CalculatedLine"
        inherit_format = "display_calc_%s"

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
        parent_alias = 'specimen'
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
            PropIntel(name="strip_startx", data_type=float, has_widget=True, widget_type="float_entry"),
            PropIntel(name="strip_endx", data_type=float, has_widget=True, widget_type="float_entry"),
            PropIntel(name="noise_level", data_type=float, has_widget=True, widget_type="float_entry"),
            PropIntel(name="stripped_pattern", data_type=object),
        ]
        store_id = "ExperimentalLine"

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
            self.find_shift_value()
    
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
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for a ExperimentalLine are:
                cap_value: the value (in raw counts) at which to cap
                 the experimental pattern  
        """
        super(ExperimentalLine, self).__init__(*args, **kwargs)
        self.cap_value = self.get_kwarg(kwargs, 0.0, "cap_value")

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
                self.data_y -= bg
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
                self.data_y = smooth(self.data_y[:,0], degree)
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
                noisified = add_noise(self.data_y[:,0], self.noise_fraction)
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
            position = self.parent.goniometer.get_2t_from_nm(self.shift_position)
            if position > 0.1:
                max_x = position + 0.5
                min_x = position - 0.5
                condition = (self.data_x >= min_x) & (self.data_x <= max_x)
                section_x, section_y = np.extract(condition, self.data_x), np.extract(condition, self.data_y[:,0])
                try:
                    actual_position = section_x[np.argmax(section_y)]
                except ValueError:
                    actual_position = position
                self.shift_value = actual_position - position

    def clear_shift_variables(self):
        with self.visuals_changed.hold_and_emit():
            self.shift_value = 0

    # ------------------------------------------------------------
    #       Peak stripping
    # ------------------------------------------------------------
    def strip_peak(self):
        with self.data_changed.hold_and_emit():
            if self.stripped_pattern is not None:
                stripx, stripy = self.stripped_pattern
                indeces = ((self.data_x >= self.strip_startx) & (self.data_x <= self.strip_endx)).nonzero()[0]
                np.put(self.data_y[:,0], indeces, stripy)
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
                    section = np.extract(condition, self.data_y[:,0])
                    self.avg_starty = np.average(section)
                    noise_starty = 2 * np.std(section) / self.avg_starty
    
                    # calculate average ending point y value
                    condition = (self.data_x >= self.strip_endx - 0.1) & (self.data_x <= self.strip_endx + 0.1)
                    section = np.extract(condition, self.data_y[:,0])
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
