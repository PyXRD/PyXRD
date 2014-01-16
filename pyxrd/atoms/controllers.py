# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from contextlib import contextmanager

import numpy as np

from pyxrd.mvc import Controller

from pyxrd.generic.controllers import BaseController, ObjectListStoreController
from pyxrd.atoms.models import AtomType
from pyxrd.atoms.views import EditAtomTypeView
from pyxrd.data import settings

class EditAtomTypeController(BaseController):
    """
        The controller for the AtomType model and EditAtomTypeView view.
    """

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def register_adapters(self):
        self.update_plot()

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update_plot(self):
        x, y = (), ()
        if self.model is not None:
            x = np.arange(0, 90.0, 90.0 / 100.0)
            y = self.model.get_atomic_scattering_factors(2 * np.sin(np.radians(x / 2)) / settings.DEFAULT_LAMBDA)
        self.view.update_figure(x, y)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("parameters_changed", signal=True)
    def notif_parameter_changed(self, model, prop_name, info):
        self.update_plot()

    pass # end of class

class AtomTypesController(ObjectListStoreController): # FIXME THIS NEES CLEAN-UP AND TESTING!!
    """
        Controller for an AtomType ObjectListStore model and view.
    """
    file_filters = AtomType.Meta.file_filters
    treemodel_property_name = "atom_types"
    treemodel_class_type = AtomType
    columns = [ ("Atom type name", "c_name") ]
    delete_msg = "Deleting an atom type is irreversible!\nAre You sure you want to continue?"
    obj_type_map = [
        (AtomType, EditAtomTypeView, EditAtomTypeController),
    ]
    title = "Edit Atom Types"

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_atom_types_tree_model(self, *args):
        return self.treemodel

    def create_new_object_proxy(self):
        return AtomType(name="New Atom Type", parent=self.model)

    @contextmanager
    def _multi_operation_context(self):
        with self.model.data_changed.hold():
            yield

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_load_object_clicked(self, event):
        def on_accept(open_dialog):
            fltr = open_dialog.get_filter()
            filename = open_dialog.get_filename()
            if fltr.get_name() == self.file_filters[0][0]:
                self.model.load_atom_types_from_csv(filename)
            elif fltr.get_name() == self.file_filters[1][0]:
                self.model.load_atom_types(filename)
        self.run_load_dialog("Import atom types", on_accept, parent=self.view.get_top_widget())

    def on_save_object_clicked(self, event):
        def on_accept(save_dialog):
            fltr = save_dialog.get_filter()
            filename = self.extract_filename(save_dialog, self.file_filters)
            if fltr.get_name() == self.file_filters[0][0]:
                AtomType.save_atom_types(filename, self.get_selected_objects())
            elif fltr.get_name() == self.file_filters[1][0]:
                AtomType.save_as_csv(filename, self.get_selected_objects())
        self.run_save_dialog("Export atom types", on_accept, parent=self.view.get_top_widget())

    pass # end of class

