# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk 

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvasGTK

from generic.views import ObjectListStoreView, DialogView, BaseView


class SpecimenView(DialogView):
    title = "Edit Specimen"
    subview_builder = "specimen/glade/specimen.glade"
    subview_toplevel = "edit_specimen"
    resizable = False
    
    __widgets_to_hide__ = (
        "entry_align_absolute_scale",
        "spec_scale_lbl",
        "bg_shift_align",
        "spec_bgshift_lbl",
        "absorption_align",
        "absorption_lbl",
        "spec_length_lbl",
        "entry_sample_length_align",
        "specimen_display_calculated",
        "specimen_display_stats_in_lbl",
        "specimen_inherit_calc_color",
        "specimen_calc_color",
        "specimen_display_phases",
        "vbox_calculated_data_tv",
        "lbl_specimen_calculated",
        "vbox_exclusion_ranges_tv",
        "lbl_tabexclusions",
        "general_separator",
        "spb_calc_lw",
        "specimen_inherit_calc_lw",
    )

class EditMarkerView(BaseView):
    builder = "specimen/glade/edit_marker.glade"
    top = "edit_marker"
    
    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)
        
        self.parent.set_title("Edit Markers")
       
class BackgroundView(DialogView):
    title = "Remove Background"
    subview_builder = "specimen/glade/background.glade"
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
      
class SmoothDataView(DialogView):
    title = "Smooth Data"
    subview_builder = "specimen/glade/smoothing.glade"
    subview_toplevel = "smooth_data"
    modal = True
    resizable = False
     
    pass #end of class
     
class ShiftDataView(DialogView):
    title = "Shift Pattern"
    subview_builder = "specimen/glade/shifting.glade"
    subview_toplevel = "shift_pattern"
    modal = True
    resizable = False

    pass #end of class
      
class EditMarkersView(ObjectListStoreView):
    extra_widget_builder = "specimen/glade/find_peaks.glade"
    extra_widget_toplevel = "vbox_find_peaks"
    resizable = False
    
    def __init__(self, *args, **kwargs):
        ObjectListStoreView.__init__(self, *args, **kwargs)
        
        self[self.subview_toplevel].child_set_property(self["frame_object_param"], "resize", False)

    pass #end of class
        
class MatchMineralsView(DialogView):
    title = "Match minerals"
    subview_builder = "specimen/glade/match_minerals.glade"
    subview_toplevel = "tbl_match_minerals"
    modal = True
    
    def __init__(self, *args, **kwargs):
        DialogView.__init__(self, *args, **kwargs)
        self.tv_minerals = self["tv_minerals"]
        self.tv_matches = self["tv_matches"]

    pass #end of class
        
class DetectPeaksView(DialogView):
    title = "Auto detect peaks"
    subview_builder = "specimen/glade/find_peaks_dialog.glade"
    subview_toplevel = "tbl_find_peaks"
    modal = True
    resizable = False
    
    __widgets_to_hide__ = (
        "pattern",
        "lbl_pattern",
        "hseparator1")
    
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
        
    pass #end of class
        
class StatisticsView(BaseView):
    builder = "specimen/glade/statistics.glade"
    top = "statistics_box"
    
    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)
        
    pass #end of class
