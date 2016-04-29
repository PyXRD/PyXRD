# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from mvc import Signal, PropIntel, OptionPropIntel

import numpy as np
from scipy.interpolate import interp1d

from pyxrd.data import settings
from pyxrd.generic.io import storables, Storable
from pyxrd.generic.models import ChildModel, DataModel
from pyxrd.generic.models.mixins import CSVMixin
from pyxrd.generic.peak_detection import score_minerals
from pyxrd.generic.io.utils import unicode_open


class MineralScorer(DataModel):
    # MODEL INTEL:
    class Meta(DataModel.Meta):
        properties = [
            PropIntel(name="matches", data_type=list, has_widget=True),
            PropIntel(name="minerals", data_type=list, has_widget=True),
            PropIntel(name="matches_changed", data_type=object, has_widget=False, storable=False)
        ]

    specimen = property(DataModel.parent.fget, DataModel.parent.fset)

    matches_changed = None

    _matches = None
    def get_matches(self):
        return self._matches

    _minerals = None
    def get_minerals(self):
        # Load them when accessed for the first time:
        if self._minerals == None:
            self._minerals = list()
            with unicode_open(settings.DATA_REG.get_file_path("MINERALS")) as f:
                mineral = ""
                abbreviation = ""
                position_flag = True
                peaks = []
                for line in f:
                    line = line.replace('\n', '')
                    try:
                        number = float(line)
                        if position_flag:
                            position = number
                        else:
                            intensity = number
                            peaks.append((position, intensity))
                        position_flag = not position_flag
                    except ValueError:
                        if mineral != "":
                            self._minerals.append((mineral, abbreviation, peaks))
                        position_flag = True
                        if len(line) > 25:
                            mineral = line[:24].strip()
                        if len(line) > 49:
                            abbreviation = line[49:].strip()
                        peaks = []
        sorted(self._minerals, key=lambda mineral:mineral[0])
        return self._minerals

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, marker_peaks=[], *args, **kwargs):
        super(MineralScorer, self).__init__(*args, **kwargs)
        self._matches = []
        self.matches_changed = Signal()

        self.marker_peaks = marker_peaks # position, intensity

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def auto_match(self):
        self._matches = score_minerals(self.marker_peaks, self.minerals)
        self.matches_changed.emit()

    def del_match(self, index):
        if self.matches:
            del self.matches[index]
            self.matches_changed.emit()

    def add_match(self, name, abbreviation, peaks):
        matches = score_minerals(self.marker_peaks, [(name, abbreviation, peaks)])
        if len(matches):
            name, abbreviation, peaks, matches, score = matches[0]
        else:
            matches, score = [], 0.
        self.matches.append([name, abbreviation, peaks, matches, score])
        sorted(self._matches, key=lambda match: match[-1], reverse=True)
        self.matches_changed.emit()

    pass # end of class

