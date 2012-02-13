# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import locale

import gtk

from gtkmvc import Controller
from gtkmvc.adapters import Adapter

from generic.utils import get_case_insensitive_glob
from generic.controllers import BaseController, DialogMixin, delayed
from generic.plot_controllers import MainPlotController, EyedropperCursorPlot

from project.controllers import ProjectController
from project.models import Project
from specimen.controllers import SpecimenController, MarkersController, StatisticsController
from specimen.models import Specimen

from goniometer.controllers import GoniometerController
from phases.controllers import PhasesController
from atoms.controllers import AtomTypesController

class AppController (BaseController, DialogMixin):

    file_filters = [("PyXRD Project files", get_case_insensitive_glob("*.pyxrd")),
                    ("All Files", "*.*")]

    def __init__(self, model, view, spurious=False, auto_adapt=False, parent=None):
        BaseController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt, parent=parent)
        
        self.plot_controller = MainPlotController(self)
        view.setup_plot(self.plot_controller)
        
        self.project = None
        self.goniometer = None
        self.specimen = None
        self.markers = None
        self.phases = None
        self.atom_types = None
        
        self.push_status_msg("Done.")
        return

    def register_view(self, view):
        self.view['statistics_expander'].connect("notify::expanded", self.on_statistics_expand)

    def set_model(self, model):
        BaseController.set_model(self, model)
        self.reset_project_controller()
        return

    def reset_project_controller(self):
        self.project = ProjectController(self.model.current_project, self.view.project, parent=self)
        self.phases = PhasesController(self.model.current_project, self.view.phases, parent=self)
        self.atom_types = AtomTypesController(self.model.current_project, self.view.atom_types, parent=self)
        #self.goniometer = GoniometerController(self.model.current_project.data_goniometer, self.view.goniometer, parent=self) FIXME?
        
    def reset_specimen_controller(self):
        self.specimen = SpecimenController(self.model.current_specimen, self.view.reset_specimen_view(), parent=self)
        if self.model.current_specimen != None:
            self.markers = MarkersController(self.model.current_specimen, self.view.reset_markers_view(), parent=self)    
            self.statistics = StatisticsController(self.model.current_specimen.statistics, self.view.reset_statistics_view(), parent=self)
        else:
            self.markers = None
            self.statistics = None
    
    def edit_specimen(self, specimen, title="Edit Specimen"):
        #self.push_status_msg("Editing specimen...", 'edit_specimen')
        self.view.specimen.set_title(title)
        self.view.specimen.present()
        return True

    def set_active_phases(self, project_model):
        self.phases = PhasesController(project_model, self.view.reset_phases_view(), parent=self)

    def edit_phases(self):
        if self.model.current_project is not None:
            self.set_active_phases(self.model.current_project)
        self.view.phases.present()
        return True

    def edit_atom_types(self):
        if self.model.current_project is not None:
            self.view.atom_types.present()
        return True

    def edit_markers(self):
        if self.model.current_specimen is not None:
            self.view.markers.present()
        return True

    @delayed
    def update_plot(self):
        self.redraw_plot(complete=False)
        
    def redraw_plot(self, complete=True):
        self.push_status_msg("Updating display...")       
        
        single = bool(self.model.current_specimen is not None or self.model.current_specimens == [])              
        labels = []
        
        if complete: self.plot_controller.unregister_all()
        
        if self.model.current_specimens is not None:
            num_species = len(self.model.current_specimens)
            offset_increment = 0.75
            offset = 0
            i = 0
            for specimen in self.model.current_specimens[::-1]:
                specimen.set_display_offset(offset)
                if complete: 
                    self.plot_controller.register(specimen, "on_update_plot", last=False)
                    for marker in specimen.data_markers._model_data:
                        self.plot_controller.register(marker, "on_update_plot", last=True)
                if not single:
                    labels.append((specimen.data_sample, 0.35 + offset))
                offset += offset_increment
                i += 1
    
        stats = (False, None)
        if single and self.model.statistics_visible:
            stats = (True, self.model.current_specimen.statistics.data_residual_pattern.line)
  
        self.plot_controller.update(
            new_title=self.get_plot_title() or "",
            clear=True,
            single=single,
            labels=labels,
            stats=stats)
        
        self.pop_status_msg()
                
    def get_plot_title(self):
        if self.model.current_specimen is not None:
            return "%s - %s" % (self.model.current_specimen.data_sample, self.model.current_specimen.data_name)
        else:
            return ""
        
    def update_title(self):
         self.view.get_top_widget().set_title("PyXRD - %s" % self.model.current_project.data_name)        
        
    def update_sensitivities(self):
        self.update_specimen_sensitivities()
        self.update_project_sensitivities()
        
    def update_project_sensitivities(self):
        sensitive = (self.model.current_project != None)
        self.view["main_pained"].set_sensitive(sensitive)
        self.view["project_actions"].set_sensitive(sensitive)
        
    def update_specimen_sensitivities(self):
        sensitive = (self.model.current_specimen != None)
        self.view["specimen_actions"].set_sensitive(sensitive)
        self.view["statistics_expander"].set_sensitive(sensitive)
        self.view['statistics_expander'].set_expanded(self.model.statistics_visible)
        sensitive = sensitive or (self.model.current_specimens is not None and len(self.model.current_specimens) >= 1)
        self.view["specimens_actions"].set_sensitive(sensitive)
        
    def save_project(self, filename=None):
        self.model.current_filename = filename or self.model.current_filename
        self.model.current_project.save_object(self.model.current_filename)
        
    def open_project(self, filename):
        self.model.current_project = Project.load_object(filename)
        self.model.current_filename = filename
        
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("current_project", assign=True, after=True)
    def notif_project_update(self, model, prop_name, info):
        self.reset_project_controller ()
        self.update_project_sensitivities ()
        return

    @Controller.observe("current_specimen", assign=True, after=True)
    @Controller.observe("current_specimens", assign=True, after=True)
    def notif_specimen_changed(self, model, prop_name, info):
        self.reset_specimen_controller ()
        self.update_specimen_sensitivities()
        self.redraw_plot()
        return
    
    @Controller.observe("statistics_visible", assign=True, after=True)
    def notif_statistics_toggle(self, model, prop_name, info):
        self.redraw_plot()
        return
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_statistics_expand(self, widget, param_spec, data=None):
        self.model.statistics_visible = widget.get_expanded()
        self.view['statistics_expander'].set_expanded(self.model.statistics_visible)
    
    def on_main_window_delete_event(self, widget, event):
        gtk.main_quit()
        return False

    def on_new_project_activate(self, widget, data=None):
        def on_accept(dialog):
            self.model.current_project = Project()
            self.update_title()
            self.view.project.present()
        if self.model.current_project != None:
            self.run_confirmation_dialog("Creating a new project will erase all data in the current project!\nAre You sure you want to continue?",
                                         on_accept, parent=self.view.get_top_widget())
        else:
            on_accept(None)

    def on_edit_project_activate(self, widget, data=None):
        #self.push_status_msg("Editing project...", 'edit_project')
        self.view.project.present()

    def on_open_project_activate(self, widget, data=None):
        def on_accept(dialog):
            print "Opening project..."
            self.open_project(dialog.get_filename())
        self.run_load_dialog(title="Open project",
                             on_accept_callback=on_accept,
                             parent=self.view.get_top_widget())

    def on_save_project_as_activate(self, widget, data=None, title="Save project as"):
        def on_accept(dialog):
            print "Saving project..."
            filename = self.extract_filename(dialog)
            self.save_project(filename=filename)
        self.run_save_dialog(title=title,
                             on_accept_callback=on_accept,
                             parent=self.view.get_top_widget())

    def on_save_project_activate(self, widget, data=None):
        if self.model.current_filename is None:
            self.on_save_project_as_activate(widget, data=data, title="Save project")
        else:
            self.save_project()

    def on_edit_gonio_activate(self, widget, data=None):
        #FIXME self.push_status_msg("Editing project...", 'edit_project')
        self.goniometer = GoniometerController(self.model.current_project.data_goniometer, self.view.goniometer, parent=self)
        self.view.goniometer.present()

    def on_specimens_treeview_popup_menu(self, widget, event):
        self.view["specimen_popup"].popup(None, None, None, 0, 0)
        return True

    def on_add_specimen_activate(self, event):
        #self.push_status_msg("Adding new specimen...", 'add_specimen')
        specimen = Specimen(parent=self.model.current_project)
        self.view["specimens_treeview"].set_cursor(self.model.current_project.add_specimen(specimen))
        self.edit_specimen(specimen, title="Create New Specimen")
        self.pop_status_msg('add_specimen')
        return True

    def on_add_multiple_specimens(self, event):        
        self.project.import_multiple_specimen()        
        return True

    def on_edit_specimen_activate(self, event):
        self.edit_specimen(self.project.get_selected_object())
        return True

    def on_del_specimen_activate(self, event):
        #self.push_status_msg("Deleting specimen...", 'del_specimen')
        tv = self.view["specimens_treeview"]
        path, col = tv.get_cursor()
        if path is not None:
            obj = tv.get_model().get_user_data_from_path(path)
            msg = gtk.MessageDialog(self.view.get_top_widget(),
                                    gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING,
                                    gtk.BUTTONS_YES_NO, 'Deleting a specimen is irreverisble!\nAre You sure you want to continue?')
            if msg.run() != gtk.RESPONSE_YES:
                msg.destroy()
                return
            msg.destroy()
            self.model.current_project.del_specimen(obj)
        self.pop_status_msg('del_specimen')
        return True

    def on_edit_phases_activate(self, event):
        self.edit_phases()
        return True

    def on_edit_atom_types_activate(self, event):
        self.edit_atom_types()
        return True

    def on_edit_markers_activate(self, event):
        self.edit_markers()
        return True

    def on_update_graph_activated(self, event):
        self.update_plot()

    def on_menu_item_quit_activate (self, widget, data=None):
        #FIXME unsaved data
        gtk.main_quit()
        return False

    def on_refresh_graph(self, event):
        self.update_plot()

    def on_save_graph(self, event):
        self.plot_controller.save()
         
    def on_sample_point(self, event):
        self.cid = -1
        self.fig = self.plot_controller.figure
        self.ret = self.view.get_toplevel()
        
        self.edc = EyedropperCursorPlot(self.plot_controller.canvas, self.plot_controller.canvas.get_window(), True, True)
        
        x_pos = -1
        def onclick(event):
            if event.inaxes:
                x_pos = event.xdata
            if self.cid != -1:
                self.fig.canvas.mpl_disconnect(self.cid)
            if self.edc != None:
                self.edc.enabled = False
                self.edc.disconnect()
                
            exp_xy = self.model.current_specimen.data_experimental_pattern.xy_data.interpolate(x_pos)[0]
            calc_xy = self.model.current_specimen.data_calculated_pattern.xy_data.interpolate(x_pos)[0]
            
            self.run_information_dialog("Sampled point:\n\tExperimental data:\t( %.4f , %.4f )\n\tCalculated data:\t\t( %.4f , %.4f )" % (exp_xy + calc_xy), parent=self.view.get_toplevel())
                
            self.ret.present()
        self.cid = self.fig.canvas.mpl_connect('button_press_event', onclick)


    pass # end of class
