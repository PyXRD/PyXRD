# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from generic.controllers import DialogController
from generic.views.validators import FloatEntryValidator
from generic.controllers.utils import ctrl_setup_combo_with_list

from specimen.views import ShiftDataView

class ShiftDataController(DialogController):

    def register_adapters(self):
        if self.model is not None:
            self.model.find_shift_value()
            for name in self.model.get_properties():
                if name == "shift_position":
                    ctrl_setup_combo_with_list(self, 
                        self.view["cmb_shift_position"],
                        "shift_position", "_shift_positions")
                elif name == "shift_value":
                    FloatEntryValidator(self.view["shift_value"])
                    self.adapt(name)
            return
            
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.model.shift_data()
        self.view.hide()
        return True
            
    def on_cancel(self):
        self.model.shift_value = 0
        DialogController.on_cancel(self)
            
    pass #end of class
