# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

import gtk

from pyxrd.generic.views import DialogView, BaseView

class CalculatedLinePropertiesView(BaseView):
    builder = resource_filename(__name__, "glade/lines/calculated_props.glade")
    top = "cal_line_props"
    widget_format = "cal_%s"

    widget_groups = {
        'full_mode_only': [
            "cal_line_props"
        ]
    }

    pass # end of class

class ExperimentalLinePropertiesView(BaseView):
    builder = resource_filename(__name__, "glade/lines/experimental_props.glade")
    top = "exp_line_props"
    widget_format = "exp_%s"

    pass # end of class

class BackgroundView(DialogView):
    title = "Remove Background"
    subview_builder = resource_filename(__name__, "glade/lines/background.glade")
    subview_toplevel = "edit_background"
    modal = True
    resizable = False

    def_bg_view = "bg_linear"
    bg_view_cont = "bg_view_container"

    def select_bg_view(self, bg_view=None):
        if bg_view is not None:
            bg_view = "bg_%s" % bg_view
        else:
            bg_view = self.def_bg_view
        self._add_child_view(self[bg_view], self[self.bg_view_cont])

    def set_file_dialog(self, dialog, callback):
        fcb_bg_pattern = gtk.FileChooserButton(dialog)
        fcb_bg_pattern.connect("file-set", callback)
        self["fcb_bg_container"].add(fcb_bg_pattern)

    pass #end of class

class AddNoiseView(DialogView):
    title = "Add Noise"
    subview_builder = resource_filename(__name__, "glade/lines/add_noise.glade")
    subview_toplevel = "add_noise"
    modal = True
    resizable = False

    pass # end of class

class SmoothDataView(DialogView):
    title = "Smooth Data"
    subview_builder = resource_filename(__name__, "glade/lines/smoothing.glade")
    subview_toplevel = "smooth_data"
    modal = True
    resizable = False

    pass # end of class

class ShiftDataView(DialogView):
    title = "Shift Pattern"
    subview_builder = resource_filename(__name__, "glade/lines/shifting.glade")
    subview_toplevel = "shift_pattern"
    modal = True
    resizable = False

    pass # end of class

class StripPeakView(DialogView):
    title = "Strip Peak"
    subview_builder = resource_filename(__name__, "glade/lines/strip_peak.glade")
    subview_toplevel = "strip_peak"
    modal = True
    resizable = False

    pass # end of class

class CalculatePeakAreaView(DialogView):
    title = "Calculate Peak Area"
    subview_builder = resource_filename(__name__, "glade/lines/peak_area.glade")
    subview_toplevel = "peak_area"
    modal = True
    resizable = False

    pass # end of class
