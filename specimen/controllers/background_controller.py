# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from gtkmvc import Controller

from generic.controllers import DialogController
from generic.views.validators import FloatEntryValidator
from generic.controllers.utils import ctrl_setup_combo_with_list

from specimen.views import BackgroundView

class BackgroundController(DialogController):

    def register_view(self, view):
        super(BackgroundController, self).register_view(view)
        view.set_file_dialog(
            self.parent.get_load_dialog(
                title="Open XRD file for import",
                parent=view.get_top_widget()
            ),
            self.on_pattern_file_set
        )
        
    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "bg_type":
                    ctrl_setup_combo_with_list(self, 
                        self.view["cmb_bg_type"],
                        "bg_type", "_bg_types")
                elif name == "bg_position":
                    FloatEntryValidator(self.view["bg_offset"])
                    FloatEntryValidator(self.view["bg_position"])
                    self.adapt(name, "bg_offset")
                    self.adapt(name, "bg_position")
                elif name == "bg_scale":
                    FloatEntryValidator(self.view["bg_scale"])
                    self.adapt(name)
            return
            
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("bg_type", assign=True)
    def notif_bg_type_changed(self, model, prop_name, info):
        self.view.select_bg_view(self.model.get_bg_type_lbl().lower())
        return
            
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_pattern_file_set(self, dialog):
        filename = dialog.get_filename()
        parser = dialog.get_filter().get_data("parser")
        pattern = parser.parse(filename)[0].data
        bg_pattern_x = pattern[:,0].copy()
        bg_pattern_y = pattern[:,1].copy()
        del pattern
        
        if bg_pattern_x.shape != self.model.xy_store._model_data_x.shape:
            raise ValueError, "Shape mismatch: background pattern (shape = %s) and experimental data (shape = %s) need to have the same length!" % (bg_pattern_x.shape, self.model.xy_store._model_data_x.shape)
            dialog.unselect_filename(filename)
        else:
            self.model.bg_pattern = bg_pattern_y

    def on_btn_ok_clicked(self, event):
        self.model.remove_background()
        self.view.hide()
        return True
            
    def on_cancel(self):
        self.model.clear_bg_variables()
        DialogController.on_cancel(self)
            
    pass #end of class
