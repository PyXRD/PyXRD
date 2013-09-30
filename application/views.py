# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import types

import gtk
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

import settings

from generic.views import ObjectListStoreView, BaseView, HasChildView

from project.views import ProjectView
from specimen.views import SpecimenView, EditMarkersView

class AppView(BaseView, HasChildView):
    """
        The main application interface view.
        
        Attributes:
            project: the project view
            specimen: the specimen view
            markers: the markers view
            phases: the phases view
            atom_types: the atom_types view
            statistics: the statistics view
            mixtures: the mixtures view
            
        
    """
    builder = "application/glade/application.glade"

    top = "main_window"

    child_views = {
        "project": ProjectView,
        "specimen": SpecimenView,
        "markers": EditMarkersView, # FIXME this should be part of the specimen view/controller code
        "phases": ObjectListStoreView,
        "atom_types": ObjectListStoreView,
        # ("statistics": ???
        "mixtures": ObjectListStoreView
    }

    widget_groups = {
        'full_mode_only': [
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
            "main_menu_item_edit_mixtures",
            "navtoolbar"
        ]
    }

    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)

        # Setup about window:
        self["about_window"].set_version(settings.VERSION)
        pixbuf = gtk.gdk.pixbuf_new_from_file("application/icons/pyxrd.png")
        scaled_buf = pixbuf.scale_simple(212, 160, gtk.gdk.INTERP_BILINEAR)
        self["about_window"].set_logo(scaled_buf)

        # self.set_layout_modes()
        self.reset_all_views()
        if not settings.DEBUG:
            self.get_top_widget().maximize()

        self.get_top_widget().show_all()

        return

    def setup_plot(self, plot_controller):
        self.plot_controller = plot_controller
        self["matplotlib_box"].add(self.plot_controller.canvas)
        self["matplotlib_box"].show_all()
        self.nav_toolbar = NavigationToolbar(self.plot_controller.canvas, self.get_top_widget())
        self.nav_toolbar.set_name("navtoolbar")
        self["navtoolbar"] = self.nav_toolbar
        self["navtoolbar_box"].add(self.nav_toolbar)

    def reset_child_view(self, view_name, class_type=None):
        if getattr(self, view_name, None) != None:
            getattr(self, view_name).hide()
            setattr(self, view_name, None)
        if class_type == None:
            class_type = self.child_views[view_name]
        view = class_type(parent=self)
        setattr(self, view_name, view)
        view.set_layout_mode(self.current_layout_state)
        return view

    def reset_all_views(self):
        for view_name, class_type in self.child_views.iteritems():
            self.reset_child_view(view_name, class_type)

    def set_specimens_widget(self, widget):
        self._add_child_view(widget, self["specimens_container"])

    def set_layout_mode(self, mode):
        super(AppView, self).set_layout_mode(mode)
        for view_name in self.child_views:
            getattr(self, view_name).set_layout_mode(mode)

    def show(self, *args, **kwargs):
        BaseView.show(self, *args, **kwargs)

    def get_toplevel(self):
        return self["main_window"]

    pass # end of class
