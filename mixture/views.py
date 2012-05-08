# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.
import gtk

import numpy as np

from generic.views import BaseView, DialogView
from generic.validators import FloatEntryValidator

class BusyView(BaseView):
    builder = "mixture/glade/busy.glade"
    top = "busy_window"
    
    def set_R(self, value):
        self["lbl_R"].set_text("%.2f" % value)
        

class RefinementView(DialogView):
    title = "Refine Phase Parameters"
    subview_builder = "mixture/glade/refinement.glade"
    subview_toplevel = "refine_params"
    modal = True      

class EditMixtureView(BaseView): #TODO add delete buttons as well!
    builder = "mixture/glade/edit_mixture.glade"
    top = "edit_mixture"
    
    matrix_widget = "tbl_matrix"
    wrapper_widget = "tbl_wrapper"
        
    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)
        
        self.parent.set_title("Edit Mixtures")  
        self.matrix = self[self.matrix_widget]
        self.wrapper = self[self.wrapper_widget]
        
        self.labels = [ self["lbl_scales"], self["lbl_fractions"], self["lbl_phases"] ]
        
        self.reset_view()
        
    def reset_view(self):
        def remove(item):
            if not item in self.labels: self.matrix.remove(item)
        self.matrix.foreach(remove)
        self.matrix.resize(3,3)
        
        self.phase_inputs = []
        self.fraction_inputs = []
        self.specimen_combos = []
        self.scale_inputs = []
        self.phase_combos = np.empty(shape=(0,0), dtype=np.object_) #2D list
        
    def update_all(self, fractions, scales):
        for i, fraction in enumerate(fractions):
            self.fraction_inputs[i].set_text(str(fraction))
        for i, scale in enumerate(scales):
            self.scale_inputs[i].set_text(str(scale))
        
    def add_column(self, phase_store, del_phase_callback, label_callback, fraction_callback, combo_callback, label, fraction, phases):
        r,c = self.matrix.get_property('n_rows'), self.matrix.get_property('n_columns')
        self.matrix.resize(r, c+1)
        
        del_icon = gtk.Image()
        del_icon.set_from_stock (gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON)  
        new_phase_del_btn = gtk.Button()
        new_phase_del_btn.set_image(del_icon)
        rid = new_phase_del_btn.connect("clicked", del_phase_callback)
        new_phase_del_btn.set_data("deleventid", rid)
        self.matrix.attach(new_phase_del_btn, c, c+1, 0, 1, gtk.EXPAND|gtk.FILL, 0)
        
        new_phase_input = self.__get_new_input__(label, callback=label_callback)
        self.phase_inputs.append(new_phase_input)
        self.matrix.attach(new_phase_input, c, c+1, 1, 2, gtk.EXPAND|gtk.FILL, 0)

        new_fraction_input = self.__get_new_input__(str(fraction), callback=fraction_callback)
        FloatEntryValidator(new_fraction_input)
        self.fraction_inputs.append(new_fraction_input)
        self.matrix.attach(new_fraction_input, c, c+1, 2, 3, gtk.EXPAND|gtk.FILL, 0)
        
        self.phase_combos.resize((r-3,c-2))
        for row in range(r-3):
            self.__add_new_phase_combo__(phase_store, phase_store.c_data_name, phases[row, c-3], row, c-3, combo_callback)
        
        self.wrapper.show_all()
    
    def add_row(self, phase_store, specimen_store, del_specimen_callback, scale_callback, specimen_callback, combo_callback, scale, specimen, phases):
        r,c = self.matrix.get_property('n_rows'), self.matrix.get_property('n_columns')
        self.matrix.resize(r+1, c)

        del_icon = gtk.Image()
        del_icon.set_from_stock (gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON)        
        new_specimen_del_btn = gtk.Button()
        new_specimen_del_btn.set_image(del_icon)
        rid = new_specimen_del_btn.connect("clicked", del_specimen_callback)
        new_specimen_del_btn.set_data("deleventid", rid)
        self.matrix.attach(new_specimen_del_btn, 0, 1, r, r+1, gtk.EXPAND|gtk.FILL, 0)        
        
        new_scale_input = self.__get_new_input__(str(scale), callback=scale_callback)
        FloatEntryValidator(new_scale_input)
        self.scale_inputs.append(new_scale_input)
        self.matrix.attach(new_scale_input, 1, 2, r, r+1, gtk.EXPAND|gtk.FILL, 0)

        new_specimen_combo = self.__get_new_combo__(specimen_store, specimen_store.c_data_name, default=specimen, callback=specimen_callback)
        self.specimen_combos.append(new_specimen_combo)
        self.matrix.attach(new_specimen_combo, 2, 3, r, r+1, gtk.EXPAND|gtk.FILL, 0)
        
        self.phase_combos.resize((r-2,c-3))
        for col in range(c-3):
            self.__add_new_phase_combo__(phase_store, phase_store.c_data_name, phases[r-3, col], r-3, col, combo_callback)
            
        self.wrapper.show_all()

    def __get_new_input__(self, text="", width=4, callback=None):
        new_input = gtk.Entry()
        new_input.set_text(text)
        new_input.set_alignment(0.5)
        new_input.set_width_chars(width)
        if callback!=None: new_input.connect("changed", callback)
        return new_input
        
    def __add_new_phase_combo__(self, model, text_column, default, r, c, callback):
        new_phase_combo = self.__get_new_combo__(model, text_column, default, callback, r, c)        
        self.phase_combos[r, c] = new_phase_combo
        self.matrix.attach(new_phase_combo, c+3, c+4, r+3, r+4, gtk.EXPAND|gtk.FILL, 0)
        
    def __get_new_combo__(self, model, column, default, callback, *args):
        combobox = gtk.ComboBox(model)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell) #, False)
        combobox.add_attribute(cell, 'text', column)
        if default != None:
            combobox.set_active(model.index(default))
        combobox.connect("changed", callback, *args)
        return combobox
        
    pass #end of class
