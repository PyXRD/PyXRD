# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.
import gtk 

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvasGTK

from generic.views import ObjectListStoreView, DialogView, BaseView

#TODO add widgets to hide when in VIEW MODE!!

class SpecimenView(DialogView):
    title = "Edit Specimen"
    subview_builder = "specimen/glade/specimen.glade"
    subview_toplevel = "edit_specimen"
    resizable = False
    
    __widgets_to_hide__ = (
        "entry_align_absolute_scale",
        "lbl_spec_scale",
        "bg_shift_align",
        "lbl_spec_bgshift",
        "absorption_align",
        "absorption_lbl",
        "lbl_spec_length",
        "entry_align_sample_length",
        "specimen_display_calculated",
        "specimen_display_stats_in_lbl",
        "specimen_inherit_calc_color",
        "specimen_calc_color",
        "specimen_display_phases",
        "vbox_calculated_data_tv",
        "lbl_specimen_calculated",
        "vbox_exclusion_ranges_tv",
        "lbl_tabexclusions",)

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
        #print self[bg_view], self[self.bg_view_cont]
        self._add_child_view(self[bg_view], self[self.bg_view_cont])
      
class SmoothDataView(DialogView):
    title = "Smooth Data"
    subview_builder = "specimen/glade/smoothing.glade"
    subview_toplevel = "smooth_data"
    modal = True
    resizable = False
     
class ShiftDataView(DialogView):
    title = "Shift Pattern"
    subview_builder = "specimen/glade/shifting.glade"
    subview_toplevel = "shift_pattern"
    modal = True
    resizable = False
      
class EditMarkersView(ObjectListStoreView):
    extra_widget_builder = "specimen/glade/find_peaks.glade"
    extra_widget_toplevel = "vbox_find_peaks"
    resizable = False
    
    def __init__(self, *args, **kwargs):
        ObjectListStoreView.__init__(self, *args, **kwargs)
        
        self[self.subview_toplevel].child_set_property(self["frame_object_param"], "resize", False)
        
class DetectPeaksView(DialogView):
    title = "Auto detect peaks"
    subview_builder = "specimen/glade/find_peaks_dialog.glade"
    subview_toplevel = "tbl_find_peaks"
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
        
class StatisticsView(BaseView):
    builder = "specimen/glade/statistics.glade"
    top = "statistics_box"
    
    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)       
