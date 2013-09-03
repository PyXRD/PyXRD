# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from generic.views import BaseView

class InlineGoniometerView(BaseView):
    """
        The inline Goniometer view.
    """

    builder = "goniometer/glade/goniometer.glade"
    top = "edit_goniometer"

    @property
    def import_combo_box(self):
        return self["cmb_import_gonio"]

    @property
    def wavelength_combo_box(self):
        return self["wavelength_combo_box"]

    pass # end of class