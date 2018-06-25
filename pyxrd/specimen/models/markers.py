# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from scipy.interpolate import interp1d

from mvc.models.properties import (
    LabeledProperty, StringProperty, StringChoiceProperty, ColorProperty,
    FloatProperty, IntegerProperty, IntegerChoiceProperty, BoolProperty,
    ListProperty, SignalProperty,
    SignalMixin, ReadOnlyMixin, SetActionMixin
)

from pyxrd.data import settings
from pyxrd.calculations.peak_detection import score_minerals
from pyxrd.generic.io import storables, Storable
from pyxrd.generic.models import ChildModel, DataModel
from pyxrd.generic.models.properties import InheritableMixin
from pyxrd.generic.models.mixins import CSVMixin
from pyxrd.generic.io.utils import unicode_open

class MineralScorer(DataModel):

    specimen = property(DataModel.parent.fget, DataModel.parent.fset)

    matches_changed = SignalProperty()

    matches = ListProperty(
        default=None, text="Matches", visible=True, persistent=False,
        mix_with=(ReadOnlyMixin,)
    )

    @ListProperty(
        default=None, text="Minerals", visible=True, persistent=False,
        mix_with=(ReadOnlyMixin,)
    )
    def minerals(self):
        # Load them when accessed for the first time:
        _minerals = type(self).minerals._get(self)
        if _minerals == None:
            _minerals = list()
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
                            _minerals.append((mineral, abbreviation, peaks))
                        position_flag = True
                        if len(line) > 25:
                            mineral = line[:24].strip()
                        if len(line) > 49:
                            abbreviation = line[49:].strip()
                        peaks = []
            sorted(_minerals, key=lambda mineral:mineral[0])
        type(self).minerals._set(self, _minerals)
        return _minerals

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, marker_peaks=[], *args, **kwargs):
        super(MineralScorer, self).__init__(*args, **kwargs)
        self._matches = []

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

    specimen = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:

    pattern = StringChoiceProperty(
        default="exp", text="Pattern",
        visible=True, persistent=False,
        choices={ "exp": "Experimental Pattern", "calc": "Calculated Pattern" },
        set_action_name="update_threshold_plot_data",
        mix_with=(SetActionMixin,)
    )

    max_threshold = FloatProperty(
        default=0.32, text="Maximum threshold",
        visible=True, persistent=False,
        minimum=0.0, maximum=1.0, widget_type="float_entry",
        set_action_name="update_threshold_plot_data",
        mix_with=(SetActionMixin,)
    )

    steps = IntegerProperty(
        default=20, text="Steps",
        visible=True, persistent=False,
        minimum=3, maximum=50,
        set_action_name="update_threshold_plot_data",
        mix_with=(SetActionMixin,)
    )

    sel_num_peaks = IntegerProperty(
        default=0, text="Selected number of peaks",
        visible=True, persistent=False,
        widget_type="label"
    )

    def set_sel_threshold(self, value):
        _sel_threshold = type(self).sel_threshold._get(self)
        if value != _sel_threshold and len(self.threshold_plot_data[0]) > 0:
            _sel_threshold = value
            if _sel_threshold >= self.threshold_plot_data[0][-1]:
                self.sel_num_peaks = self.threshold_plot_data[1][-1]
            elif _sel_threshold <= self.threshold_plot_data[0][0]:
                self.sel_num_peaks = self.threshold_plot_data[1][0]
            else:
                self.sel_num_peaks = int(interp1d(*self.threshold_plot_data)(_sel_threshold))
            type(self).sel_threshold._set(self, _sel_threshold)
    sel_threshold = FloatProperty(
        default=0.1, text="Selected threshold",
        visible=True, persistent=False,
        widget_type="float_entry",
        fset = set_sel_threshold
    )

    threshold_plot_data = LabeledProperty(
        default=None, text="Threshold plot data",
        visible=False, persistent=False
    )

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
    def update_threshold_plot_data(self, status_dict=None):
        if self.parent is not None and not self._updating_plot_data:
            self._updating_plot_data = True
            if self.pattern == "exp":
                p, t, m = self.parent.experimental_pattern.get_best_threshold(
                            self.max_threshold, self.steps, status_dict)
            elif self.pattern == "calc":
                p, t, m = self.parent.calculated_pattern.get_best_threshold(
                            self.max_threshold, self.steps, status_dict)
            self.threshold_plot_data = p
            self.sel_threshold = t
            self.max_threshold = m
            self._updating_plot_data = False
    pass # end of class

