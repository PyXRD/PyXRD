# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk
import logging
from pyxrd.mvc.adapters.gtk_support.treemodels.utils import create_treestore_from_directory

logger = logging.getLogger(__name__)

from pyxrd.mvc import Model, Controller
from pyxrd.mvc.adapters.dummy_adapter import DummyAdapter

from pyxrd.data import settings

from pyxrd.generic.gtk_tools.utils import convert_string_to_gdk_color_int
from pyxrd.generic.views import ChildObjectListStoreView
from pyxrd.generic.views.treeview_tools import new_pb_column
from pyxrd.generic.views.combobox_tools import add_combo_text_column
from pyxrd.generic.controllers import DialogController, BaseController, ObjectListStoreController
from pyxrd.generic.controllers.objectliststore_controllers import wrap_list_property_to_treemodel
# from pyxrd.generic.models.treemodels.utils import create_treestore_from_directory

from pyxrd.probabilities.models import get_Gbounds_for_R, get_Rbounds_for_G
from pyxrd.probabilities.controllers import EditProbabilitiesController
from pyxrd.probabilities.views import EditProbabilitiesView

from pyxrd.phases.controllers import EditCSDSTypeController, ComponentsController
from pyxrd.phases.views import EditPhaseView, AddPhaseView, EditCSDSDistributionView
from pyxrd.phases.models import Phase
from pyxrd.generic.utils import not_none
from contextlib import contextmanager

