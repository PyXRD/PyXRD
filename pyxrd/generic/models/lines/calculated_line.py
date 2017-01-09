# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
from mvc.models.properties.tools import modify
logger = logging.getLogger(__name__)

from mvc.models.properties import (
    ListProperty, SignalMixin
)

from pyxrd.data import settings
from pyxrd.generic.io import storables

from pyxrd.generic.models.base import DataModel

from .pyxrd_line import PyXRDLine

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