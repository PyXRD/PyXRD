# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

from generic.views import DialogView

class BackgroundView(DialogView):
    title = "Remove Background"
    subview_builder = "generic/glade/lines/background.glade"
    subview_toplevel = "edit_background"
    modal = True
    resizable = False

    def_bg_view = "bg_linear"
    bg_view_cont = "bg_view_container"

    def select_bg_view(self, bg_view=None):
        if bg_view != None:
            bg_view = "bg_%s" % bg_view
        else:
            bg_view = self.def_bg_view
        self._add_child_view(self[bg_view], self[self.bg_view_cont])

    def set_file_dialog(self, dialog, callback):
        fcb_bg_pattern = gtk.FileChooserButton(dialog)
        fcb_bg_pattern.connect("file-set", callback)
        self["fcb_bg_container"].add(fcb_bg_pattern)

class AddNoiseView(DialogView):
    title = "Add Noise"
    subview_builder = "generic/glade/lines/add_noise.glade"
    subview_toplevel = "add_noise"
    modal = True
    resizable = False

    pass # end of class

class SmoothDataView(DialogView):
    title = "Smooth Data"
    subview_builder = "generic/glade/lines/smoothing.glade"
    subview_toplevel = "smooth_data"
    modal = True
    resizable = False

    pass # end of class

class ShiftDataView(DialogView):
    title = "Shift Pattern"
    subview_builder = "generic/glade/lines/shifting.glade"
    subview_toplevel = "shift_pattern"
    modal = True
    resizable = False

    pass # end of class

class StripPeakView(DialogView):
    title = "Strip Peak"
    subview_builder = "generic/glade/lines/strip_peak.glade"
    subview_toplevel = "strip_peak"
    modal = True
    resizable = False

    pass # end of class