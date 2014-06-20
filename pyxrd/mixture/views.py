# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename  # @UnresolvedImport

import gtk

from math import isnan
import numpy as np

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvasGTK, NavigationToolbar2GTKAgg as NavigationToolbar

from pyxrd.generic.views import BaseView, DialogView
from pyxrd.generic.views.widgets import ThreadedTaskBox
from pyxrd.generic.views.validators import FloatEntryValidator
from pyxrd.generic.utils import not_none

class RefinementView(DialogView):
    title = "Refine Phase Parameters"
    subview_builder = resource_filename(__name__, "glade/refinement.glade")
    subview_toplevel = "refine_params"
    modal = True

    refine_status_builder = resource_filename(__name__, "glade/refine_status.glade")
    refine_status_toplevel = "tbl_refine_info"
    refine_status_container = "refine_status_box"

    refine_spin_container = "refine_spin_box"
    refine_spin_box = None

    refine_method_builder = resource_filename(__name__, "glade/refine_method.glade")
    refine_method_toplevel = "tbl_refine_method"
    refine_method_container = "refine_method_box"

    def __init__(self, *args, **kwargs):
        super(RefinementView, self).__init__(*args, **kwargs)
        self._builder.add_from_file(self.refine_status_builder)
        self._add_child_view(self[self.refine_status_toplevel], self[self.refine_status_container])
        self._builder.add_from_file(self.refine_method_builder)
        self._add_child_view(self[self.refine_method_toplevel], self[self.refine_method_container])
        self.hide_refinement_info()

    def show_refinement_info(self, refine_function, gui_callback, complete_callback, cancel_callback=None):

        self.complete_callback = complete_callback
        self.cancel_callback = cancel_callback

        self["hbox_actions"].set_sensitive(False)
        self["btn_auto_restrict"].set_sensitive(False)
        self[self.refine_method_toplevel].set_sensitive(False)
        self["refinables"].set_visible(False)
        self["refinables"].set_no_show_all(True)

        if self.refine_spin_box is not None:
            self.refine_spin_box.cancel()
        self.refine_spin_box = ThreadedTaskBox(refine_function, gui_callback, cancelable=True)
        self.refine_spin_box.connect("complete", self.complete_function)
        self.refine_spin_box.connect("cancelrequested", self.canceled_function)

        self._add_child_view(self.refine_spin_box, self[self.refine_spin_container])
        self.refine_spin_box.set_no_show_all(False)
        self.refine_spin_box.set_visible(True)
        self.refine_spin_box.show_all()
        self[self.refine_status_toplevel].show_all()

        self.refine_spin_box.start("Refining")

    def hide_refinement_info(self):
        self[self.refine_status_toplevel].hide()
        if self.refine_spin_box is not None:
            self.refine_spin_box.set_no_show_all(True)
            self.refine_spin_box.cancel()
        self["hbox_actions"].set_sensitive(True)
        self["btn_auto_restrict"].set_sensitive(True)
        self[self.refine_method_toplevel].set_sensitive(True)
        self["refinables"].set_visible(True)
        self["refinables"].set_no_show_all(False)

    def update_refinement_info(self, current_rp=None, message=None):
        if not isnan(current_rp):
            self["current_residual"].set_text("%.2f" % current_rp)
        self["message"].set_text(not_none(message, ""))

    def complete_function(self, widget, data=None):
        self.refine_spin_box.set_status("Processing...")
        if callable(self.complete_callback):
            self.complete_callback(data)
        self.hide_refinement_info()

    def canceled_function(self, widget, data=None):
        self.refine_spin_box.set_status("Cancelling...")
        if callable(self.cancel_callback):
            self.cancel_callback(data)
        self.hide_refinement_info()

    pass # end of class

class RefinementResultView(BaseView):
    builder = resource_filename(__name__, "glade/refine_results.glade")
    top = "window_refine_results"
    modal = True

    graph_parent = "plot_box"

    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)

        self.graph_parent = self[self.graph_parent]

        self.get_toplevel().set_transient_for(self.parent.get_toplevel())

        self.setup_matplotlib_widget()

    def setup_matplotlib_widget(self):
        # TODO Create a mixin for this kind of thing!!
        style = gtk.Style()
        self.figure = Figure(dpi=72, edgecolor=str(style.bg[2]), facecolor=str(style.bg[2]))

        self.figure.subplots_adjust(bottom=0.20)

        self.canvas = FigureCanvasGTK(self.figure)

        box = gtk.VBox()
        box.pack_start(NavigationToolbar(self.canvas, self.get_top_widget()), expand=False)
        box.pack_start(self.canvas)
        self.graph_parent.add(box)
        self.graph_parent.show_all()

        cdict = {'red': ((0.0, 0.0, 0.0),
                         (0.5, 1.0, 1.0),
                         (1.0, 0.0, 0.0)),
                'green': ((0.0, 0.0, 0.0),
                         (0.5, 1.0, 1.0),
                         (1.0, 0.0, 0.0)),
                'blue': ((0.0, 0.0, 0.0),
                         (0.5, 1.0, 1.0),
                         (1.0, 0.0, 0.0))}
        self.wbw_cmap = matplotlib.colors.LinearSegmentedColormap('WBW', cdict, 256)

    pass # end of class


