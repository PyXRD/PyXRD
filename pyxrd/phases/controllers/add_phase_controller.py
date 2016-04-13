# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk
import logging
logger = logging.getLogger(__name__)

from mvc.adapters.gtk_support.treemodels.utils import create_treestore_from_directory

from pyxrd.data import settings

from pyxrd.generic.views.combobox_tools import add_combo_text_column
from pyxrd.generic.controllers import DialogController

from pyxrd.probabilities.models import get_Gbounds_for_R, get_Rbounds_for_G

class AddPhaseController(DialogController):
    """ 
        Controller for the add phase dialog
    """

    auto_adapt = False

    def __init__(self, model=None, view=None, parent=None, callback=None):
        super(AddPhaseController, self).__init__(
            model=model, view=view, parent=parent)
        self.callback = callback

    def register_view(self, view):
        self.update_bounds()
        self.generate_combo()

    def register_adapters(self):
        pass # has no intel, or a model!

    def update_R_bounds(self):
        if self.view is not None:
            min_R, max_R, R = get_Rbounds_for_G(
                self.view.get_G(), self.view.get_R())
            self.view["adj_R"].set_upper(max_R)
            self.view["adj_R"].set_lower(min_R)
            self.view["R"].set_value(R)

    def update_G_bounds(self):
        if self.view is not None:
            min_G, max_G, G = get_Gbounds_for_R(
                self.view.get_R(), self.view.get_G())
            self.view["adj_G"].set_upper(max_G)
            self.view["adj_G"].set_lower(min_G)
            self.view["G"].set_value(G)

    def update_bounds(self):
        self.update_G_bounds()
        self.update_R_bounds()

    def generate_combo(self):
        self.reload_combo_model()
        add_combo_text_column(
            self.view.phase_combo_box, text_col=0, sensitive_col=2)

    def reload_combo_model(self):
        cmb_model = create_treestore_from_directory(
            settings.DATA_REG.get_directory_path("DEFAULT_PHASES"))
        self.view.phase_combo_box.set_model(cmb_model)

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.view.hide()
        self.callback(
            self.view.get_phase_type(), self.view.get_G(), self.view.get_R())
        return True

    def on_rdb_toggled(self, widget):
        self.view.update_sensitivities()

    def on_btn_generate_phases_clicked(self, event):
        from pyxrd.scripts.generate_default_phases import run
        def ui_callback(progress):
            self.view["gen_progress_bar"].set_fraction(progress)
            while gtk.events_pending():
                gtk.main_iteration()
        self.view["img_repeat"].set_visible(False)
        self.view["gen_spinner"].start()
        self.view["gen_spinner"].set_visible(True)
        self.view["gen_progress_bar"].set_visible(True)
        while gtk.events_pending():
            gtk.main_iteration()
        run(ui_callback=ui_callback)
        self.view["gen_progress_bar"].set_visible(False)
        self.view["img_repeat"].set_visible(True)
        self.view["gen_spinner"].stop()
        self.view["gen_spinner"].set_visible(False)
        self.reload_combo_model()
        return True

    def on_r_value_changed(self, *args):
        self.update_G_bounds()
        return True

    def on_g_value_changed(self, *args):
        self.update_R_bounds()
        return True

    def on_keypress(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.view.hide()
            return True
        if event.keyval == gtk.keysyms.Return:
            self.view.hide()
            self.callback(
                self.view.get_phase_type(), self.view.get_G(), self.view.get_R())
            return True

    def on_window_edit_dialog_delete_event(self, event, args=None):
        self.view.hide()
        return True # do not propagate

    pass # end of class