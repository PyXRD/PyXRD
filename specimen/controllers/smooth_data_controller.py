# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from generic.controllers import DialogController
from generic.views.validators import FloatEntryValidator
from generic.controllers.utils import ctrl_setup_combo_with_list

from specimen.views import SmoothDataView

#
# TODO Generalize this kind of controller (e.g. apply function etc.)
#

class SmoothDataController(DialogController):

    def register_adapters(self):
        if self.model is not None:
            self.model.sd_degree = 5
            for name in self.model.get_properties():
                if name == "smooth_type":
                    ctrl_setup_combo_with_list(self, 
                        self.view["cmb_smooth_type"],
                        "smooth_type", "_smooth_types")
                elif name == "smooth_degree":
                    #FloatEntryValidator(self.view["smooth_degree"])
                    self.adapt(name)
            return
            
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.model.smooth_data()
        self.view.hide()
        return True
            
    def on_cancel(self):
        self.model.sd_degree = 0
        DialogController.on_cancel(self)
            
    pass #end of class
