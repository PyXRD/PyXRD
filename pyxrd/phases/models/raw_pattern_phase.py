# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from random import choice
import numpy as np

from mvc import PropIntel

from pyxrd.generic.io import storables, get_case_insensitive_glob
from pyxrd.generic.models.lines import PyXRDLine
from pyxrd.refinement.refinables.metaclasses import PyXRDRefinableMeta
from pyxrd.file_parsers.xrd_parsers import xrd_parsers

from .abstract_phase import AbstractPhase

@storables.register()
class RawPatternPhase(AbstractPhase):

    # MODEL INTEL:
    __metaclass__ = PyXRDRefinableMeta
    class Meta(AbstractPhase.Meta):
        properties = [
            PropIntel(name="display_color", data_type=str, label="Display color", is_column=True, has_widget=True, widget_type='color', storable=True),
            PropIntel(name="raw_pattern", label="Raw pattern", data_type=object, is_column=True, storable=True, has_widget=True, widget_type="xy_list_view"),
        ]
        store_id = "RawPatternPhase"
        file_filters = [
            ("Phase file", get_case_insensitive_glob("*.PHS")),
        ]
        rp_filters = xrd_parsers.get_import_file_filters()
        rp_export_filters = xrd_parsers.get_export_file_filters()

    _data_object = None
    @property
    def data_object(self):
        self._data_object.type = "RawPatternPhase"

        self._data_object.raw_pattern_x = self.raw_pattern.data_x
        self._data_object.raw_pattern_y = self.raw_pattern.data_y[:, 0]
        self._data_object.apply_lpf = False
        self._data_object.apply_correction = False

        return self._data_object

    project = property(AbstractPhase.parent.fget, AbstractPhase.parent.fset)

    _raw_pattern = None
    def get_raw_pattern(self): return self._raw_pattern
    def set_raw_pattern(self, value):
        if value != self._raw_pattern:
            with self.data_changed.hold_and_emit():
                if self._raw_pattern is not None:
                    self.relieve_model(self._raw_pattern)
                self._raw_pattern = value
                if self._raw_pattern is not None:
                    self.observe_model(self._raw_pattern)

    @property
    def max_intensity(self):
        """The maximum intensity of the current loaded profile"""
        _max = 0.0
        if self.raw_pattern is not None:
            _max = max(_max, np.max(self.raw_pattern.max_intensity))
        return _max

    _display_color = "#FFB600"
    def get_display_color(self): return self._display_color
    def set_display_color(self, value):
        if self._display_color != value:
            with self.visuals_changed.hold_and_emit():
                self._display_color = value

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):

        my_kwargs = self.pop_kwargs(kwargs,
            *[names[0] for names in RawPatternPhase.Meta.get_local_storable_properties()]
        )
        super(RawPatternPhase, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.data_changed.hold():
            self.raw_pattern = PyXRDLine(
                data=self.get_kwarg(kwargs, None, "raw_pattern"),
                parent=self
            )
            self.display_color = self.get_kwarg(kwargs, choice(self.line_colors), "display_color")
            self.inherit_display_color = self.get_kwarg(kwargs, False, "inherit_display_color")

    def __repr__(self):
        return "RawPatternPhase(name='%s')" % (self.name)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @AbstractPhase.observe("data_changed", signal=True)
    def notify_data_changed(self, model, prop_name, info):
        self.data_changed.emit() # propagate signal

    pass #end of class
