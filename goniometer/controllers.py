# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import locale

import gtk

from gtkmvc import Controller

import settings

from generic.utils import create_treestore_from_directory, create_valuestore_from_file, get_case_insensitive_glob
from generic.views.validators import FloatEntryValidator
from generic.controllers import DialogController, DialogMixin

class GoniometerController(DialogController, DialogMixin):

    file_filters = [("Goniometer files", get_case_insensitive_glob("*.GON")),
                    ("All Files", "*.*")]

    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name in ("radius", "divergence", "soller1", 
                        "wavelength", "soller2", "min_2theta", "max_2theta", 
                        "ads_factor", "ads_phase_fact",
                        "ads_phase_shift", "ads_const"):
                    FloatEntryValidator(self.view["gonio_%s" % name])
                    self.adapt(name)                   
                elif name=="steps":
                    self.adapt(name, "gonio_%s" % name)
                elif not name in self.model.__have_no_widget__:
                    self.adapt(name)
        
    def __init__(self, *args, **kwargs):
        DialogController.__init__(self, *args, **kwargs)
            
    def register_view(self, view):
        self.generate_import_combo()
        self.generate_wavelength_combo()

    def generate_import_combo(self):
        self.view.import_combo_box.clear()
        cmb_model = create_treestore_from_directory(settings.get_def_dir("DEFAULT_GONIOS"), ".gon")
        self.view.import_combo_box.set_model(cmb_model)
        cell = gtk.CellRendererText()
        self.view.import_combo_box.pack_start(cell, True)
        self.view.import_combo_box.add_attribute(cell, 'text', 0)
        self.view.import_combo_box.add_attribute(cell, 'sensitive', 2)

    def generate_wavelength_combo(self):
        self.view.wavelength_combo_box.clear()
        cmb_model = create_valuestore_from_file(settings.get_def_file("WAVELENGTHS"))
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
                             parent=self.view.get_top_widget())
    
    def on_cmb_import_gonio_changed(self, combobox, *args):    
        model = combobox.get_model()
        itr = combobox.get_active_iter()
        if itr:
            path = model.get_value(itr, 1)
            if path:
                def on_accept(dialog):
                    self.model.reset_from_file(path)
                self.run_confirmation_dialog("Are you sure?\nYou will loose the current settings!", on_accept, parent=self.view.get_toplevel())
        combobox.set_active(-1) #deselect
        
    def on_cmb_wavelength_changed(self, combobox, *args):    
        model = combobox.get_model()
        itr = combobox.get_active_iter()
        if itr:
            self.wavelength = float(model.get_value(itr, 1))
    pass # end of class
