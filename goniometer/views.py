# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk
from generic.views import DialogView

class GoniometerView (DialogView):
    title = "Edit Goniometer"
    subview_builder = "goniometer/glade/goniometer.glade"
    subview_toplevel = "edit_goniometer"
    resizable = False
    model = True    
    
    @property
    def import_combo_box(self):
        return self["cmb_import_gonio"]

    @property
    def wavelength_combo_box(self):
        return self["wavelength_combo_box"]
