# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from ..data_object import DataObject
from pyxrd.generic.utils import not_none


class XRDDataObject(DataObject):
    """
        A generic class holding all the information retrieved from an XRD data
        file using an XRD-parser class.
    """

    # General information
    name = None
    date = None

    # x-axis range
    twotheta_min = None
    twotheta_max = None
    twotheta_count = None
    twotheta_step = None

    # Wavelength and target information
    target_type = None
    alpha1 = None
    alpha2 = None
    alpha_average = None
    beta = None
    alpha_factor = None

    # Goniometer setup
    radius = None
    soller1 = None
    soller2 = None
    divergence = None

    # Generator or list of x,y data
    data = None

    def create_gon_file(self):

        output = """        {
            "type": "Goniometer", 
            "properties": {
                "radius": %(radius)f, 
                "divergence": %(divergence)f, 
                "soller1": %(soller1)f, 
                "soller2": %(soller2)f, 
                "min_2theta": %(twotheta_min)f, 
                "max_2theta": %(twotheta_max)f, 
                "steps": %(twotheta_count)f, 
                "wavelength": %(alpha_average)f, 
                "has_ads": false, 
                "ads_fact": 1.0, 
                "ads_phase_fact": 1.0, 
                "ads_phase_shift": 0.0, 
                "ads_const": 0.0
            }
        }""" % dict(
            radius=float(not_none(self.radius, 25)),
            divergence=float(not_none(self.divergence, 0.5)),
            soller1=float(not_none(self.soller1, 2.5)),
            soller2=float(not_none(self.soller2, 2.5)),
            twotheta_min=float(not_none(self.twotheta_min, 3.0)),
            twotheta_max=float(not_none(self.twotheta_max, 45.0)),
            twotheta_count=float(not_none(self.twotheta_count, 2500)),
            alpha_average=float(not_none(self.alpha_average, 0.154056)),
        )
        f = StringIO(output)
        f.flush()
        return f


    pass #end of class
