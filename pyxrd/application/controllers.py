# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, sys
from shutil import copy2 as copy, move
from os.path import basename, dirname

import gtk
import gobject

from pyxrd.gtkmvc import Controller

from pyxrd.data import settings

from pyxrd.generic.controllers import BaseController, DialogMixin
from pyxrd.generic.io.utils import get_case_insensitive_glob
from pyxrd.generic.plot.controllers import MainPlotController, EyedropperCursorPlot

from pyxrd.project.controllers import ProjectController
from pyxrd.project.models import Project
from pyxrd.specimen.controllers import SpecimenController, MarkersController
from pyxrd.specimen.models import Specimen

from pyxrd.mixture.controllers import MixturesController
from pyxrd.phases.controllers import PhasesController
from pyxrd.atoms.controllers import AtomTypesController

class AppController (BaseController, DialogMixin):
    """
        Controller handling the main application interface.
    """

    file_filters = [
        ("PyXRD Project files", get_case_insensitive_glob("*.pyxrd", "*.zpd")),
        ("All Files", "*.*")
    ]

    import_filters = [
        ("Sybilla XML files", get_case_insensitive_glob("*.xml")),
        ("All Files", "*.*")
    ]

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, model, view, spurious=False, auto_adapt=False, parent=None):
        """ Initializes an AppController with the given arguments. """
        super(AppController, self).__init__(model, view, spurious=spurious, auto_adapt=auto_adapt, parent=parent)

        self.plot_controller = MainPlotController(self)
        view.setup_plot(self.plot_controller)

        self.project = None
        self.specimen = None
        self.markers = None
        self.phases = None
        self.atom_types = None
        self.mixtures = None

        self.push_status_msg("Done.")
        return

    def register_view(self, view):
        if self.model.current_project is not None:
            self.update_project_sensitivities ()
            view.set_layout_mode(self.model.current_project.layout_mode)
        else:
            view.set_layout_mode(settings.DEFAULT_LAYOUT)

    def set_model(self, model):
        super(self, AppController).set_model(model)
        self.reset_project_controller()
        return

    def reset_project_controller(self):
        self.view.reset_all_views()
        self.project = ProjectController(model=self.model.current_project, view=self.view.project, parent=self)
        self.phases = PhasesController(model=self.model.current_project, view=self.view.phases, parent=self)
        self.atom_types = AtomTypesController(model=self.model.current_project, view=self.view.atom_types, parent=self)
        self.mixtures = MixturesController(model=self.model.current_project, view=self.view.mixtures, parent=self)

    def reset_specimen_controller(self):
        if self.model.current_specimen is not None:
            view = self.view.reset_child_view("specimen")
            self.specimen = SpecimenController(model=self.model.current_specimen, view=view, parent=self)
            self.markers = MarkersController(model=self.model.current_specimen, view=self.view.reset_child_view("markers"), parent=self)
        else:
            self.specimen = None
            self.markers = None

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("needs_plot_update", signal=True)
    def notif_needs_plot_update(self, model, prop_name, info):
        # This is emitted by the Application model, in effect it is either a
        #  forwarded data_changed or visuals_changed signal coming from the
        #  project model.
        self.idle_redraw_plot()
        return

    @Controller.observe("current_project", assign=True, after=True)
    def notif_project_update(self, model, prop_name, info):
        self.reset_project_controller()
        self.update_project_sensitivities()
        self.set_layout_mode(self.model.current_project.layout_mode)
        self.update_title()
        return

    @Controller.observe("current_specimen", assign=True, after=True)
    @Controller.observe("current_specimens", assign=True, after=True)
    def notif_specimen_changed(self, model, prop_name, info):
        self.reset_specimen_controller()
        self.update_specimen_sensitivities()
        self.idle_redraw_plot()
        return

    # ------------------------------------------------------------
    #      View updating
    # ------------------------------------------------------------

    _idle_redraw_id = None
    def idle_redraw_plot(self):
        """
            Adds a redraw plot function as 'idle' action to the main GTK loop.
        """
        if self._idle_redraw_id is not None:
            gobject.source_remove(self._idle_redraw_id)
        self._idle_redraw_id = gobject.idle_add(self.redraw_plot)

    @BaseController.status_message("Updating display...")
    def redraw_plot(self):
        self.plot_controller.update(
            clear=True,
            project=self.model.current_project,
            specimens=self.model.current_specimens[::-1]
        )

    def update_title(self):
        self.view.get_top_widget().set_title("PyXRD - %s" % self.model.current_project.name)

    def update_sensitivities(self):
        self.update_specimen_sensitivities()
        self.update_project_sensitivities()

    def update_project_sensitivities(self):
        sensitive = (self.model.current_project is not None)
        self.view["main_pained"].set_sensitive(sensitive)
        self.view["project_actions"].set_sensitive(sensitive)
        for action in self.view["project_actions"].list_actions():
            action.set_sensitive(sensitive)

    def update_specimen_sensitivities(self):
        sensitive = (self.model.current_specimen is not None)
        self.view["specimen_actions"].set_sensitive(sensitive)
        sensitive = sensitive or (self.model.current_specimens is not None and len(self.model.current_specimens) >= 1)
        self.view["specimens_actions"].set_sensitive(sensitive)

    def set_layout_mode(self, mode):
        self.view.set_layout_mode(mode)

    # ------------------------------------------------------------
    #      Loading and saving of projects
    # ------------------------------------------------------------
    def save_project(self, filename=None):
        filename = filename or self.model.current_filename

        # create backup in case something goes wrong:
        try:
            backupfile = sys.path[0] + "/data/temp_backup.pyxrd"
            copy(filename, backupfile)
        except IOError:
            backupfile = None

        # try to save the project, if this fails, put the backup back
        try:
            self.model.current_project.save_object(filename)
            self.model.current_filename = filename
        except:
            if backupfile:
                move(backupfile, self.model.current_filename) # move original file back
                backupfile = None
            self.run_information_dialog("An error has occurred.\n Your project was not saved!", parent=self.view.get_top_widget())
            raise
        finally:
            if backupfile: os.remove(backupfile) # remove backup file

    def open_project(self, filename):
        try:
            self.model.current_project = Project.load_object(filename, parent=self.model)
            self.model.current_filename = filename
            self.update_title()
        except any as error:
            self.run_information_dialog("An error has occurred.\n Your project was not loaded!", parent=self.view.get_top_widget())
            print error

    def new_project(self):
        self.model.current_project = Project(parent=self.model)
        self.model.current_filename = None
        self.view.project.present()

    def import_project_from_xml(self, filename):
        try:
            self.model.current_project = Project.create_from_sybilla_xml(filename, parent=self.model)
            self.model.current_filename = None
            self.update_title()
            self.view.project.present()
        except any as error:
            self.run_information_dialog("An error has occurred.\n Your project was not imported!", parent=self.view.get_top_widget())
            print error

    # ------------------------------------------------------------
    #      GTK Signal handlers - general
    # ------------------------------------------------------------
    def on_manual_activate(self, widget, data=None):
        try:
            import webbrowser
            webbrowser.open(settings.MANUAL_URL)
        except:
            pass # ignore errors
        return True

    def on_about_activate(self, widget, data=None):
        # self.run_dialog(self.view["about_window"], destroy=True)
        self.view["about_window"].show()
        return True

    def on_main_window_delete_event(self, widget, event):
        def on_accept(dialog):
            gtk.main_quit()
            return False
        def on_reject(dialog):
            return True
        if self.model.current_project and self.model.current_project.needs_saving:
            return self.run_confirmation_dialog(
                "The current project has unsaved changes,\n"
                "are you sure you want to quit?",
                on_accept, on_reject,
                parent=self.view.get_top_widget())
        else:
            return on_accept(None)

    def on_menu_item_quit_activate (self, widget, data=None):
        self.view.get_toplevel().destroy()
        return True

    def on_refresh_graph(self, event):
        if self.model.current_project:
            self.model.current_project.update_all()

    def on_save_graph(self, event):
        filename = None
        if self.model.single_specimen_selected:
            filename = os.path.splitext(self.model.current_specimen.name)[0]
        else:
            filename = self.model.current_project.name
        self.plot_controller.save(
            parent=self.view.get_toplevel(),
            suggest_name=filename,
            num_specimens=len(self.model.current_specimens),
            offset=self.model.current_project.display_plot_offset)

    def on_sample_point(self, event):
        """
            Sample a point on the plot and display the (calculated and)
            experimental data values in an information dialog.
        """
        def onclick(edc, x_pos, event):
            if edc is not None:
                edc.enabled = False
                edc.disconnect()

            exp_y = self.model.current_specimen.experimental_pattern.xy_store.get_y_at_x(x_pos)
            calc_y = self.model.current_specimen.calculated_pattern.xy_store.get_y_at_x(x_pos)
            message = "Sampled point:\n"
            message += "\tExperimental data:\t( %.4f , %.4f )\n"
            if self.model.current_project.layout_mode == "FULL":
                message += "\tCalculated data:\t\t( %.4f , %.4f )"
            message = message % (x_pos, exp_y, x_pos, calc_y)
            self.run_information_dialog(message, parent=self.view.get_toplevel())
            del self.edc

        self.edc = EyedropperCursorPlot(
            self.plot_controller.figure,
            self.plot_controller.canvas,
            self.plot_controller.canvas.get_window(),
            onclick,
            True, True
        )

    # ------------------------------------------------------------
    #      GTK Signal handlers - Project related
    # ------------------------------------------------------------
    @BaseController.status_message("Creating new project...", "new_project")
    def on_new_project_activate(self, widget, data=None):
        def on_accept(dialog):
            print "Creating new project..."
            self.new_project()
        if self.model.current_project and self.model.current_project.needs_saving:
            self.run_confirmation_dialog(
                "The current project has unsaved changes,\n"
                "are you sure you want to create a new project?",
                on_accept, parent=self.view.get_top_widget())
        else:
            on_accept(None)

    @BaseController.status_message("Displaying project data...", "edit_project")
    def on_edit_project_activate(self, widget, data=None):
        self.view.project.present()

    @BaseController.status_message("Open project...", "open_project")
    def on_open_project_activate(self, widget, data=None):
        def on_open_project(dialog):
            def on_accept(dialog):
                print "Opening project..."
                self.open_project(dialog.get_filename())
            self.run_load_dialog(
                title="Open project",
                on_accept_callback=on_accept,
                parent=self.view.get_top_widget())
        if self.model.current_project and self.model.current_project.needs_saving:
            self.run_confirmation_dialog(
                "The current project has unsaved changes,\n"
                "are you sure you want to load another project?",
                on_open_project,
                parent=self.view.get_top_widget())
        else:
            on_open_project(None)

    @BaseController.status_message("Import Sybilla XML...", "import_project_xml")
    def on_import_project_sybilla_activate(self, widget, data=None, title="Import Sybilla XML"):
        def on_open_project(confirm_dialog):
            def on_accept(dialog):
                print "Importing project..."
                self.import_project_from_xml(self.extract_filename(dialog))
            self.run_load_dialog(
                title="Import project",
                on_accept_callback=on_accept,
                filters=self.import_filters,
                parent=self.view.get_top_widget())
        if self.model.current_project and self.model.current_project.needs_saving:
            self.run_confirmation_dialog(
                "The current project has unsaved changes,\n"
                "are you sure you want to create a new project?",
                on_open_project,
                parent=self.view.get_top_widget())
        else:
            on_open_project(None)

    @BaseController.status_message("Save project...", "save_project")
    def on_save_project_activate(self, widget, data=None):
        if self.model.current_filename is None:
            self.on_save_project_as_activate(widget, data=data, title="Save project")
        else:
            self.save_project()

    @BaseController.status_message("Save project...", "save_project")
    def on_save_project_as_activate(self, widget, data=None, title="Save project as"):
        def on_accept(dialog):
            print "Saving project..."
            filename = self.extract_filename(dialog)
            self.save_project(filename=filename)
        suggest_name, suggest_folder = None, None
        if self.model.current_filename is not None:
            suggest_name = basename(self.model.current_filename)
            suggest_folder = dirname(self.model.current_filename)
        self.run_save_dialog(title=title,
                             suggest_name=suggest_name,
                             suggest_folder=suggest_folder,
                             on_accept_callback=on_accept,
                             parent=self.view.get_top_widget())

    # ------------------------------------------------------------
    #      GTK Signal handlers - Mixtures related
    # -----------------------------------------------------------
    @BaseController.status_message("Displaying mixtures view...", "edit_mixtures")
    def on_edit_mixtures(self, widget, data=None):
        if self.model.current_project is not None:
            self.view.mixtures.present()
        pass

    # ------------------------------------------------------------
    #      GTK Signal handlers - Specimen related
    # ------------------------------------------------------------
    @BaseController.status_message("Displaying specimen...", "edit_specimen")
    def on_edit_specimen_activate(self, event):
        self.view.specimen.present()
        return True

    def on_specimens_treeview_popup_menu(self, widget, data=None):
        self.view["specimen_popup"].popup(None, None, None, 0, 0)
        return True

    @BaseController.status_message("Creating new specimen...", "add_specimen")
    def on_add_specimen_activate(self, event):
        specimen = Specimen(parent=self.model.current_project)
        self.view.project.specimens_treeview.set_cursor(self.model.current_project.specimens.append(specimen))
        self.view.specimen.present()
        return True

    def on_add_multiple_specimens(self, event):
        self.project.import_multiple_specimen()
        return True

    def on_replace_specimen_data_activate(self, event):
        self.specimen.on_replace_experimental_data()

    def on_export_specimen_data_activate(self, event):
        self.specimen.on_export_experimental_data()

    @BaseController.status_message("Deleting specimen view...", "del_specimen")
    def on_del_specimen_activate(self, event):
        tv = self.view.project.specimens_treeview
        selection = tv.get_selection()
        if selection.count_selected_rows() >= 1:
            def delete_objects(dialog):
                for obj in self.project.get_selected_objects():
                    self.model.current_project.specimens.remove_item(obj)
            self.run_confirmation_dialog(
                message='Deleting a specimen is irreverisble!\nAre You sure you want to continue?',
                on_accept_callback=delete_objects,
                parent=self.view.get_top_widget())
        return True

    def on_remove_background(self, event):
        if self.model.current_specimen is not None:
            self.specimen.remove_background()
        return True

    def on_smooth_data(self, event):
        if self.model.current_specimen is not None:
            self.specimen.smooth_data()
        return True

    def on_add_noise(self, event):
        if self.model.current_specimen is not None:
            self.specimen.add_noise()
        return True

    def on_shift_data(self, event):
        if self.model.current_specimen is not None:
            self.specimen.shift_data()
        return True

    def on_strip_peak(self, event):
        if self.model.current_specimen is not None:
            self.specimen.strip_peak()
        return True

    # ------------------------------------------------------------
    #      GTK Signal handlers - Phases related
    # ------------------------------------------------------------
    @BaseController.status_message("Displaying phases view...", "edit_phases")
    def on_edit_phases_activate(self, event):
        if self.model.current_project is not None:
            self.view.phases.present()
        return True

    # ------------------------------------------------------------
    #      GTK Signal handlers - Atom Types related
    # ------------------------------------------------------------
    @BaseController.status_message("Displaying atom types view...", "edit_atom_types")
    def on_edit_atom_types_activate(self, event):
        if self.model.current_project is not None:
            self.view.atom_types.present()
        return True

    # ------------------------------------------------------------
    #      GTK Signal handlers - Markers related
    # ------------------------------------------------------------
    @BaseController.status_message("Displaying markers view...", "edit_markers")
    def on_edit_markers_activate(self, event):
        if self.model.current_specimen is not None:
            self.view.markers.present()
        return True

    pass # end of class