class EditMixtureView(BaseView):
    builder = resource_filename(__name__, "glade/edit_mixture.glade")
    top = "edit_mixture"

    base_width = 4
    base_height = 5

    matrix_widget = "tbl_matrix"
    wrapper_widget = "tbl_wrapper"
    widget_format = "mixture_%s"

    def __init__(self, *args, **kwargs):
        BaseView.__init__(self, *args, **kwargs)

        self.parent.set_title("Edit Mixtures")
        self.matrix = self[self.matrix_widget]
        self.wrapper = self[self.wrapper_widget]

        self.labels = [ self["lbl_scales"], self["lbl_fractions"], self["lbl_phases"], self["lbl_bgshifts"], self["lbl_specimens"] ]

        self["scolled_window"].set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
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
        if isinstance(self[self.edit_view_container], gtk.ScrolledWindow):
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

    def add_phase_slot(self, phase_store, del_phase_callback, label_callback, fraction_callback, combo_callback, label, fraction, phases):
        r, c = self.matrix.get_property('n_rows'), self.matrix.get_property('n_columns')
        self.matrix.resize(r + 1, c)

        del_icon = gtk.Image()
        del_icon.set_from_stock ("192-circle-remove", gtk.ICON_SIZE_SMALL_TOOLBAR)
        new_phase_del_btn = gtk.Button()
        new_phase_del_btn.set_image(del_icon)
        rid = new_phase_del_btn.connect("clicked", del_phase_callback)
        new_phase_del_btn.set_data("deleventid", rid)
        self.matrix.attach(new_phase_del_btn, 0, 1, r, r + 1, gtk.FILL, 0)

        new_phase_input = self._get_new_input(label, callback=label_callback)
        self.phase_inputs.append(new_phase_input)
        self.matrix.attach(new_phase_input, 1, 2, r, r + 1, gtk.EXPAND | gtk.FILL, 0)

        new_fraction_input = self._get_new_input(str(fraction), callback=fraction_callback)
        FloatEntryValidator(new_fraction_input)
        self.fraction_inputs.append(new_fraction_input)
        self.matrix.attach(new_fraction_input, 2, 3, r, r + 1, gtk.EXPAND | gtk.FILL, 0)

        self.phase_combos.resize((c - self.base_width, r + 1 - self.base_height))
        for col in range(c - self.base_width):
            mcol, mrow = r - self.base_height, col
            self._add_new_phase_combo(phase_store, phase_store.c_name, phases[mrow, mcol], mrow, mcol, combo_callback)

        self.wrapper.show_all()

    def add_specimen_slot(self, phase_store, specimen_store, del_specimen_callback, scale_callback, bgs_callback, specimen_callback, combo_callback, scale, bgs, specimen, phases):
        r, c = self.matrix.get_property('n_rows'), self.matrix.get_property('n_columns')
        self.matrix.resize(r, c + 1)

        del_icon = gtk.Image()
        del_icon.set_from_stock("192-circle-remove", gtk.ICON_SIZE_SMALL_TOOLBAR)
        new_specimen_del_btn = gtk.Button()
        new_specimen_del_btn.set_image(del_icon)
        rid = new_specimen_del_btn.connect("clicked", del_specimen_callback)
        new_specimen_del_btn.set_data("deleventid", rid)
        self.matrix.attach(new_specimen_del_btn, c, c + 1, 0, 1, gtk.EXPAND | gtk.FILL, 0)

        new_specimen_combo = self._get_new_combo(specimen_store, specimen_store.c_name, default=specimen, callback=specimen_callback)
        self.specimen_combos.append(new_specimen_combo)
        self.matrix.attach(new_specimen_combo, c, c + 1, 1, 2, gtk.EXPAND | gtk.FILL, 0)

        new_bgs_input = self._get_new_input(str(bgs), callback=bgs_callback)
        FloatEntryValidator(new_bgs_input)
        self.bgs_inputs.append(new_bgs_input)
        self.matrix.attach(new_bgs_input, c, c + 1, 2, 3, gtk.EXPAND | gtk.FILL, 0)

        new_scale_input = self._get_new_input(str(scale), callback=scale_callback)
        FloatEntryValidator(new_scale_input)
        self.scale_inputs.append(new_scale_input)
        self.matrix.attach(new_scale_input, c, c + 1, 3, 4, gtk.EXPAND | gtk.FILL, 0)

        self.phase_combos.resize((c + 1 - self.base_width, r - self.base_height))
        for row in range(r - self.base_height):
            mcol, mrow = row, c - self.base_width
            self._add_new_phase_combo(phase_store, phase_store.c_name, phases[mrow, mcol], mrow, mcol, combo_callback)
        self.wrapper.show_all()

    def _get_new_input(self, text="", width=7, callback=None):
        """
            Creates a new text input box.
        """
        new_input = gtk.Entry()
        new_input.set_text(text)
        new_input.set_alignment(0.0)
        new_input.set_width_chars(width)
        if callback is not None: new_input.connect("changed", callback)
        return new_input

    def _add_new_phase_combo(self, model, text_column, default, r, c, callback):
        """
            Creates a new 'phase slot' combo box, and adds it to the table at
            the given row and column indices.
        """
        new_phase_combo = self._get_new_combo(model, text_column, default, callback, r, c)
        self.phase_combos[r, c] = new_phase_combo
        self.matrix.attach(new_phase_combo, self.base_width + r, self.base_width + r + 1, self.base_height + c, self.base_height + c + 1, gtk.EXPAND | gtk.FILL, 0)

    def _get_new_combo(self, model, text_column, default, callback, *args):
        """
            Creates a new combo box with the given model as ListStore, setting
            the given column as text column, the given default value set as 
            active row, and connecting the given callback with 'changed' signal.
        """
        combobox = gtk.ComboBox(model)
        combobox.set_size_request(75, -1)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell) # , False)
        combobox.add_attribute(cell, 'text', text_column)
        if default is not None:
            index = model.on_get_path(default)[0]
            combobox.set_active(index)
        combobox.connect("changed", callback, *args)
        return combobox

    pass # end of class
