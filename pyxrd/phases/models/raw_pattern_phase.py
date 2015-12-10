# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from mvc import PropIntel

from pyxrd.generic.io import storables, Storable, get_case_insensitive_glob
#from pyxrd.generic.io.xrd_parsers import XRDParser
from pyxrd.generic.io.file_parsers import parsers
from pyxrd.generic.models.lines import PyXRDLine

from pyxrd.refinement.refinables.metaclasses import PyXRDRefinableMeta

from .abstract_phase import AbstractPhase

@storables.register()
class RawPatternPhase(AbstractPhase, Storable):

    # MODEL INTEL:
    __metaclass__ = PyXRDRefinableMeta
    class Meta(AbstractPhase.Meta):
        properties = [
            PropIntel(name="name", data_type=unicode, label="Name", is_column=True, has_widget=True, storable=True),
            PropIntel(name="raw_pattern", label="Raw pattern", data_type=object, is_column=True, storable=True, has_widget=True, widget_type="xy_list_view"),
        ]
        store_id = "RawPatternPhase"
        file_filters = [
            ("Phase file", get_case_insensitive_glob("*.PHS")),
        ]
        rp_filters = [parser.file_filter for parser in parsers["xrd"]]
        rp_export_filters = [parser.file_filter for parser in parsers["xrd"] if parser.can_write]


    _data_object = None
    @property
    def data_object(self):
        self._data_object.type = "RawPatternPhase"

        self._data_object.raw_pattern_x = self.raw_pattern.data_x
        self._data_object.raw_pattern_y = self.raw_pattern.data_y[:, 0]
        self._data_object.apply_lpf = False
        self._data_object.apply_correction = False

        print "Y DATA", self._data_object.raw_pattern_y

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

    def __repr__(self):
        return "RawPatternPhase(name='%s')" % (self.name)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @AbstractPhase.observe("data_changed", signal=True)
    def notify_data_changed(self, model, prop_name, info):
        self.data_changed.emit() # propagate signal

    pass #end of class
