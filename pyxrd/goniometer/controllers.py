# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

from pyxrd.data import settings

from pyxrd.generic.models.treemodels.utils import create_valuestore_from_file, create_treestore_from_directory

from pyxrd.generic.controllers.utils import get_case_insensitive_glob
from pyxrd.generic.controllers import BaseController

class InlineGoniometerController(BaseController):
    """
        Goniometer controller. Is not expected to be used with a dialog view,
        but rather in another view. 
    """

    file_filters = [("Goniometer files", get_case_insensitive_glob("*.GON")),
                    ("All Files", "*.*")]

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def register_view(self, view):
        self.generate_import_combo()
        self.generate_wavelength_combo()

    def generate_import_combo(self):
        self.view.import_combo_box.clear()
        cmb_model = create_treestore_from_directory(
            settings.DATA_REG.get_directory_path("DEFAULT_GONIOS"),
            ".gon"
        )
        self.view.import_combo_box.set_model(cmb_model)
        cell = gtk.CellRendererText()
        self.view.import_combo_box.pack_start(cell, True)
        self.view.import_combo_box.add_attribute(cell, 'text', 0)
        self.view.import_combo_box.add_attribute(cell, 'sensitive', 2)

    def generate_wavelength_combo(self):
        self.view.wavelength_combo_box.clear()
        cmb_model = create_valuestore_from_file(
            settings.DATA_REG.get_file_path("WAVELENGTHS")
        )
        self.view.wavelength_combo_box.set_model(cmb_model)
        cell = gtk.CellRendererText()
        self.view.wavelength_combo_box.pack_start(cell, True)
        self.view.wavelength_combo_box.add_attribute(cell, 'text', 0)
        self.view.wavelength_combo_box.set_entry_text_column(1)

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_export_gonio_clicked(self, widget, *args):
        def on_accept(dialog):
            filename = self.extract_filename(dialog)
            self.model.save_object(filename=filename)
        self.run_save_dialog(title="Select the goniometer setup file to save to",
                             on_accept_callback=on_accept,
                             parent=self.view.parent.get_top_widget())

    def on_cmb_import_gonio_changed(self, combobox, *args):
        model = combobox.get_model()
        itr = combobox.get_active_iter()
        if itr:
            path = model.get_value(itr, 1)
            if path:
                def on_accept(dialog):
                    self.model.reset_from_file(path)
                self.run_confirmation_dialog("Are you sure?\nYou will loose the current settings!", on_accept, parent=self.view.get_toplevel())
        combobox.set_active(-1) # deselect

    def on_cmb_wavelength_changed(self, combobox, *args):
        model = combobox.get_model()
        itr = combobox.get_active_iter()
        if itr:
            self.wavelength = float(model.get_value(itr, 1))

    pass # end of class
