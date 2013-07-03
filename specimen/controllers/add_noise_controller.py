# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from generic.controllers import DialogController
from generic.views.validators import FloatEntryValidator

#
# TODO Generalize this kind of controller (e.g. apply function etc.)
#

class AddNoiseController(DialogController):

    def register_adapters(self):
        if self.model is not None:
            FloatEntryValidator(self.view["noise_fraction"])
            self.adapt("noise_fraction")
        return
            
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.model.add_noise()
        self.view.hide()
        return True
            
    def on_cancel(self):
        self.model.noise_fraction = 0.0
        DialogController.on_cancel(self)
            
    pass #end of class
