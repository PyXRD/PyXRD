# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

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
        "tbtn_edit_phases",
        "tbtn_edit_atom_types",
        "tbtn_edit_mixtures",
        "tbtn_separator1",
        "btn_sample",
        "separator3",
        "separator4",
        "separator5",
        "main_menu_item_edit_phases",
        "main_menu_item_edit_atom_types",
        "main_menu_item_edit_mixtures")
    
    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)

        #Setup about window:
        self["about_window"].set_version(settings.VERSION)
        pixbuf = gtk.gdk.pixbuf_new_from_file("application/icons/pyxrd.png")
        scaled_buf = pixbuf.scale_simple(212,160,gtk.gdk.INTERP_BILINEAR)
        self["about_window"].set_logo(scaled_buf)

        self.reset_all_views()
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
        #view = self._reset_child_view("statistics", StatisticsView)
        #child = self["statistics_expander"].get_child()
        #if child is not None:
        #    self["statistics_expander"].remove(child)
        #self["statistics_expander"].add(view[view.top])
        #if not settings.VIEW_MODE:
        #    self["statistics_expander"].show_all()
        #else:
        #    self["statistics_expander"].set_visible(False)
        #return view
        pass
        
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
        
