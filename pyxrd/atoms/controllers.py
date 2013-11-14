# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from pyxrd.gtkmvc import Controller

from pyxrd.generic.controllers import BaseController, ObjectListStoreController
from pyxrd.atoms.models import AtomType
from pyxrd.atoms.views import EditAtomTypeView
from pyxrd.data import settings

class EditAtomTypeController(BaseController):
    """
        The controller for the AtomType model and EditAtomTypeView view.
    """

    # ------------------------------------------------------------
    #      Initialisation and other internals
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
    file_filters = AtomType.__file_filters__
    model_property_name = "atom_types"
    columns = [ ("Atom type name", "c_name") ]
    delete_msg = "Deleting an atom type is irreverisble!\nAre You sure you want to continue?"
    obj_type_map = [
        (AtomType, EditAtomTypeView, EditAtomTypeController),
    ]
    title = "Edit Atom Types"

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def create_new_object_proxy(self):
        # new_atom_type =
        # self.model.add_atom_type(new_atom_type)
        # self.select_object(new_atom_type)
        return AtomType("New Atom Type", parent=self.model)

    def open_atom_type(self, filename):
        self.model.append(AtomType.load_object(filename))

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_load_object_clicked(self, event):
        def on_accept(open_dialog):
            print "Importing atom types..."
            fltr = open_dialog.get_filter()
            if fltr.get_name() == self.file_filters[0][0]:
                self.open_atom_type(open_dialog.get_filename())
            elif fltr.get_name() == self.file_filters[1][0]:
                def save_append(*args):
                    try:
                        self.model.atom_types.append(*args)
                    except AssertionError:
                        print "AssertionError raised when trying to add %s: most likely there is already an AtomType with this name!" % args
                AtomType.get_from_csv(open_dialog.get_filename(), save_append) # self.model.atom_types.append)
        self.run_load_dialog("Import atom types", on_accept, parent=self.view.get_top_widget())


    def on_save_object_clicked(self, event):
        def on_accept(save_dialog):
            print "Exporting atom types..."
            fltr = save_dialog.get_filter()
            filename = save_dialog.get_filename()
            if fltr.get_name() == self.file_filters[0][0]:
                if filename[len(filename) - 4:] != self.file_filters[0][1][1:]:
                    filename = "%s%s" % (filename, self.file_filters[0][1][1:])
                atom_type = self.get_selected_object()
                if atom_type is not None:
                    atom_type.save_object(filename=filename)
            elif fltr.get_name() == self.file_filters[1][0]:
                if filename[len(filename) - 4:] != self.file_filters[1][1][1:]:
                    filename = "%s%s" % (filename, self.file_filters[1][1][1:])
                AtomType.save_as_csv(filename, self.get_selected_objects())
        self.run_save_dialog("Export atom types", on_accept, parent=self.view.get_top_widget())

    pass # end of class