class EditPhaseController(BaseController):
    """ 
        Controller for the phase edit view
    """
    probabilities_view = None
    probabilities_controller = None

    csds_view = None
    csds_controller = None

    components_view = None
    components_controller = None

    widget_handlers = {
        'custom': 'custom_handler',
    }

    @property
    def phases_treemodel(self):
        prop = self.model.project.Meta.get_prop_intel_by_name("phases")
        return wrap_list_property_to_treemodel(self.model.project, prop)

    def register_view(self, view):
        BaseController.register_view(self, view)

        self.csds_view = EditCSDSDistributionView(parent=self.view)
        self.view.set_csds_view(self.csds_view)

        if self.model.G > 1:
            self.probabilities_view = EditProbabilitiesView(parent=self.view)
            self.view.set_probabilities_view(self.probabilities_view)
        else:
            self.view.remove_probabilities()

        self.components_view = ChildObjectListStoreView(parent=self.view)
        self.components_view["button_add_object"].set_visible(False)
        self.components_view["button_add_object"].set_no_show_all(True)
        self.components_view["button_del_object"].set_visible(False)
        self.components_view["button_del_object"].set_no_show_all(True)
        self.view.set_components_view(self.components_view)

    @staticmethod
    def custom_handler(self, intel, widget): # TODO split out these 4 properties in their own adapters
        if intel.name in ("CSDS_distribution", "components", "probabilities", "based_on"):
            if intel.name == "CSDS_distribution":
                self.reset_csds_controller()
            elif intel.name == "components":
                self.reset_components_controller()
            elif intel.name == "probabilities":
                self.reset_probabilities_controller()
            elif intel.name == "based_on":
                combo = self.view["phase_based_on"]

                combo.set_model(self.phases_treemodel)
                combo.connect('changed', self.on_based_on_changed)

                def phase_renderer(celllayout, cell, model, itr, user_data=None):
                    phase = model.get_user_data(itr)
                    if phase: # FIXME an error can occur here if the phase list is cleared and the view is still open
                        cell.set_sensitive(phase.R == self.model.R and phase.G == self.model.G and phase.get_based_on_root() != self.model)
                add_combo_text_column(combo, data_func=phase_renderer, text_col=self.phases_treemodel.c_name)

                for row in self.phases_treemodel:
                    if self.phases_treemodel.get_user_data(row.iter) == self.model.based_on:
                        combo.set_active_iter (row.iter)
                        break

            return DummyAdapter(controller=self, prop=intel)

    def reset_csds_controller(self):
        if self.csds_controller is None:
            self.csds_controller = EditCSDSTypeController(
                model=self.model, view=self.csds_view, parent=self)
        else:
            self.csds_controller.model = self.model

    def reset_components_controller(self):
        self.components_controller = ComponentsController(
            model=self.model, view=self.components_view, parent=self)

    def reset_probabilities_controller(self):
        if self.probabilities_controller is None:
            if self.model.G > 1: # False if model is a multi-component phase
                self.probabilities_controller = EditProbabilitiesController(
                    model=self.model.probabilities,
                    view=self.probabilities_view, parent=self)
        else:
            self.probabilities_controller.model = self.model.probabilities

    def register_adapters(self):
        self.update_sensitivities()

    def update_sensitivities(self):
        can_inherit = (self.model.based_on is not None)

        for name in ("sigma_star", "display_color"):
            widget_name = "container_%s" % name
            self.view[widget_name].set_sensitive(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view[widget_name].set_visible(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view["phase_inherit_%s" % name].set_sensitive(can_inherit)

        for name in ("CSDS_distribution",):
            sensitive = not (can_inherit and getattr(self.model, "inherit_%s" % name))
            self.view["phase_inherit_%s" % name].set_sensitive(can_inherit)
            self.view.set_csds_sensitive(sensitive)
            self.reset_csds_controller()

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("inherit_display_color", assign=True)
    @Controller.observe("inherit_sigma_star", assign=True)
    @Controller.observe("inherit_CSDS_distribution", assign=True)
    def notif_change_inherit(self, model, prop_name, info):
        self.update_sensitivities()
        return

    @Controller.observe("probabilities", assign=True)
    def notif_change_probabilities(self, model, prop_name, info):
        self.reset_probabilities_controller()
        return

    @Controller.observe("name", assign=True)
    def notif_name_changed(self, model, prop_name, info):
        self.phases_treemodel.on_item_changed(self.model)
        return

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_based_on_changed(self, combo, user_data=None):
        itr = combo.get_active_iter()
        if itr is not None:
            val = combo.get_model().get_user_data(itr)
            # cannot be based on itself == not based on anything
            # cannot be based on a model with a different # of components
            if val != self.model and val.get_based_on_root() != self.model and val.G == self.model.G:
                self.model.based_on = val
                self.update_sensitivities()
                return
        combo.set_active(-1)
        self.update_sensitivities()
        self.model.based_on = None

class PhasesController(ObjectListStoreController):
    """ 
        Controller for the phases list
    """
    file_filters = Phase.Meta.file_filters
    treemodel_property_name = "phases"
    treemodel_class_type = Phase
    obj_type_map = [
        (Phase, EditPhaseView, EditPhaseController),
    ]
    multi_selection = True
    columns = [
        ("Phase name", "c_name"),
        (" ", "c_display_color"),
        ("R", "c_R"),
        ("#", "c_G"),
    ]
    delete_msg = "Deleting a phase is irreversible!\nAre You sure you want to continue?"
    title = "Edit Phases"

    def get_phases_tree_model(self, *args):
        return self.treemodel

    def load_phases(self, filename):
        index = self.get_selected_index()
        if index is not None: index += 1
        self.model.load_phases(filename, insert_index=index)

    def setup_treeview_col_c_display_color(self, treeview, name, col_descr, col_index, tv_col_nr):
        def set_pb(column, cell_renderer, tree_model, iter, col_index): # @ReservedAssignment
            try:
                color = tree_model.get_value(iter, col_index)
            except TypeError:
                pass # invalid iter
            else:
                color = convert_string_to_gdk_color_int(color)
                phase = tree_model.get_user_data(iter)
                pb, old_color = getattr(phase, "__col_c_pb", (None, None))
                if old_color != color:
                    pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 10, 20) # @UndefinedVariable
                    pb.fill(color)
                    setattr(phase, "__col_c_pb", (color, pb))
                cell_renderer.set_property('pixbuf', pb)

        treeview.append_column(new_pb_column(
            name,
            data_func=(set_pb, (col_index,)),
            resizable=False,
            expand=False))

        return True

    def create_new_object_proxy(self):
        def on_accept(filename, G, R):
            index = int(not_none(self.get_selected_index(), -1)) + 1
            if filename is None:
                self.add_object(Phase(G=int(G), R=int(R)))
            else:
                self.model.load_phases(filename, insert_index=index)

        # TODO re-use this and reset the COMBO etc.
        self.add_model = Model()
        self.add_view = AddPhaseView(parent=self.view)
        self.add_ctrl = AddPhaseController(
            model=self.add_model, view=self.add_view, parent=self.parent,
            callback=on_accept
        )

        self.add_view.present()
        return None

    @contextmanager
    def _multi_operation_context(self):
        with self.model.hold_mixtures_data_changed():
            with self.model.hold_mixtures_needs_update():
                with self.model.hold_phases_data_changed():
                    yield

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_save_object_clicked(self, event):
        def on_accept(dialog):
            logger.info("Exporting phases...")
            filename = self.extract_filename(dialog)
            Phase.save_phases(self.get_selected_objects(), filename=filename)
        self.run_save_dialog("Export phase", on_accept, parent=self.view.get_top_widget())
        return True


    def on_load_object_clicked(self, event):
        def on_accept(dialog):
            self.load_phases(dialog.get_filename())
        self.run_load_dialog("Import phase", on_accept, parent=self.view.get_top_widget())
        return True

class AddPhaseController(DialogController):
    """ 
        Controller for the add phase dialog
    """

    auto_adapt = False

    def __init__(self, model=None, view=None, parent=None, callback=None):
        super(AddPhaseController, self).__init__(
            model=model, view=view, parent=parent)
        self.callback = callback

    def register_view(self, view):
        self.update_bounds()
        self.generate_combo()

    def register_adapters(self):
        pass # has no intel, or a model!

    def update_R_bounds(self):
        if self.view is not None:
            min_R, max_R, R = get_Rbounds_for_G(
                self.view.get_G(), self.view.get_R())
            self.view["adj_R"].set_upper(max_R)
            self.view["adj_R"].set_lower(min_R)
            self.view["R"].set_value(R)

    def update_G_bounds(self):
        if self.view is not None:
            min_G, max_G, G = get_Gbounds_for_R(
                self.view.get_R(), self.view.get_G())
            self.view["adj_G"].set_upper(max_G)
            self.view["adj_G"].set_lower(min_G)
            self.view["G"].set_value(G)

    def update_bounds(self):
        self.update_G_bounds()
        self.update_R_bounds()

    def generate_combo(self):
        self.reload_combo_model()
        add_combo_text_column(
            self.view.phase_combo_box, text_col=0, sensitive_col=2)

    def reload_combo_model(self):
        cmb_model = create_treestore_from_directory(
            settings.DATA_REG.get_directory_path("DEFAULT_PHASES"), ".phs")
        self.view.phase_combo_box.set_model(cmb_model)

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.view.hide()
        self.callback(
            self.view.get_phase(), self.view.get_G(), self.view.get_R())
        return True

    def on_btn_generate_phases_clicked(self, event):
        from pyxrd.scripts.generate_default_phases import run
        def ui_callback(progress):
            self.view["gen_progress_bar"].set_fraction(progress)
            while gtk.events_pending():
                gtk.main_iteration()
        self.view["img_repeat"].set_visible(False)
        self.view["gen_spinner"].start()
        self.view["gen_spinner"].set_visible(True)
        self.view["gen_progress_bar"].set_visible(True)
        while gtk.events_pending():
            gtk.main_iteration()
        run(ui_callback=ui_callback)
        self.view["gen_progress_bar"].set_visible(False)
        self.view["img_repeat"].set_visible(True)
        self.view["gen_spinner"].stop()
        self.view["gen_spinner"].set_visible(False)
        self.reload_combo_model()
        return True

    def on_r_value_changed(self, *args):
        self.update_G_bounds()
        return True

    def on_g_value_changed(self, *args):
        self.update_R_bounds()
        return True

    def on_keypress(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.view.hide()
            return True
        if event.keyval == gtk.keysyms.Return:
            self.view.hide()
            self.callback(
                self.view.get_phase(), self.view.get_G(), self.view.get_R())
            return True

    def on_window_edit_dialog_delete_event(self, event, args=None):
        self.view.hide()
        return True # do not propagate

    pass # end of class