@storables.register()
class Marker(DataModel, Storable, CSVMixin):

    # MODEL INTEL:
    class Meta(DataModel.Meta):
        store_id = "Marker"

    specimen = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:

    #: This marker's label
    label = StringProperty(
        default="New Marker", text="Label",
        persistent=True, visible=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: Flag indicating whether the color of this marker is inherited
    inherit_color = BoolProperty(
        default=settings.MARKER_INHERIT_COLOR, text="Inherit color",
        persistent=True, visible=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )
    #: This maker's color:
    color = ColorProperty(
        default=settings.MARKER_COLOR, text="Color",
        persistent=True, visible=True, tabular=True, inheritable=True,
        signal_name="visuals_changed", inherit_flag="inherit_color",
        inherit_from="specimen.project.display_marker_color",
        mix_with=(InheritableMixin, SignalMixin,)
    )

    #: Flag indicating whether the angle of this marker is inherited
    inherit_angle = BoolProperty(
        default=settings.MARKER_INHERIT_ANGLE, text="Inherit angle",
        persistent=True, visible=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )
    #: This maker's angle:
    angle = FloatProperty(
        default=settings.MARKER_ANGLE, text="Angle", widget_type="spin",
        persistent=True, visible=True, tabular=True, inheritable=True,
        signal_name="visuals_changed", inherit_flag="inherit_angle",
        inherit_from="specimen.project.display_marker_angle",
        mix_with=(InheritableMixin, SignalMixin,)
    )

    #: Flag indicating whether the top offset of this marker is inherited
    inherit_top_offset = BoolProperty(
        default=settings.MARKER_INHERIT_TOP_OFFSET, text="Inherit top offset",
        persistent=True, visible=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )
    #: This maker's top offset:
    top_offset = FloatProperty(
        default=settings.MARKER_TOP_OFFSET, text="Top offset", widget_type="spin",
        persistent=True, visible=True, tabular=True, inheritable=True,
        signal_name="visuals_changed", inherit_flag="inherit_top_offset",
        inherit_from="specimen.project.display_marker_top_offset",
        mix_with=(InheritableMixin, SignalMixin,)
    )

    #: Whether this marker is visible
    visible = BoolProperty(
        default=settings.MARKER_VISIBLE, text="Visible",
        persistent=True, visible=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: The marker's position
    position = FloatProperty(
        default=settings.MARKER_POSITION, text="Position", widget_type="spin",
        persistent=True, visible=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: The marker's x offset
    x_offset = FloatProperty(
        default=settings.MARKER_X_OFFSET, text="X offset", widget_type="spin",
        persistent=True, visible=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: The marker's y offset
    y_offset = FloatProperty(
        default=settings.MARKER_Y_OFFSET, text="Y offset", widget_type="spin",
        persistent=True, visible=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: Flag indicating whether the alignment of this marker is inherited
    inherit_align = BoolProperty(
        default=settings.MARKER_INHERIT_ALIGN, text="Inherit align",
        persistent=True, visible=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )
    #: This marker's alignment
    align = StringChoiceProperty(
        default=settings.MARKER_ALIGN, text="Align",
        choices=settings.MARKER_ALIGNS,
        persistent=True, visible=True, tabular=True, inheritable=True,
        signal_name="visuals_changed", inherit_flag="inherit_align",
        inherit_from="specimen.project.display_marker_align",
        mix_with=(InheritableMixin, SignalMixin,)
    )

    #: Flag indicating whether the base of this marker is inherited
    inherit_base = BoolProperty(
        default=settings.MARKER_INHERIT_BASE, text="Inherit base",
        persistent=True, visible=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )
    #: This marker's base
    base = IntegerChoiceProperty(
        default=settings.MARKER_BASE, text="Base",
        choices=settings.MARKER_BASES,
        persistent=True, visible=True, tabular=True, inheritable=True,
        signal_name="visuals_changed", inherit_flag="inherit_base",
        inherit_from="specimen.project.display_marker_base",
        mix_with=(InheritableMixin, SignalMixin,)
    )

    #: Flag indicating whether the top of this marker is inherited
    inherit_top = BoolProperty(
        default=settings.MARKER_INHERIT_TOP, text="Inherit top",
        persistent=True, visible=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )
    #: This marker's top
    top = IntegerChoiceProperty(
        default=settings.MARKER_TOP, text="Top",
        choices=settings.MARKER_TOPS,
        persistent=True, visible=True, tabular=True, inheritable=True,
        signal_name="visuals_changed", inherit_flag="inherit_top",
        inherit_from="specimen.project.display_marker_top",
        mix_with=(InheritableMixin, SignalMixin,)
    )

    #: Flag indicating whether the line style of this marker is inherited
    inherit_style = BoolProperty(
        default=settings.MARKER_INHERIT_STYLE, text="Inherit line style",
        persistent=True, visible=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )
    #: This marker's line style
    style = StringChoiceProperty(
        default=settings.MARKER_STYLE, text="Line style",
        choices=settings.MARKER_STYLES,
        persistent=True, visible=True, tabular=True, inheritable=True,
        signal_name="visuals_changed", inherit_flag="inherit_style",
        inherit_from="specimen.project.display_marker_style",
        mix_with=(InheritableMixin, SignalMixin,)
    )

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):

        my_kwargs = self.pop_kwargs(kwargs,
            "data_label", "data_visible", "data_position", "data_x_offset", "data_y_offset"
            "data_color", "data_base", "data_angle", "data_align",
            *[prop.label for prop in type(self).Meta.get_local_persistent_properties()]
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
