# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import locale

import gtk

from math import pi
import numpy as np

from gtkmvc import Controller
from gtkmvc.adapters import Adapter

from generic.validators import FloatEntryValidator
from generic.controllers import BaseController, ObjectListStoreController

from atoms.models import AtomType
from atoms.views import EditAtomTypeView

class EditAtomTypeController(BaseController):

    def register_adapters(self):
        print "EditAtomTypeController.register_adapters()"
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "name":
                    ad = Adapter(self.model, "name")
                    ad.connect_widget(self.view["atom_name"])
                    self.adapt(ad)
                elif name in ("atom_nr", "debye", "weight", "par_a1", "par_a2", "par_a3", "par_a4", "par_a5", "par_b1", "par_b2", "par_b3", "par_b4", "par_b5", "par_c"):
                    FloatEntryValidator(self.view["atom_%s" % name])
                    self.adapt(name)                
                elif not name in ("parameters_changed", "atom_nr", "parent", "added", "removed"):
                    self.adapt(name)
            self.update_plot()
            return

    def update_plot(self):
        x, y = (),()
        if self.model is not None:
            x = np.arange(0,90.0,90.0/100.0)
            y = self.model.get_atomic_scattering_factors(2*np.sin(np.radians(x/2)) / self.model.project.goniometer.wavelength)
        self.view.update_figure(x, y)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("parameters_changed", signal=True)
    def notif_parameter_changed(self, model, prop_name, info):
        self.update_plot()


    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------


class AtomTypesController(ObjectListStoreController):
    file_filters = ("Single atom type file", "*.sat"), ("Atom types list file", "*.atl")
    model_property_name = "atom_types"
    columns = [ ("Atom type name", "c_name") ]
    delete_msg = "Deleting an atom type is irreverisble!\nAre You sure you want to continue?"
    title="Edit Atom Types"

    def get_new_edit_view(self, obj):
        if isinstance(obj, AtomType):
            return EditAtomTypeView(parent=self.view)
        else:
            return ObjectListStoreController.get_new_edit_view(self, obj)
        
    def get_new_edit_controller(self, obj, view, parent=None):
        if isinstance(obj, AtomType):
            return EditAtomTypeController(obj, view, parent=parent)
        else:
            return ObjectListStoreController.get_new_edit_controller(self, obj, view, parent=parent)

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
                AtomType.get_from_csv(open_dialog.get_filename(), save_append) #self.model.atom_types.append)
        self.run_load_dialog("Import atom types", on_accept, parent=self.view.get_top_widget())


    def on_save_object_clicked(self, event):
        def on_accept(save_dialog):
            print "Exporting atom types..."
            fltr = save_dialog.get_filter()
            filename = save_dialog.get_filename()
            if fltr.get_name() == self.file_filters[0][0]:
                if filename[len(filename)-4:] != self.file_filters[0][1][1:]:
                    filename = "%s%s" % (filename, self.file_filters[0][1][1:])
                atom_type = self.get_selected_object()
                if atom_type is not None:
                    atom_type.save_object(filename=filename)
            elif fltr.get_name() == self.file_filters[1][0]:
                if filename[len(filename)-4:] != self.file_filters[1][1][1:]:
                    filename = "%s%s" % (filename, self.file_filters[1][1][1:])
                AtomType.save_as_csv(filename, self.get_selected_objects())
        self.run_save_dialog("Export atom types", on_accept, parent=self.view.get_top_widget())
        
    def create_new_object_proxy(self):
        #new_atom_type = 
        #self.model.add_atom_type(new_atom_type)
        #self.select_object(new_atom_type)
        return AtomType("New Atom Type", parent=self.model)
        
    pass #end of class
        
