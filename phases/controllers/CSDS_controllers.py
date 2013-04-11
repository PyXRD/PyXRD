# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from traceback import format_exc

import gtk

from gtkmvc import Controller
from gtkmvc.adapters import Adapter

import settings

from generic.controllers import BaseController

from phases.views import EditCSDSDistributionView
from phases.CSDS_models import CSDS_distribution_types

class EditCSDSTypeController(BaseController):
    """ 
        Controller for the selection of the type of CSDS Model
    """

    distributions_controller = None

    def reset_type_store(self):
        combo = self.view["cmb_type"]
        store = gtk.ListStore(str, object)
        
        for cls in CSDS_distribution_types:
            store.append([cls.__description__, cls])
        combo.set_model(store)

        for row in store:
            if type(self.model.CSDS_distribution) == store.get_value(row.iter, 1):
                combo.set_active_iter(row.iter)
                break
        return store

    def register_view(self, view):
        combo = self.view["cmb_type"]
        combo.connect('changed', self.on_changed)
        cell = gtk.CellRendererText()
        combo.pack_start(cell, True)
        combo.add_attribute(cell, 'markup', 0)    

    def register_adapters(self):
        if self.model is not None:
            store = self.reset_type_store()
            if self.distributions_controller==None:      
                self.distributions_controller = EditCSDSDistributionController(
                    model=self.model.CSDS_distribution,
                    view=self.view,
                    parent=self)
            else:
                self.distributions_controller.reset_model(self.model)
       
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_changed(self, combo, user_data=None):
        itr = combo.get_active_iter()
        if itr != None:
            cls = combo.get_model().get_value(itr, 1)
            if not type(self.model.CSDS_distribution) == cls:
                new_csds_model = cls(parent=self.model)
                self.model.CSDS_distribution = new_csds_model
                self.distributions_controller.reset_model(new_csds_model)
                    
    pass #end of class

class EditCSDSDistributionController(BaseController):
    """ 
        Controller for the CSDS Models 
        Handles the creation of widgets based on their PropIntel settings
    """
    
    def reset_model(self, new_model):
        self.relieve_model(self.model)
        self.model = new_model
        self.observe_model(new_model)
        self.register_adapters()
            
    def register_adapters(self):
        if self.model is not None:
            self.view.reset_params()
            for intel in self.model.__model_intel__:
                if intel.refinable:
                    widget = self.view.add_param_widget(intel.label, intel.minimum, intel.maximum)
                    #adapt the widget to the model property:
                    adapter = Adapter(self.model, intel.name)
                    adapter.connect_widget(widget)
                    self.adapt(adapter)
            self.view.update_figure(self.model.distrib[1])
    
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("updated", signal=True)
    def notif_updated(self, model, prop_name, info):
        if self.model.distrib!=None and not self.model.phase.project.before_needs_update_lock:
            try: self.view.update_figure(self.model.distrib[1])
            except any as error:
                print "Caught unhandled exception: %s" % error
                print format_exc()
    
    pass #end of class
