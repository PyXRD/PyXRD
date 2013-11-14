# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

from pyxrd.generic.views.treeview_tools import new_text_column, new_combo_column, create_float_data_func, setup_treeview
from pyxrd.generic.controllers import InlineObjectListStoreController

from pyxrd.atoms.models import Atom

class EditLayerController(InlineObjectListStoreController):
    """ 
        Controller for the (inter)layer atom ObjectListStores
    """
    auto_adapt = False
    file_filters = Atom.__layer_filters__
    new_atom_type = None

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, model_property_name, stretch_values=False, *args, **kwargs):
        InlineObjectListStoreController.__init__(self, model_property_name, *args, **kwargs)
        self.new_atom_type = None
        self.stretch_values = stretch_values

    def _setup_treeview(self, tv, model):
        setup_treeview(tv, model, sel_mode=gtk.SELECTION_MULTIPLE, reset=True)
        tv.set_model(model)

        # Add Atom name, default z, calculated z and #:
        def add_text_col(title, colnr, is_float=True, editable=True):
            tv.append_column(new_text_column(
                title,
                data_func=create_float_data_func() if is_float else None,
                editable=editable,
                edited_callback=(self.on_item_cell_edited, (model, colnr)) if editable else None,
                resizable=False,
                text_col=colnr))
        add_text_col('Atom name', model.c_name, is_float=False)
        add_text_col('Def. Z (nm)', model.c_default_z)
        add_text_col('Calc. Z (nm)', model.c_z, editable=False)
        add_text_col('#', model.c_pn)

        # Add atom type column (combo box with atom types from pyxrd.project level):
        def atom_type_renderer(column, cell, model, itr, col=None):
            try:
                name = model.get_user_data_from_path(model.get_path(itr)).atom_type.name
            except:
                name = '#NA#'
            cell.set_property('text', name)
            return
        def adjust_combo(cell, editable, path, data=None):
            editable.set_wrap_width(10)
        atom_model = self.model.parent.parent.atom_types
        tv.append_column(new_combo_column(
            "Element",
            data_func=(atom_type_renderer, (3,)),
            changed_callback=self.on_atom_type_changed,
            edited_callback=(self.on_atom_type_edited, (model,)),
            editing_started_callback=adjust_combo,
            model=atom_model,
            text_column=atom_model.c_name,
            editable=True,
            has_entry=True))

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def create_new_object_proxy(self):
        return Atom("New Atom", parent=self.model, stretch_values=self.stretch_values)

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_export_item(self, widget, user_data=None):
        def on_accept(save_dialog):
            filename = self.extract_filename(save_dialog, self.file_filters)
            Atom.save_as_csv(filename, self.get_all_objects())
        self.run_save_dialog(
            "Export atoms", on_accept, parent=self.view.get_toplevel(),
             suggest_name="%s%s" % (self.model.name.lower(),
             self.model_property_name.replace("data", "").lower())
         )

    def on_import_item(self, widget, user_data=None):
        def import_layer(dialog):
            def on_accept(open_dialog):
                filename = self.extract_filename(open_dialog, self.file_filters)
                self.liststore.clear()
                Atom.get_from_csv(filename, self.liststore.append, self.model)
            self.run_load_dialog("Import atoms", on_accept, parent=self.view.get_toplevel())
        self.run_confirmation_dialog(
            message="Are you sure?\nImporting a layer file will clear the current list of atoms!",
             on_accept_callback=import_layer, parent=self.view.get_toplevel()
         )

    def on_atom_type_changed(self, combo, path, new_iter, user_data=None):
        """Called when the user selects an AtomType from the combo box"""
        self.new_atom_type = self.model.phase.project.atom_types.get_user_data(new_iter)
        return True

    def on_atom_type_edited(self, combo, path, new_text, user_data=None):
        """Called when the user has closed the AtomType combo box 
        (so after the on_atom_type_changed call)"""
        atom = self.liststore.get_user_data_from_path((int(path),))
        if atom is not None:
            # If new_atom_type is not set, but the user has typed in the name
            # of an atom_type, find it (index search):
            if self.new_atom_type is None and not new_text in (None, ""):
                try:
                    self.new_atom_type = self.model.phase.project.atom_types.get_item_by_index(new_text)
                except:
                    pass
            # Set the new atom type if it is not None:
            if self.new_atom_type is not None:
                atom.atom_type = self.new_atom_type
            # Clear variable and leave
            self.new_atom_type = None
            return True
        return False

    pass # end of class
