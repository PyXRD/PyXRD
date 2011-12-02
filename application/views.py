# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os
import gtk

from generic.views import ObjectListStoreView, BaseView, DialogView

from project.views import ProjectView
from goniometer.views import GoniometerView
from specimen.views import SpecimenView, EditMarkersView

class AppView(BaseView):
    builder = "application/glade/application.glade"
    
    top = "main_window"
    project = None
    specimen = None
    markers = None
    goniometer = None
    phases = None
    atom_types = None
    
    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)

        self.reset_project_view()
        self.reset_specimen_view()
        self.reset_markers_view()
        self.reset_goniometer_view()
        self.reset_phases_view()
        self.reset_atom_types_view()
        
        self.get_top_widget().set_icon(gtk.gdk.pixbuf_new_from_file(os.path.join(__file__[:__file__.rfind(os.sep)], "icon.png")))
        self.get_top_widget().show_all()

        return

    def setup_plot(self, plot_controller): 
        self.plot_controller = plot_controller
        self["matplotlib_box"].add(self.plot_controller.canvas)
        self["matplotlib_box"].show_all()

    def _reset_child_view(self, view_name, class_type):
        if getattr(self, view_name) != None:
            getattr(self, view_name).hide()
            setattr(self, view_name, None)
        setattr(self, view_name, class_type(parent=self))
        return getattr(self, view_name)

    def reset_project_view(self):
        return self._reset_child_view("project", ProjectView)

    def reset_goniometer_view(self):
        return self._reset_child_view("goniometer", GoniometerView)

    def reset_specimen_view(self):
        return self._reset_child_view("specimen", SpecimenView)
        
    def reset_markers_view(self):
        return self._reset_child_view("markers", EditMarkersView)
        
    def reset_atom_types_view(self):
        return self._reset_child_view("atom_types", ObjectListStoreView)

    def reset_phases_view(self):
        return self._reset_child_view("phases", ObjectListStoreView)

    def show(self, *args, **kwargs):
        #self.get_top_widget().maximize()
        BaseView.show(self, *args, **kwargs)
        
    def get_toplevel(self):
        return self["main_window"]
        
