# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import numpy as np

from mvc.models.xydata import XYData

from pyxrd.generic.io import storables, Storable

from pyxrd.generic.models.base import DataModel
from pyxrd.generic.utils import not_none

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
            with self.visuals_changed.hold_and_emit():
                super(StorableXYData, self).load_data_from_generator(generator, clear=clear)

    def set_data(self, x, y):
        """
            Sets data using the supplied x, y1, ..., yn arrays.
        """
        with self.data_changed.hold_and_emit():
            with self.visuals_changed.hold_and_emit():
                super(StorableXYData, self).set_data(x, y)

    def set_value(self, i, j, value):
        with self.data_changed.hold_and_emit():
            with self.visuals_changed.hold_and_emit():
                super(StorableXYData, self).set_value(i, j, value)

    def append(self, x, y):
        """
            Appends data using the supplied x, y1, ..., yn arrays.
        """
        with self.data_changed.hold_and_emit():
            with self.visuals_changed.hold_and_emit():
                super(StorableXYData, self).append(x, y)

    def insert(self, pos, x, y):
        """
            Inserts data using the supplied x, y1, ..., yn arrays at the given
            position.
        """
        with self.data_changed.hold_and_emit():
            with self.visuals_changed.hold_and_emit():
                super(StorableXYData, self).insert(pos, x, y)

    def remove_from_indeces(self, *indeces):
        with self.data_changed.hold_and_emit():
            with self.visuals_changed.hold_and_emit():
                super(StorableXYData, self).remove_from_indeces(*indeces)

    pass # end of class