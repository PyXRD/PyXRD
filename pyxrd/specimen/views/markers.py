# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

import gtk

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvasGTK

from pyxrd.generic.views import ObjectListStoreView, DialogView, BaseView

class EditMarkerView(BaseView):
    builder = resource_filename(__name__, "../glade/edit_marker.glade")
    top = "edit_marker"

    widget_format = "marker_%s"

    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)

        self.parent.set_title("Edit Markers")

class EditMarkersView(ObjectListStoreView):
    extra_widget_builder = resource_filename(__name__, "../glade/find_peaks.glade")
    extra_widget_toplevel = "vbox_find_peaks"
    resizable = False

    def __init__(self, *args, **kwargs):
        ObjectListStoreView.__init__(self, *args, **kwargs)

        self[self.subview_toplevel].child_set_property(self["frame_object_param"], "resize", False)

    def set_selection_state(self, value):
        super(EditMarkersView, self).set_selection_state(value)
        self["cmd_match_minerals"].set_sensitive(value is not None)

    pass # end of class

class MatchMineralsView(DialogView):
    title = "Match minerals"
    subview_builder = resource_filename(__name__, "../glade/match_minerals.glade")
    subview_toplevel = "tbl_match_minerals"
    modal = True

    def __init__(self, *args, **kwargs):
        DialogView.__init__(self, *args, **kwargs)
        self.tv_minerals = self["tv_minerals"]
        self.tv_matches = self["tv_matches"]

    pass # end of class

class DetectPeaksView(DialogView):
    title = "Auto detect peaks"
    subview_builder = resource_filename(__name__, "../glade/find_peaks_dialog.glade")
    subview_toplevel = "tbl_find_peaks"
    modal = True
    resizable = False

    widget_groups = {
        'full_mode_only': [
            "pattern",
            "lbl_pattern",
            "hseparator1"
        ]
    }

    def __init__(self, *args, **kwargs):
        DialogView.__init__(self, *args, **kwargs)

        self.graph_parent = self["view_graph"]
        self.setup_matplotlib_widget()

    def setup_matplotlib_widget(self):
        style = gtk.Style()
        self.figure = Figure(dpi=72, edgecolor=str(style.bg[2]), facecolor=str(style.bg[2]))

        self.plot = self.figure.add_subplot(111)
        self.plot.set_ylabel('# of peaks', labelpad=1)
        self.plot.set_xlabel('Threshold', labelpad=1)
        self.plot.autoscale_view()

        self.figure.subplots_adjust(left=0.15, right=0.875, top=0.875, bottom=0.15)
        self.matlib_canvas = FigureCanvasGTK(self.figure)

        self.graph_parent.add(self.matlib_canvas)
        self.graph_parent.show_all()

    pass # end of class