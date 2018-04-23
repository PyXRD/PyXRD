# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename  # @UnresolvedImport

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import numpy as np

from pyxrd.generic.views import BaseView
from pyxrd.generic.views.validators import FloatEntryValidator

class EditInSituMixtureView(BaseView):   
    builder = resource_filename(__name__, "glade/edit_mixture.glade")
    top = "edit_mixture"

    base_width = 4
    base_height = 5

    matrix_widget = "tbl_matrix"
    wrapper_widget = "tbl_wrapper"
    widget_format = "mixture_%s"

    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)

        self.parent.set_title("Edit In Situ Mixtures")
        self.matrix = self[self.matrix_widget]
        self.wrapper = self[self.wrapper_widget]

        self.labels = [ self["lbl_scales"], self["lbl_fractions"], self["lbl_phases"], self["lbl_bgshifts"], self["lbl_specimens"] ]

        self["scolled_window"].set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.matrix.connect("size-request", self.on_size_requested)

        self.reset_view()

    def reset_view(self):
        def remove(item):
            if not item in self.labels: self.matrix.remove(item)
        self.matrix.foreach(remove)
        self.matrix.resize(self.base_height, self.base_width)

        self.phase_inputs = []
        self.fraction_inputs = []
        self.specimen_combos = []
        self.scale_inputs = []
        self.bgs_inputs = []
        self.phase_combos = np.empty(shape=(0, 0), dtype=np.object_) # 2D list
        self.behav_combos = np.empty(shape=(0, 0), dtype=np.object_) # 2D list

        self.on_size_requested()

    def on_size_requested(self, *args):
        sr = self.matrix.size_request()
        self[self.top].set_size_request(sr[0] + 100, -1)

    def set_edit_view(self, view):
        if self._on_sr_id is not None and self.child_view is not None:
            self.child_view.disconnect(self._on_sr_id)
        self.edit_view = view
        self.child_view = view.get_top_widget()
        self._add_child_view(self.child_view, self[self.edit_view_container])
        if isinstance(self[self.edit_view_container], Gtk.ScrolledWindow):
            sr = self.child_view.get_size_request()
            self[self.edit_view_container].set_size_request(sr[0], -1)

    def update_all(self, fractions, scales, bgs):
        for i, fraction in enumerate(fractions):
            if not i >= len(self.fraction_inputs):
                self.fraction_inputs[i].set_text(str(fraction))
        for i, scale in enumerate(scales):
            if not i >= len(self.scale_inputs):
                self.scale_inputs[i].set_text(str(scale))
        for i, bgs in enumerate(bgs):
            if not i >= len(self.bgs_inputs):
                self.bgs_inputs[i].set_text(str(bgs))

    def add_phase_slot(self, 
           phase_store, behav_store, 
           del_phase_callback, label_callback, fraction_callback, 
           phase_visible_callback, phase_combo_callback,
           behav_visible_callback, behav_combo_callback, 
           label, fraction,
           phases, behavs):
        r, c = self.matrix.get_property('n_rows'), self.matrix.get_property('n_columns')
        self.matrix.resize(r + 1, c)

        del_icon = Gtk.Image()
        del_icon.set_from_stock ("192-circle-remove", Gtk.IconSize.SMALL_TOOLBAR)
        new_phase_del_btn = Gtk.Button()
        new_phase_del_btn.set_image(del_icon)
        rid = new_phase_del_btn.connect("clicked", del_phase_callback)
        setattr(new_phase_del_btn, "deleventid", rid)
        self.matrix.attach(new_phase_del_btn, 0, 1, r, r + 1, Gtk.AttachOptions.FILL, 0)

        new_phase_input = self._get_new_input(label, callback=label_callback)
        self.phase_inputs.append(new_phase_input)
        self.matrix.attach(new_phase_input, 1, 2, r, r + 1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0)

        new_fraction_input = self._get_new_input(str(fraction), callback=fraction_callback)
        FloatEntryValidator(new_fraction_input)
        self.fraction_inputs.append(new_fraction_input)
        self.matrix.attach(new_fraction_input, 2, 3, r, r + 1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0)

        self.phase_combos.resize((c - self.base_width, r + 1 - self.base_height))
        self.behav_combos.resize((c - self.base_width, r + 1 - self.base_height))
        for col in range(c - self.base_width):
            mcol, mrow = r - self.base_height, col
            self._add_new_phase_behav_combo(
                mrow, mcol,
                phase_store, phase_store.c_name, phases[mrow, mcol], phase_visible_callback, phase_combo_callback,
                behav_store, behav_store.c_name, behavs[mrow, mcol], behav_visible_callback, behav_combo_callback
            )

        self.wrapper.show_all()

    def add_specimen_slot(self,
            phase_store, behav_store, specimen_store, 
            del_specimen_callback, scale_callback, bgs_callback, specimen_callback, 
            phase_visible_callback, phase_combo_callback,
            behav_visible_callback, behav_combo_callback, 
            scale, bgs, specimen, 
            phases, behavs):
        r, c = self.matrix.get_property('n_rows'), self.matrix.get_property('n_columns')
        self.matrix.resize(r, c + 1)

        del_icon = Gtk.Image()
        del_icon.set_from_stock("192-circle-remove", Gtk.IconSize.SMALL_TOOLBAR)
        new_specimen_del_btn = Gtk.Button()
        new_specimen_del_btn.set_image(del_icon)
        rid = new_specimen_del_btn.connect("clicked", del_specimen_callback)
        setattr(new_specimen_del_btn, "deleventid", rid)
        self.matrix.attach(new_specimen_del_btn, c, c + 1, 0, 1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0)

        new_specimen_combo = self._get_new_combo(specimen_store, specimen_store.c_name, specimen, None, specimen_callback)
        self.specimen_combos.append(new_specimen_combo)
        self.matrix.attach(new_specimen_combo, c, c + 1, 1, 2, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0)

        new_bgs_input = self._get_new_input(str(bgs), callback=bgs_callback)
        FloatEntryValidator(new_bgs_input)
        self.bgs_inputs.append(new_bgs_input)
        self.matrix.attach(new_bgs_input, c, c + 1, 2, 3, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0)

        new_scale_input = self._get_new_input(str(scale), callback=scale_callback)
        FloatEntryValidator(new_scale_input)
        self.scale_inputs.append(new_scale_input)
        self.matrix.attach(new_scale_input, c, c + 1, 3, 4, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0)

        self.phase_combos.resize((c + 1 - self.base_width, r - self.base_height))
        self.behav_combos.resize((c + 1 - self.base_width, r - self.base_height))
        for row in range(r - self.base_height):
            mcol, mrow = row, c - self.base_width
            self._add_new_phase_behav_combo(
                mrow, mcol,
                phase_store, phase_store.c_name, phases[mrow, mcol], phase_visible_callback, phase_combo_callback,
                behav_store, behav_store.c_name, behavs[mrow, mcol], behav_visible_callback, behav_combo_callback
            )
            
        self.wrapper.show_all()

    def _get_new_input(self, text="", width=7, callback=None):
        """
            Creates a new text input box.
        """
        new_input = Gtk.Entry()
        new_input.set_text(text)
        new_input.set_alignment(0.0)
        new_input.set_width_chars(width)
        if callback is not None: new_input.connect("changed", callback)
        return new_input

    def _add_new_phase_behav_combo(self, 
            r, c,
            phase_model, phase_text_column, default_phase, phase_visible_callback, phase_callback,
            behav_model, behav_text_column, default_behav, behav_visible_callback, behav_callback):
        """
            Creates new 'phase' and 'behaviour' combo boxes, and adds them to the table at
            the given row and column indices.
        """
        new_phase_combo = self._get_new_combo(phase_model, phase_text_column, default_phase, phase_visible_callback, phase_callback, r, c)
        self.phase_combos[r, c] = new_phase_combo
        
        new_behav_combo = self._get_new_combo(behav_model, behav_text_column, default_behav, behav_visible_callback, behav_callback, r, c)
        self.behav_combos[r, c] = new_behav_combo

        box = Gtk.HBox(spacing = 5)
        box.pack_start(new_phase_combo, True, True, padding = 2)
        box.pack_end(new_behav_combo, True, True, padding = 2)
       
        self.matrix.attach(box, self.base_width + r, self.base_width + r + 1, self.base_height + c, self.base_height + c + 1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0)

    def _get_new_combo(self, model, text_column, default, visible_callback, callback, *args):
        """
            Creates a new combo box with the given model as ListStore, setting
            the given column as text column, the given default value set as 
            active row, and connecting the given callback with 'changed' signal.
        """
        combobox = Gtk.ComboBox(model)
        combobox.set_size_request(75, -1)
        cell = Gtk.CellRendererText()
        combobox.pack_start(cell, True)

        def combo_func(cmb, cell, model, itr, args):
            text = model.get_value(itr, text_column)
            cell.set_property('text', text)
            if callable(visible_callback):
                cell.set_property('sensitive', visible_callback(model, itr, args))
        combobox.set_cell_data_func(cell, combo_func, args)       
            
        if default is not None:
            index = model.on_get_path(default)[0]
            combobox.set_active(index)
        combobox.connect("changed", callback, *args)
        return combobox

    pass # end of class
