# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

from pyxrd.generic.views import BaseView, DialogView

class InlineGoniometerView(BaseView):
    """
        The inline Goniometer view.
    """

    builder = resource_filename(__name__, "glade/goniometer.glade")
    top = "edit_goniometer"

    widget_format = "gonio_%s"

    @property
    def import_combo_box(self):
        return self["cmb_import_gonio"]

    @property
    def wavelength_combo_box(self):
        return self["wavelength_combo_box"]

    pass # end of class


class WavelengthDistributionView(DialogView):
    """
        The wavelength distribution view.
    """   
    subview_builder = resource_filename(__name__, "glade/wavelength_distribution.glade")
    subview_toplevel = "edit_wld"

    widget_format = "wld_%s"
    
    pass # end of class