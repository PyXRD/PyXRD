# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

from pyxrd.generic.controllers.base_controller import BaseController

class DialogController(BaseController):
    """
        Simple controller which has a DialogView subclass instance as view.
    """

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.on_cancel()
        return True

    def on_keypress(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.on_cancel()
            return True

    def on_window_edit_dialog_delete_event(self, event, args=None):
        self.on_cancel()
        return True # do not propagate

    def on_cancel(self):
        self.view.hide()

    pass #end of class