class ThresholdSelector(ChildModel):

    # MODEL INTEL:

    class Meta(DataModel.Meta):
        properties = [ # TODO add labels
            OptionPropIntel(name="pattern", data_type=str, storable=True, has_widget=True, options={ "exp": "Experimental Pattern", "calc": "Calculated Pattern" }),
            PropIntel(name="max_threshold", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
            PropIntel(name="steps", data_type=int, storable=True, has_widget=True),
            PropIntel(name="sel_threshold", data_type=float, storable=True, has_widget=True, widget_type="float_entry"),
            PropIntel(name="sel_num_peaks", data_type=int, storable=True, has_widget=True, widget_type="label"),
            PropIntel(name="threshold_plot_data", data_type=object, storable=True),
        ]

    specimen = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:

    _pattern = "exp"
    def get_pattern(self): return self._pattern
    def set_pattern(self, value):
        self._pattern = value
        self.update_threshold_plot_data()

    _max_threshold = 0.32
    def get_max_threshold(self): return self._max_threshold
    def set_max_threshold(self, value):
        value = min(max(0, float(value)), 1) # set some bounds
        if value != self._max_threshold:
            self._max_threshold = value
            self.update_threshold_plot_data()

    _steps = 20
    def get_steps(self): return self._steps
    def set_steps(self, value):
        value = min(max(3, value), 50) # set some bounds
        if value != self._steps:
            self._steps = value
            self.update_threshold_plot_data()

    _sel_threshold = 0.1
    sel_num_peaks = 0
    def get_sel_threshold(self): return self._sel_threshold
    def set_sel_threshold(self, value):
        if value != self._sel_threshold:
            self._sel_threshold = value
            if self._sel_threshold >= self.threshold_plot_data[0][-1]:
                self.sel_num_peaks = self.threshold_plot_data[1][-1]
            elif self._sel_threshold <= self.threshold_plot_data[0][0]:
                self.sel_num_peaks = self.threshold_plot_data[1][0]
            else:
                self.sel_num_peaks = int(interp1d(*self.threshold_plot_data)(self._sel_threshold))

    threshold_plot_data = None

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(ThresholdSelector, self).__init__(*args, **kwargs)

        self.max_threshold = self.get_kwarg(kwargs, self.max_threshold, "max_threshold")
        self.steps = self.get_kwarg(kwargs, self.steps, "steps")
        self.sel_threshold = self.get_kwarg(kwargs, self.sel_threshold, "sel_threshold")

        if self.parent.experimental_pattern.size > 0:
            self.pattern = "exp"
        else:
            self.pattern = "calc"

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_xy(self):
        if self.pattern == "exp":
            data_x, data_y = self.parent.experimental_pattern.get_xy_data()
        elif self.pattern == "calc":
            data_x, data_y = self.parent.calculated_pattern.get_xy_data()
        if data_y.size > 0:
            data_y = data_y / np.max(data_y)
        return data_x, data_y

    _updating_plot_data = False
    def update_threshold_plot_data(self):
        if self.parent is not None and not self._updating_plot_data:
            self._updating_plot_data = True
            if self.pattern == "exp":
                p, t, m = self.parent.experimental_pattern.get_best_threshold(
                            self.max_threshold, self.steps)
            elif self.pattern == "calc":
                p, t, m = self.parent.calculated_pattern.get_best_threshold(
                            self.max_threshold, self.steps)
            self.threshold_plot_data = p
            self.sel_threshold = t
            self.max_threshold = m
            self._updating_plot_data = False
    pass # end of class


def get_inherit_attribute_pair(name, inherit_name, levels=1, parent_prefix="display_marker", signal=None):
    def get_inherit_attribute_value(self):
        return getattr(self, "_%s" % inherit_name)
    def set_inherit_attribute_value(self, value):
        setattr(self, "_%s" % inherit_name, bool(value))
        if getattr(self, signal, None) is not None: getattr(self, signal, None).emit()

    def get_attribute_value(self):
        if getattr(self, inherit_name, False) and self.parent is not None and self.parent.parent is not None:
            parent = self.parent
            for level in range(levels - 1):
                parent = parent.parent
            return getattr(parent, "%s_%s" % (parent_prefix, name))
        else:
            return getattr(self, "_%s" % name)
    def set_attribute_value(self, value):
        setattr(self, "_%s" % name, value)
        if getattr(self, signal, None) is not None: getattr(self, signal, None).emit()

    return get_inherit_attribute_value, set_inherit_attribute_value, get_attribute_value, set_attribute_value

@storables.register()
class Marker(DataModel, Storable, CSVMixin):

    # MODEL INTEL:
    class Meta(DataModel.Meta):
        properties = [ # TODO add labels
            PropIntel(name="label", data_type=unicode, storable=True, has_widget=True, is_column=True),
            PropIntel(name="visible", data_type=bool, storable=True, has_widget=True, is_column=True),
            PropIntel(name="position", data_type=float, storable=True, has_widget=True, widget_type="spin"),
            PropIntel(name="x_offset", data_type=float, storable=True, has_widget=True, widget_type="spin"),
            PropIntel(name="y_offset", data_type=float, storable=True, has_widget=True, widget_type="spin"),
            OptionPropIntel(name="align", data_type=str, storable=True, has_widget=True, inh_name="inherit_align", options=settings.MARKER_ALIGNS),
            PropIntel(name="inherit_align", data_type=bool, storable=True, has_widget=True),
            PropIntel(name="color", data_type=str, storable=True, has_widget=True, inh_name="inherit_color", widget_type="color"),
            PropIntel(name="inherit_color", data_type=bool, storable=True, has_widget=True),
            OptionPropIntel(name="base", data_type=int, storable=True, has_widget=True, inh_name="inherit_base", options=settings.MARKER_BASES),
            PropIntel(name="inherit_base", data_type=bool, storable=True, has_widget=True),
            OptionPropIntel(name="top", data_type=int, storable=True, has_widget=True, inh_name="inherit_top", options=settings.MARKER_TOPS),
            PropIntel(name="inherit_top", data_type=bool, storable=True, has_widget=True),
            PropIntel(name="top_offset", data_type=float, storable=True, has_widget=True, inh_name="inherit_top_offset", widget_type="spin"),
            PropIntel(name="inherit_top_offset", data_type=bool, storable=True, has_widget=True),
            PropIntel(name="angle", data_type=float, storable=True, has_widget=True, inh_name="inherit_angle", widget_type="spin"),
            PropIntel(name="inherit_angle", data_type=bool, storable=True, has_widget=True),
            OptionPropIntel(name="style", data_type=str, storable=True, has_widget=True, inh_name="inherit_style", options=settings.MARKER_STYLES),
            PropIntel(name="inherit_style", data_type=bool, storable=True, has_widget=True),
        ]
        csv_storables = [ (prop.name, prop.name) for prop in properties ]
        store_id = "Marker"

    specimen = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:
    _label = "New Marker"
    def get_label(self): return self._label
    def set_label(self, value):
        self._label = value
        self.visuals_changed.emit()

    # Color:
    _color = settings.MARKER_COLOR
    _inherit_color = settings.MARKER_INHERIT_COLOR
    (get_inherit_color,
    set_inherit_color,
    get_color,
    set_color) = get_inherit_attribute_pair(
        "color", "inherit_color",
        levels=2, parent_prefix="display_marker", signal="visuals_changed"
    )

    # Angle:
    _angle = settings.MARKER_ANGLE
    _inherit_angle = settings.MARKER_INHERIT_ANGLE
    (get_inherit_angle,
    set_inherit_angle,
    get_angle,
    set_angle) = get_inherit_attribute_pair(
        "angle", "inherit_angle",
        levels=2, parent_prefix="display_marker", signal="visuals_changed"
    )

    # Angle:
    _top_offset = settings.MARKER_TOP_OFFSET
    _inherit_top_offset = settings.MARKER_INHERIT_TOP_OFFSET
    (get_inherit_top_offset,
    set_inherit_top_offset,
    get_top_offset,
    set_top_offset) = get_inherit_attribute_pair(
        "top_offset", "inherit_top_offset",
        levels=2, parent_prefix="display_marker", signal="visuals_changed"
    )

    # Visible, position, X and Y offset:
    _visible = settings.MARKER_VISIBLE
    def get_visible(self): return self._visible
    def set_visible(self, value):
        self._visible = bool(value)
        self.visuals_changed.emit()

    _position = settings.MARKER_POSITION
    def get_position(self): return self._position
    def set_position(self, value):
        self._position = float(value)
        self.visuals_changed.emit()

    _x_offset = settings.MARKER_X_OFFSET
    def get_x_offset(self): return self._x_offset
    def set_x_offset(self, value):
        self._x_offset = float(value)
        self.visuals_changed.emit()

    _y_offset = settings.MARKER_Y_OFFSET
    def get_y_offset(self): return self._y_offset
    def set_y_offset(self, value):
        self._y_offset = float(value)
        self.visuals_changed.emit()

    def cbb_callback(self, prop_name, value):
        self.visuals_changed.emit()

    # Alignment:
    _inherit_align = settings.MARKER_INHERIT_ALIGN
    _align = settings.MARKER_ALIGN
    (get_inherit_align,
    set_inherit_align,
    get_align,
    set_align) = get_inherit_attribute_pair(
        "align", "inherit_align",
        levels=2, parent_prefix="display_marker", signal="visuals_changed"
    )

    # Base connection point:
    _inherit_base = settings.MARKER_INHERIT_BASE
    _base = settings.MARKER_BASE
    (get_inherit_base,
    set_inherit_base,
    get_base,
    set_base) = get_inherit_attribute_pair(
        "base", "inherit_base",
        levels=2, parent_prefix="display_marker", signal="visuals_changed"
    )

    # Top connection point:
    _inherit_top = settings.MARKER_INHERIT_TOP
    _top = settings.MARKER_TOP
    (get_inherit_top,
    set_inherit_top,
    get_top,
    set_top) = get_inherit_attribute_pair(
        "top", "inherit_top",
        levels=2, parent_prefix="display_marker", signal="visuals_changed"
    )

    # Line style:
    _inherit_style = settings.MARKER_INHERIT_STYLE
    _style = settings.MARKER_STYLE
    (get_inherit_style,
    set_inherit_style,
    get_style,
    set_style) = get_inherit_attribute_pair(
        "style", "inherit_style",
        levels=2, parent_prefix="display_marker", signal="visuals_changed"
    )

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):

        my_kwargs = self.pop_kwargs(kwargs,
            "data_label", "data_visible", "data_position", "data_x_offset", "data_y_offset"
            "data_color", "data_base", "data_angle", "data_align",
            *[names[0] for names in type(self).Meta.get_local_storable_properties()]
        )
        super(Marker, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        self.label = self.get_kwarg(kwargs, "", "label", "data_label")
        self.visible = self.get_kwarg(kwargs, True, "visible", "data_visible")
        self.position = float(self.get_kwarg(kwargs, 0.0, "position", "data_position"))
        self.x_offset = float(self.get_kwarg(kwargs, 0.0, "x_offset", "data_x_offset"))
        self.y_offset = float(self.get_kwarg(kwargs, 0.05, "y_offset", "data_y_offset"))
        self.top_offset = float(self.get_kwarg(kwargs, 0.0, "top_offset"))
        self.color = self.get_kwarg(kwargs, settings.MARKER_COLOR, "color", "data_color")
        self.base = int(self.get_kwarg(kwargs, settings.MARKER_BASE, "base", "data_base"))
        self.angle = float(self.get_kwarg(kwargs, 0.0, "angle", "data_angle"))
        self.align = self.get_kwarg(kwargs, settings.MARKER_ALIGN, "align")
        self.style = self.get_kwarg(kwargs, settings.MARKER_STYLE, "style", "data_align")

        # if top is not set and style is not "none",
        # assume top to be "Top of plot", otherwise (style is not "none")
        # assume top to be relative to the base point (using top_offset)
        self.top = int(self.get_kwarg(kwargs, 0 if self.style == "none" else 1, "top"))

        self.inherit_align = self.get_kwarg(kwargs, True, "inherit_align")
        self.inherit_color = self.get_kwarg(kwargs, True, "inherit_color")
        self.inherit_base = self.get_kwarg(kwargs, True, "inherit_base")
        self.inherit_top = self.get_kwarg(kwargs, True, "inherit_top")
        self.inherit_top_offset = self.get_kwarg(kwargs, True, "inherit_top_offset")
        self.inherit_angle = self.get_kwarg(kwargs, True, "inherit_angle")
        self.inherit_style = self.get_kwarg(kwargs, True, "inherit_style")

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_nm_position(self):
        if self.parent is not None:
            return self.parent.goniometer.get_nm_from_2t(self.position)
        else:
            return 0.0

    def set_nm_position(self, position):
        if self.parent is not None:
            self.position = self.parent.goniometer.get_2t_from_nm(position)
        else:
            self.position = 0.0

    pass # end of class
