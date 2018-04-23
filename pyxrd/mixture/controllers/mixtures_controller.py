# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from contextlib import contextmanager

from mvc.models.base import Model

from pyxrd.generic.controllers import ObjectListStoreController

from pyxrd.mixture.models import Mixture #, InSituMixture
from pyxrd.mixture.views import EditMixtureView, AddMixtureView #EditInSituMixtureView,

from .edit_mixture_controller import EditMixtureController
#from .edit_insitu_mixture_controller import EditInSituMixtureController
from .add_mixture_controller import AddMixtureController


class MixturesController(ObjectListStoreController):

    treemodel_property_name = "mixtures"
    treemodel_class_type = Mixture
    columns = [ ("Mixture name", "c_name") ]
    delete_msg = "Deleting a mixture is irreverisble!\nAre You sure you want to continue?"
    obj_type_map = [
        #(InSituMixture, EditInSituMixtureView, EditInSituMixtureController),
        (Mixture, EditMixtureView, EditMixtureController),
    ]

    def get_mixtures_tree_model(self, *args):
        return self.treemodel

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_load_object_clicked(self, event):
        pass # cannot load mixtures
    
    def on_save_object_clicked(self, event):
        pass # cannot save mixtures

    def create_new_object_proxy(self):
        """def on_accept(mixture_type):
            if mixture_type == "mixture":
                self.add_object(Mixture(parent=self.model))
            #elif mixture_type == "insitu":
            #    self.add_object(InSituMixture(parent=self.model))
                
        # TODO re-use this and reset the COMBO etc.
        self.add_model = Model()
        self.add_view = AddMixtureView(types_dict={
            'mixture': "Create a regular mixture", 
            #'insitu': "Create an in-situ mixture"
        }, parent=self.view)
        self.add_ctrl = AddMixtureController(
            model=self.add_model, view=self.add_view, parent=self.parent,
            callback=on_accept
        )

        self.add_view.present()"""
        return Mixture(parent=self.model) #None

    @contextmanager
    def _multi_operation_context(self):
        with self.model.data_changed.hold():
            yield

    pass # end of class