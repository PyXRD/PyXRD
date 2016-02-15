# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os
from os.path import basename, dirname
from functools import wraps

import gtk
import gobject

from mvc.support.utils import not_none
from mvc.adapters.gtk_support.dialogs.dialog_factory import DialogFactory

from pyxrd.data import settings

from pyxrd.generic.controllers import BaseController
from pyxrd.generic.plot.controllers import MainPlotController
from pyxrd.generic.plot.eye_dropper import EyeDropper

from pyxrd.file_parsers.project_parsers import JSONProjectParser
from pyxrd.file_parsers.project_parsers import project_parsers

from pyxrd.project.controllers import ProjectController
from pyxrd.project.models import Project
from pyxrd.specimen.controllers import SpecimenController, MarkersController

from pyxrd.mixture.controllers import MixturesController
from pyxrd.phases.controllers import PhasesController
from pyxrd.atoms.controllers import AtomTypesController

class AppController (BaseController):
    """
        Controller handling the main application interface.
        In essence this delegates actions to its child controllers for Project,
        Mixture, Specimen, Phase, Marker and Atoms actions. 
    """

    # ------------------------------------------------------------
    #      Dialog properties
    # ------------------------------------------------------------
    _save_project_dialog = None
    @property
    def save_project_dialog(self):
        """ Creates & returns the 'save project' dialog """
        if self._save_project_dialog is None:
            # Check to see if we have a project loaded, if so,
            # set the paths to match
            current_name, current_folder = None, None
            if self.model.current_filename is not None:
                current_name = basename(self.model.current_filename)
                current_folder = dirname(self.model.current_filename)
            # Create the dialog once, and re-use its context
            self._save_project_dialog = DialogFactory.get_save_dialog(
                title="Save project",
                current_name=current_name,
                current_folder=current_folder,
                filters=project_parsers.get_export_file_filters(),
                persist=True,
                parent=self.view.get_top_widget()
            )
        return self._save_project_dialog

    _load_project_dialog = None
    @property
    def load_project_dialog(self):
        """ Creates & returns the 'load project' dialog """
        if self._load_project_dialog is None:
            # Check to see if we have a project loaded, if so,
            # set the paths to match
            current_folder = None
            if self.model.current_filename is not None:
                current_folder = dirname(self.model.current_filename)
            # Create the dialog once, and re-use
            self._load_project_dialog = DialogFactory.get_load_dialog(
                title="Load project",
                current_folder=current_folder,
                filters=project_parsers.get_import_file_filters(),
                persist=True,
                parent=self.view.get_top_widget()
            )
        return self._load_project_dialog

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, model, view, gtk_exception_hook=None, spurious=False, auto_adapt=False, parent=None):
        """ Initializes an AppController with the given arguments. """
        super(AppController, self).__init__(model=model, view=view, spurious=spurious, auto_adapt=auto_adapt, parent=parent)

        self.gtk_exception_hook = gtk_exception_hook
        self.gtk_exception_hook.parent_view = view.get_toplevel()

        # Plot controller:
        self.plot_controller = MainPlotController(self)
        view.setup_plot(self.plot_controller)

        # Child controllers:
        self.project = None
        self.specimen = None
        self.markers = None
        self.phases = None
        self.atom_types = None
        self.mixtures = None

        self.idle_redraw_plot()

        if self.model.project_loaded:
            self.reset_project_controller()

        self.push_status_msg("Done.")

    def register_view(self, view):
        """ Registers the view with this controller """
        if self.model.project_loaded:
            self.update_sensitivities()
            view.set_layout_mode(self.model.current_project.layout_mode)
        else:
            view.set_layout_mode(settings.DEFAULT_LAYOUT)

    def set_model(self, model):
        """ Sets the model in this controller """
        super(self, AppController).set_model(model)
        self.reset_project_controller()

    def reset_project_controller(self):
        """ Recreates all child controllers """
        self.view.reset_all_views()
        self.project = ProjectController(model=self.model.current_project, view=self.view.project, parent=self)
        self.phases = PhasesController(model=self.model.current_project, view=self.view.phases, parent=self)
        self.atom_types = AtomTypesController(model=self.model.current_project, view=self.view.atom_types, parent=self)
        self.mixtures = MixturesController(model=self.model.current_project, view=self.view.mixtures, parent=self)
        self.reset_specimen_controller()
        self.view.update_project_sensitivities(self.model.project_loaded)
        self.set_layout_mode(self.model.current_project.layout_mode)
        self.update_title()

    def reset_specimen_controller(self):
        """ Recreates only the specimen controllers """
        if self.model.specimen_selected:
            specimen_view = self.view.reset_child_view("specimen")
            self.specimen = SpecimenController(model=self.model.current_specimen, view=specimen_view, parent=self)
            markers_view = self.view.reset_child_view("markers")
            self.markers = MarkersController(model=self.model.current_specimen, view=markers_view, parent=self)
        else:
            self.specimen = None
            self.markers = None
        self.view.update_specimen_sensitivities(
            self.model.single_specimen_selected,
            self.model.multiple_specimens_selected
        )
        self.idle_redraw_plot()

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @BaseController.observe("needs_plot_update", signal=True)
    def notif_needs_plot_update(self, model, prop_name, info):
        """ 
            This handles needs_plot_update signals emitted by the Application
            model, in effect it is either a forwarded 'data_changed' or 
            'visuals_changed' signal coming from the 
            :class:`pyxrd.project.models.Project` model.
        """
        self.idle_redraw_plot()

    @BaseController.observe("current_project", assign=True, after=True)
    def notif_project_update(self, model, prop_name, info):
        self.reset_project_controller()

    @BaseController.observe("current_specimen", assign=True, after=True)
    @BaseController.observe("current_specimens", assign=True, after=True)
    def notif_specimen_changed(self, model, prop_name, info):
        self.reset_specimen_controller()

    # ------------------------------------------------------------
    #      View updating
    # ------------------------------------------------------------

    _idle_redraw_id = None
    _needs_redraw = False
    def idle_redraw_plot(self):
        """Adds a redraw plot function as 'idle' action to the main GTK loop."""
        if self._idle_redraw_id is None:
            self._idle_redraw_id = gobject.idle_add(self.redraw_plot)
        self._needs_redraw = True

    @BaseController.status_message("Updating display...")
    def redraw_plot(self):
        """Updates the plot"""
        if self._needs_redraw == True:
            self._needs_redraw = False
            self.plot_controller.update(
                clear=True,
                project=self.model.current_project,
                specimens=self.model.current_specimens[::-1]
            )
        if self._needs_redraw:
            return True
        else:
            self._idle_redraw_id = None
            return False


    def update_title(self):
        """Convenience method for setting the application view's title"""
        self.view.set_title(self.model.current_project.name)

    def update_sensitivities(self):
        """Convenience method for updating the application view's sensitivities"""
        self.view.update_project_sensitivities(self.model.project_loaded)
        self.view.update_specimen_sensitivities(
            self.model.single_specimen_selected,
            self.model.multiple_specimens_selected
        )

    def set_layout_mode(self, mode):
        """Convenience method for updating the application view's layout mode"""
        self.view.set_layout_mode(mode)

    # ------------------------------------------------------------
    #      Loading and saving of projects
    # ------------------------------------------------------------
    def _save_project(self, filename=None):
        # Set the filename to the current location if None or "" was given:
        filename = filename or self.model.current_filename

        # Try to save the project:
        with DialogFactory.error_dialog_handler(
                "An error has occurred while saving!\n<i>{0}</i>",
                parent=self.view.get_toplevel(), reraise=False):
            JSONProjectParser.write(self.model.current_project, filename, zipped=True)
            self.model.current_project.filename = filename

        # Update the title
        self.update_title()

    def confirm_discard_unsaved_changes(self,
            confirm_msg="The current project has unsaved changes,\n"
                        "are you sure you want to continue?",
            on_reject=None):
        """
            Function decorator which will check if a project is opened with
            unsaved changes and ask the user to confirm the action without first
            saving the changes.
        """
        def accept_decorator(on_accept):
            @wraps(on_accept)
            def accept_wrapper(self, *args, **kwargs):
                if self.model.current_project and self.model.current_project.needs_saving:
                    return DialogFactory.get_confirmation_dialog(
                        confirm_msg, parent=self.view.get_top_widget()
                    ).run(lambda d: on_accept(self, *args, **kwargs), on_reject)
                else:
                    return on_accept(self, *args, **kwargs)
            return accept_wrapper
        return accept_decorator

    @confirm_discard_unsaved_changes(
        "The current project has unsaved changes,\n"
        "are you sure you want to quit?")
    def quit(self, *args, **kwargs):
        gtk.main_quit()
        return False

    @confirm_discard_unsaved_changes(
        "The current project has unsaved changes,\n"
        "are you sure you want to load another project?")
    def load_project(self):
        """Convenience function for loading projects from different sources
        following similar user interaction paths"""
        def on_accept(dialog):
            # Try to load the project:
            with DialogFactory.error_dialog_handler(
                    "An error has occurred:\n<i>{0}</i>\n Your project was not loaded!",
                    parent=self.view.get_toplevel(), reraise=False):
                self.model.current_project = dialog.parser.parse(dialog.filename)
                self.model.current_project.parent = self.model
                # Update the title
                self.update_title()

        # Run the open/import project dialog:
        self.load_project_dialog.run(on_accept)

    @confirm_discard_unsaved_changes(
        "The current project has unsaved changes,\n"
        "are you sure you want to create a new project?")
    def new_project(self, *args, **kwargs):
        # Create a new project
        self.model.current_project = Project(parent=self.model)

        # Set the current filename property and update the title
        self.update_title()

        # Show the edit project dialog
        self.view.project.present()

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
        self.view["about_window"].show()
        return True

    def on_main_window_delete_event(self, widget, event):
        self.quit()
        return True

    def on_menu_item_quit_activate (self, widget, data=None):
        self.quit()
        return True

    def on_refresh_graph(self, event):
        if self.model.current_project:
            with self.model.current_project.data_changed.hold():
                self.model.current_project.update_all_mixtures()
                self.redraw_plot()

    def on_save_graph(self, event):
        filename = None
        if self.model.single_specimen_selected:
            filename = os.path.splitext(self.model.current_specimen.name)[0]
        else:
            filename = self.model.current_project.name
        self.plot_controller.save(
            parent=self.view.get_toplevel(),
            current_name=filename,
            num_specimens=len(self.model.current_specimens),
            offset=self.model.current_project.display_plot_offset)

    @BaseController.status_message("Sampling...", "sampling")
    def on_sample_point(self, event):
        """
            Sample a point on the plot and display the (calculated and)
            experimental data values in an information dialog.
        """

        self.edc = None

        def parse_x_pos(x_pos, event):
            # Clear the eye dropper controller
            self.edc.enabled = False
            self.edc.disconnect()
            del self.edc
            # Get experimental data at the sampled point
            exp_y = self.model.current_specimen.experimental_pattern.get_y_at_x(x_pos)
            message = "Sampled point:\n"
            message += "\tExperimental data:\t( %.4f , %.4f )\n" % (x_pos, exp_y)
            # Get calculated data if applicable
            if self.model.current_project.layout_mode == "FULL":
                calc_y = self.model.current_specimen.calculated_pattern.get_y_at_x(x_pos)
                message += "\tCalculated data:\t\t( %.4f , %.4f )" % (x_pos, calc_y)
            # Display message dialog
            DialogFactory.get_information_dialog(
                message, parent=self.view.get_toplevel()
            ).run()


        self.edc = EyeDropper(self.plot_controller, parse_x_pos)

    # ------------------------------------------------------------
    #      GTK Signal handlers - Project related
    # ------------------------------------------------------------
    @BaseController.status_message("Creating new project...", "new_project")
    def on_new_project_activate(self, widget, data=None):
        self.new_project()

    @BaseController.status_message("Displaying project data...", "edit_project")
    def on_edit_project_activate(self, widget, data=None):
        self.view.project.present()

    @BaseController.status_message("Open project...", "open_project")
    def on_open_project_activate(self, widget, data=None):
        """Open an existing project. Asks the user if (s)he's sure when an 
        unsaved project is loaded."""
        self.load_project()

    @BaseController.status_message("Save project...", "save_project")
    def on_save_project_activate(self, widget, *args):
        # No filename yet: show a dialog
        if not self.model.current_filename:
            self.save_project_dialog.update(title="Save project").run(
                lambda dialog: self._save_project(filename=dialog.filename)
            )
        else: # we already have a filename, overwrite:
            self._save_project()

    @BaseController.status_message("Save project as...", "save_project_as")
    def on_save_project_as_activate(self, widget, *args):
        self.save_project_dialog.update(title="Save project as").run(
            lambda dialog: self._save_project(filename=dialog.filename)
        )

    # ------------------------------------------------------------
    #      GTK Signal handlers - Mixtures related
    # -----------------------------------------------------------
    def on_edit_mixtures(self, widget, data=None):
        if self.model.project_loaded:
            self.view.mixtures.present()
        pass

    # ------------------------------------------------------------
    #      GTK Signal handlers - Specimen related
    # ------------------------------------------------------------
    def on_edit_specimen_activate(self, event):
        self.project.edit_specimen()
        return True

    def on_add_specimen_activate(self, event):
        self.project.add_specimen()
        return True

    def on_add_multiple_specimens(self, event):
        self.project.import_multiple_specimen()
        return True

    def on_del_specimen_activate(self, event):
        self.project.delete_selected_specimens()
        return True

    def on_replace_specimen_data_activate(self, event):
        if self.model.single_specimen_selected:
            self.specimen.on_replace_experimental_data()
        return True

    def on_export_specimen_data_activate(self, event):
        if self.model.single_specimen_selected:
            self.specimen.on_export_experimental_data()
        return True

    def on_convert_to_fixed_activate(self, event):
        for specimen in self.model.current_specimens:
            specimen.convert_to_fixed()

    def on_convert_to_ads_activate(self, event):
        for specimen in self.model.current_specimens:
            specimen.convert_to_ads()

    def on_remove_background(self, event):
        if self.model.single_specimen_selected:
            self.specimen.remove_background()
        else:
            self.project.remove_backgrounds(self.model.current_specimens)
        return True

    def on_smooth_data(self, event):
        if self.model.single_specimen_selected:
            self.specimen.smooth_data()
        return True

    def on_add_noise(self, event):
        if self.model.single_specimen_selected:
            self.specimen.add_noise()
        return True

    def on_shift_data(self, event):
        if self.model.single_specimen_selected:
            self.specimen.shift_data()
        return True

    def on_strip_peak(self, event):
        if self.model.single_specimen_selected:
            self.specimen.strip_peak()
        return True

    def on_peak_area(self, event):
        if self.model.single_specimen_selected:
            self.specimen.peak_area()
        return True

    # ------------------------------------------------------------
    #      GTK Signal handlers - Phases related
    # ------------------------------------------------------------
    def on_edit_phases_activate(self, event):
        if self.model.project_loaded:
            self.view.phases.present()
        return True

    # ------------------------------------------------------------
    #      GTK Signal handlers - Atom Types related
    # ------------------------------------------------------------
    def on_edit_atom_types_activate(self, event):
        if self.model.project_loaded:
            self.view.atom_types.present()
        return True

    # ------------------------------------------------------------
    #      GTK Signal handlers - Markers related
    # ------------------------------------------------------------
    def on_edit_markers_activate(self, event):
        if self.model.current_specimen is not None:
            self.view.markers.present()
        return True

    pass # end of class

