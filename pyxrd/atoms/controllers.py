# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from contextlib import contextmanager
from os.path import dirname

import numpy as np

from mvc import Controller
from mvc.adapters.gtk_support.dialogs.dialog_factory import DialogFactory

from pyxrd.generic.controllers import BaseController, ObjectListStoreController
from pyxrd.atoms.models import AtomType
from pyxrd.atoms.views import EditAtomTypeView
from pyxrd.data import settings
from pyxrd.file_parsers.atom_type_parsers import atom_type_parsers

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
    file_filters = property(fget=lambda *a: atom_type_parsers.get_file_filters())
    export_filters = property(fget=lambda *a: atom_type_parsers.get_export_file_filters())
    treemodel_property_name = "atom_types"
    treemodel_class_type = AtomType
    columns = [ ("Atom type name", "c_name") ]
    delete_msg = "Deleting an atom type is irreversible!\nAre You sure you want to continue?"
    obj_type_map = [
        (AtomType, EditAtomTypeView, EditAtomTypeController),
    ]
    title = "Edit Atom Types"

    _export_atomtypes_dialog = None
    @property
    def export_atomtypes_dialog(self):
        """ Creates & returns the 'export atom types' dialog """
        if self._export_atomtypes_dialog is None:
            # Default location of the database:
            current_folder = dirname(settings.DATA_REG.get_file_path("ATOM_SCAT_FACTORS"))
            # Create the dialog once, and re-use
            self._export_atomtypes_dialog = DialogFactory.get_save_dialog(
                title="Export atom types",
                current_folder=current_folder,
                persist=True,
                filters=self.export_filters,
                parent=self.view.get_top_widget()
            )
        return self._export_atomtypes_dialog

    _import_atomtypes_dialog = None
    @property
    def import_atomtypes_dialog(self):
        """ Creates & returns the 'import atom types' dialog """
        if self._import_atomtypes_dialog is None:
            # Default location of the database:
            current_folder = dirname(settings.DATA_REG.get_file_path("ATOM_SCAT_FACTORS"))
            # Create the dialog once, and re-use
            self._import_atomtypes_dialog = DialogFactory.get_load_dialog(
                title="Import atom types",
                current_folder=current_folder,
                persist=True, multiple=False,
                filters=self.file_filters,
                parent=self.view.get_top_widget()
            )
        return self._import_atomtypes_dialog

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
        self.import_atomtypes_dialog.run(
            lambda dialog: self.model.load_atom_types(
                dialog.filename,
                dialog.parser
            )
        )

    def on_save_object_clicked(self, event):
        self.export_atomtypes_dialog.run(
            lambda dialog: dialog.parser.write(
                dialog.filename,
                self.get_selected_objects(),
                AtomType.Meta.get_local_storable_properties()
            )
        )

    pass # end of class

