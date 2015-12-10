# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from mvc import Controller
from mvc.adapters.dummy_adapter import DummyAdapter

from pyxrd.generic.views import ChildObjectListStoreView
from pyxrd.generic.views.combobox_tools import add_combo_text_column
from pyxrd.generic.controllers import BaseController
from pyxrd.generic.controllers.objectliststore_controllers import wrap_list_property_to_treemodel

from pyxrd.probabilities.controllers import EditProbabilitiesController
from pyxrd.probabilities.views import EditProbabilitiesView

from pyxrd.phases.controllers import (
    EditCSDSTypeController, ComponentsController
)
from pyxrd.phases.views import EditCSDSDistributionView

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
        if self.model.project is not None:
            prop = self.model.project.Meta.get_prop_intel_by_name("phases")
            return wrap_list_property_to_treemodel(self.model.project, prop)
        else:
            return None

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
            elif intel.name == "based_on" and self.phases_treemodel is not None:
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
