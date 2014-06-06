# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

import gtk
from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

from pyxrd.data import settings

from pyxrd.generic.views import ObjectListStoreView, BaseView, HasChildView, FormattedTitleView

from pyxrd.project.views import ProjectView
from pyxrd.specimen.views import SpecimenView, EditMarkersView
from pyxrd.application.icons import get_icon_list

class AppView(BaseView, HasChildView, FormattedTitleView):
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
    builder = resource_filename(__name__, "glade/application.glade")
    top = "main_window"
    title_format = "PyXRD - %s"

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

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(AppView, self).__init__(*args, **kwargs)

        # Setup about window:
        def on_aboutbox_response(dialog, response, *args):
            if response < 0:
                dialog.hide()
                dialog.emit_stop_by_name('response')

        def on_aboutbox_close(widget, event=None):
            self["about_window"].hide()
            return gtk.TRUE

        self["about_window"].set_version(settings.VERSION)
        pixbuf = gtk.gdk.pixbuf_new_from_file(resource_filename(__name__, "icons/pyxrd.png")) # @UndefinedVariable
        scaled_buf = pixbuf.scale_simple(212, 160, gtk.gdk.INTERP_BILINEAR) # @UndefinedVariable
        self["about_window"].set_logo(scaled_buf)
        self["about_window"].connect("response", on_aboutbox_response)
        self["about_window"].connect("close", on_aboutbox_close)
        self["about_window"].connect("delete_event", on_aboutbox_close)

        self["main_window"].set_icon_list(*get_icon_list())

        # self.set_layout_modes()
        self.reset_all_views()
        if not settings.DEBUG:
            self.get_top_widget().maximize()

        self.get_top_widget().show()

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
        if getattr(self, view_name, None) is not None:
            getattr(self, view_name).hide()
            setattr(self, view_name, None)
        if class_type == None:
            class_type = self.child_views[view_name]
        view = class_type(parent=self)
        setattr(self, view_name, view)
        view.set_layout_mode(self.current_layout_state)

        if view_name.lower() == "project":
            # Plug in this tree view in the main application:
            self._add_child_view(
                view.specimens_treeview_container, self["specimens_container"])

        return view

    def reset_all_views(self):
        for view_name, class_type in self.child_views.iteritems():
            self.reset_child_view(view_name, class_type)

    # ------------------------------------------------------------
    #      Sensitivity updates
    # ------------------------------------------------------------
    def update_project_sensitivities(self, project_loaded):
        """
            Updates the views sensitivities according to the flag 'project_loaded'
            indicating whether or not there's a project loaded.
        """
        self["main_pained"].set_sensitive(project_loaded)
        self["project_actions"].set_sensitive(project_loaded)
        for action in self["project_actions"].list_actions():
            action.set_sensitive(project_loaded)

    def update_specimen_sensitivities(self, single_specimen_selected, multiple_specimen_selected):
        """
            Updates the views sensitivities according to the flags 
            'single_specimen_active' indicating whether or not there's a single
            specimen selected (= active) and 'multiple_specimen_active' 
            indicating whether or not there are multiple specimen selected.
        """
        self["specimen_actions"].set_sensitive(single_specimen_selected)
        self["specimens_actions"].set_sensitive(single_specimen_selected or multiple_specimen_selected)

    # ------------------------------------------------------------
    #      View update methods
    # ------------------------------------------------------------
    def set_layout_mode(self, mode):
        super(AppView, self).set_layout_mode(mode)
        for view_name in self.child_views:
            getattr(self, view_name).set_layout_mode(mode)

    def show(self, *args, **kwargs):
        BaseView.show(self, *args, **kwargs)

    def get_toplevel(self):
        return self["main_window"]

    pass # end of class
