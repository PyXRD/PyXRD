# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import gtk

from mvc import Controller

from pyxrd.generic.controllers import BaseController

from pyxrd.phases.models.CSDS import CSDS_distribution_types

class EditCSDSTypeController(BaseController):
    """ 
        Controller for the selection of the type of CSDS Model
    """
    auto_adapt = False

    distributions_controller = None

    def reset_type_store(self):
        if self.view is not None:
            combo = self.view["cmb_type"]
            store = gtk.ListStore(str, object) # @UndefinedVariable

            for cls in CSDS_distribution_types:
                store.append([cls.Meta.description, cls])
            combo.set_model(store)

            for row in store:
                if type(self.model.CSDS_distribution) == store.get_value(row.iter, 1):
                    combo.set_active_iter(row.iter)
                    break
            return store

    def register_view(self, view):
        self.view = view
        combo = self.view["cmb_type"]
        combo.connect('changed', self.on_changed)
        cell = gtk.CellRendererText() # @UndefinedVariable
        combo.pack_start(cell, True)
        combo.add_attribute(cell, 'markup', 0)
        self.reset_type_store()
        self.reset_distributions_controller()

    @BaseController.model.setter
    def _set_model(self, model):
        super(EditCSDSTypeController, self)._set_model(model)
        self.reset_distributions_controller()


    def reset_distributions_controller(self):
        if self.view is not None:
            if self.distributions_controller is None:
                self.distributions_controller = EditCSDSDistributionController(
                    model=self.model.CSDS_distribution,
                    view=self.view,
                    parent=self)
            else:
                self.distributions_controller.model = self.model.CSDS_distribution

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_changed(self, combo, user_data=None):
        itr = combo.get_active_iter()
        if itr is not None:
            cls = combo.get_model().get_value(itr, 1)
            if not type(self.model.CSDS_distribution) == cls:
                new_csds_model = cls(parent=self.model)
                self.model.CSDS_distribution = new_csds_model
                self.distributions_controller.model = new_csds_model

    pass # end of class

class EditCSDSDistributionController(BaseController):
    """ 
        Controller for the CSDS Models 
        Handles the creation of widgets based on their PropIntel settings
    """

    auto_adapt = False

    def reset_view(self):
        if self.view is not None:
            self.view.reset_params()
            for prop in self.model.Meta.all_properties:
                if prop.refinable:
                    self.view.add_param_widget(
                        self.view.widget_format % prop.name, prop.label,
                        prop.minimum, prop.maximum
                    )
            self.view.update_figure(self.model.distrib[0])
            self.register_adapters()
            self.adapt()

    def register_view(self, view):
        if self.model is not None:
            self.reset_view()

    @BaseController.model.setter
    def model(self, model):
        super(EditCSDSDistributionController, self)._set_model(model)
        self.reset_view()

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("updated", signal=True)
    def notif_updated(self, model, prop_name, info):
        if self.model.distrib is not None and not self.model.phase.project.before_needs_update_lock:
            try: self.view.update_figure(self.model.distrib[0])
            except any as error:
                logger.exception("Caught unhandled exception: %s" % error)

    pass # end of class
