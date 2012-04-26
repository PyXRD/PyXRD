# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os
import gtk
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

import settings

from generic.views import ObjectListStoreView, BaseView, DialogView

from project.views import ProjectView
from goniometer.views import GoniometerView
from specimen.views import SpecimenView, EditMarkersView, StatisticsView

class AppView(BaseView):
    builder = "application/glade/application.glade"
    
    top = "main_window"
    project = None
    specimen = None
    markers = None
    goniometer = None
    phases = None
    atom_types = None
    statistics = None
    mixtures = None
    
    __widgets_to_hide__ = (
        "statistics_container",
        "tbtn_edit_phases",
        "tbtn_edit_atom_types",
        "tbtn_edit_mixtures",
        "tbtn_separator1",
        "btn_sample",
        "btn_view_statistics",
        "seperator2",
        "separator3",
        "separator4",
        "main_menu_item_edit_phases",
        "main_menu_item_edit_atom_types")
    
    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)

        self.reset_all_views()
        
        self.get_top_widget().set_icon(gtk.gdk.pixbuf_new_from_file(os.path.join(__file__[:__file__.rfind(os.sep)], "icon.png")))
        if not settings.DEBUG:
            self.get_top_widget().maximize()

        self.get_top_widget().show_all()

        return

    def setup_plot(self, plot_controller): 
        self.plot_controller = plot_controller
        self["matplotlib_box"].add(self.plot_controller.canvas)
        self["matplotlib_box"].show_all()
        
        if not settings.VIEW_MODE:
            self.nav_toolbar = NavigationToolbar(self.plot_controller.canvas, self.get_top_widget())
            self["navtoolbar_box"].add(self.nav_toolbar)
        
    def _reset_child_view(self, view_name, class_type):
        if getattr(self, view_name) != None:
            getattr(self, view_name).hide()
            setattr(self, view_name, None)
        setattr(self, view_name, class_type(parent=self))
        return getattr(self, view_name)

    def reset_all_views(self):
        self.reset_project_view()
        self.reset_goniometer_view()
        self.reset_specimen_view()
        self.reset_statistics_view()
        self.reset_markers_view()
        self.reset_atom_types_view()
        self.reset_phases_view()
        self.reset_mixtures_view()

    def reset_project_view(self):
        return self._reset_child_view("project", ProjectView)

    def reset_goniometer_view(self):
        return self._reset_child_view("goniometer", GoniometerView)

    def reset_specimen_view(self):
        return self._reset_child_view("specimen", SpecimenView)
        
    def reset_statistics_view(self):
        view = self._reset_child_view("statistics", StatisticsView)
        child = self["statistics_expander"].get_child()
        if child is not None:
            self["statistics_expander"].remove(child)
        self["statistics_expander"].add(view[view.top])
        if not settings.VIEW_MODE:
            self["statistics_expander"].show_all()
        else:
            self["statistics_expander"].set_visible(False)
        return view
        
    def reset_markers_view(self):
        return self._reset_child_view("markers", EditMarkersView)
        
    def reset_atom_types_view(self):
        return self._reset_child_view("atom_types", ObjectListStoreView)

    def reset_mixtures_view(self):
        return self._reset_child_view("mixtures", ObjectListStoreView)

    def reset_phases_view(self):
        return self._reset_child_view("phases", ObjectListStoreView)

    def show(self, *args, **kwargs):
        BaseView.show(self, *args, **kwargs)
        
    def get_toplevel(self):
        return self["main_window"]
        
