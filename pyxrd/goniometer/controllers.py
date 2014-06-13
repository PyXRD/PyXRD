# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

from pyxrd.generic.controllers import BaseController
from pyxrd.goniometer.models import Goniometer
from pyxrd.mvc.adapters.gtk_support.treemodels.utils import (
    create_treestore_from_directory, create_valuestore_from_file)

class InlineGoniometerController(BaseController):
    """
        Goniometer controller. Is not expected to be used with a dialog view,
        but rather in another view. 
    """

    file_filters = Goniometer.Meta.file_filters + [("All Files", "*.*"), ]

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def register_view(self, view):
        self.generate_import_combo()
        self.generate_wavelength_combo()

    def generate_import_combo(self):
        # TODO seperate this more the gtk level...
        self.view.import_combo_box.clear()
        path, ext = Goniometer.get_default_goniometers_path()
        cmb_model = create_treestore_from_directory(path, ext)
        self.view.import_combo_box.set_model(cmb_model)
        cell = gtk.CellRendererText()
        self.view.import_combo_box.pack_start(cell, True)
        self.view.import_combo_box.add_attribute(cell, 'text', 0)
        self.view.import_combo_box.add_attribute(cell, 'sensitive', 2)

    def generate_wavelength_combo(self):
        # TODO seperate this more the gtk level...
        self.view.wavelength_combo_box.clear()
        path = Goniometer.get_default_wavelengths_path()
        cmb_model = create_valuestore_from_file(path)
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
            self.model.save_object(filename)
            self.generate_import_combo()
        suggest_folder, _ = Goniometer.get_default_goniometers_path()
        self.run_save_dialog(title="Select the goniometer setup file to save to",
                             on_accept_callback=on_accept,
                             suggest_folder=suggest_folder,
                             parent=self.view.parent.get_top_widget())

    def on_cmb_import_gonio_changed(self, combobox, *args):
        model = combobox.get_model()
        itr = combobox.get_active_iter()
        if itr:
            # first column is the name, second column the path and third column
            # a flag indicating if this can be selected
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
