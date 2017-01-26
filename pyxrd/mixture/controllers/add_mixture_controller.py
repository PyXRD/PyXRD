# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk
import logging
logger = logging.getLogger(__name__)

from pyxrd.generic.controllers import DialogController

class AddMixtureController(DialogController):
    """ 
        Controller for the add mixture dialog
    """

    auto_adapt = False

    def __init__(self, model=None, view=None, parent=None, callback=None):
        super(AddMixtureController, self).__init__(
            model=model, view=view, parent=parent)
        self.callback = callback

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.view.hide()
        self.callback(self.view.get_mixture_type())
        return True

    def on_rdb_toggled(self, widget):
        self.view.update_sensitivities()

    def on_keypress(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.view.hide()
            return True
        if event.keyval == gtk.keysyms.Return:
            return self.on_btn_ok_clicked(event)

    def on_window_edit_dialog_delete_event(self, event, args=None):
        self.view.hide()
        return True # do not propagate

    pass # end of class