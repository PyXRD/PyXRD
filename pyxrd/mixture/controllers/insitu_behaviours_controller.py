# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.


from contextlib import contextmanager

from mvc.models.base import Model

from pyxrd.generic.controllers import ObjectListStoreController

from pyxrd.mixture.models import InSituBehaviour, insitu_behaviours
from pyxrd.mixture.views import EditInSituBehaviourView


from pyxrd.mixture.views.add_insitu_behaviour_view import AddInSituBehaviourView

from .edit_insitu_behaviour_controller import EditInSituBehaviourController
from .add_insitu_behaviour_controller import AddInSituBehaviourController

class InSituBehavioursController(ObjectListStoreController):

    treemodel_property_name = "behaviours"
    treemodel_class_type = InSituBehaviour
    columns = [ ("Mixture name", "c_name") ]
    delete_msg = "Deleting a mixture is irreverisble!\nAre You sure you want to continue?"
    obj_type_map = [
        (cls, EditInSituBehaviourView, EditInSituBehaviourController)
        for name, cls in list(insitu_behaviours.__dict__.items()) if hasattr(cls, 'Meta') and cls.Meta.concrete
    ]

    def get_behaviours_tree_model(self, *args):
        return self.treemodel

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_load_object_clicked(self, event):
        pass # cannot load behaviours
    
    def on_save_object_clicked(self, event):
        pass # cannot save behaviours

    def get_new_edit_view(self, obj):
        """
            Gets a new 'edit object' view for the given obj, view and parent
            view.
        """
        if obj == None:
            return self.view.none_view
        else:
            for obj_tp, view_tp, ctrl_tp in self.obj_type_map: # @UnusedVariable
                if isinstance(obj, obj_tp):
                    return view_tp(obj.Meta, parent=self.view)
            raise NotImplementedError("Unsupported object type; subclasses of"
                " TreeControllerMixin need to define an obj_type_map attribute!")

    def create_new_object_proxy(self):
        
        def on_accept(behaviour_type):
            if behaviour_type is not None:
                self.add_object(behaviour_type(parent=self.model))

        # TODO re-use this and reset the COMBO etc.
        self.add_model = Model()
        self.add_view = AddInSituBehaviourView(parent=self.view)
        self.add_ctrl = AddInSituBehaviourController(
            model=self.add_model, view=self.add_view, parent=self,
            callback=on_accept
        )

        self.add_view.present()
        return None

    @contextmanager
    def _multi_operation_context(self):
        with self.model.data_changed.hold():
            yield

    pass # end of class