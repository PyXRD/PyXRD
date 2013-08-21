# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk
from generic.views import DialogView, BaseView

class GoniometerViewMixin(object):
    @property
    def import_combo_box(self):
        return self["cmb_import_gonio"]

    @property
    def wavelength_combo_box(self):
        return self["wavelength_combo_box"]

    pass #end of class

class GoniometerView(GoniometerViewMixin, DialogView):
    subview_builder = "goniometer/glade/goniometer.glade"
    subview_toplevel = "edit_goniometer"
    
    title = "Edit Goniometer"
    resizable = False
    model = True    
    
    pass #end of class
        
class InlineGoniometerView(GoniometerViewMixin, BaseView):
    builder = "goniometer/glade/goniometer.glade"
    top = "edit_goniometer"
    
    pass #end of class
