# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk as gdk

import logging
logger = logging.getLogger(__name__)

from pyxrd.generic.views.combobox_tools import add_combo_text_column

from pyxrd.generic.controllers import DialogController

class AddInSituBehaviourController(DialogController):
    """ 
        Controller for the add InSituBehaviour dialog
    """

    auto_adapt = False

    def __init__(self, model=None, view=None, parent=None, callback=None):
        super(AddInSituBehaviourController, self).__init__(
            model=model, view=view, parent=parent)
        self.callback = callback

    def generate_combo(self):
        cmb_model = Gtk.ListStore(str, object)
        print("Adding rows from:", self.parent.obj_type_map)
        for cls, _, _ in self.parent.obj_type_map:
            print("Adding row:", cls)
            cmb_model.append([cls.Meta.store_id, cls])
        self.view.behaviour_combo_box.set_model(cmb_model)
        add_combo_text_column(
            self.view.behaviour_combo_box, text_col=0)

    def register_view(self, view):
        self.generate_combo()

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.view.hide()
        self.callback(self.view.get_behaviour_type())
        return True

    def on_keypress(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.view.hide()
            return True
        if event.keyval == Gdk.KEY_Return:
            return self.on_btn_ok_clicked(event)

    def on_window_edit_dialog_delete_event(self, event, args=None):
        self.view.hide()
        return True # do not propagate

    pass # end of class