# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from generic.plot.controllers import EyedropperCursorPlot
from generic.controllers import DialogController
from generic.views.validators import FloatEntryValidator

from specimen.views import StripPeakView

class StripPeakController(DialogController):

    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name in ("strip_startx", "strip_endx", "noise_level"):
                    FloatEntryValidator(self.view[name])
                    self.adapt(name)                    
            return
            
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.model.strip_peak()
        self.view.hide()
        return True
            
    def on_cancel(self):
        self.model._strip_start_x = 0.0
        self.model._strip_pattern = None
        self.model.end_start_x = 0.0         
        DialogController.on_cancel(self)
        
    def on_sample_start_clicked(self, event):    
        self.sample("strip_startx")
        return True
            
    def on_sample_end_clicked(self, event):
        self.sample("strip_endx")
        return True
        
    def sample(self, attribute):
    
        def onclick(edc, x_pos, event):            
            if edc != None:
                edc.enabled = False
                edc.disconnect()
            if x_pos != -1:
                setattr(self.model, attribute, x_pos)
            self.view.get_toplevel().present()            
            del self.edc
        
        self.edc = EyedropperCursorPlot(
            self.parent.parent.plot_controller.figure,
            self.parent.parent.plot_controller.canvas,
            self.parent.parent.plot_controller.canvas.get_window(),
            onclick,
            True, True
        )
        
        self.view.get_toplevel().hide()
        self.parent.parent.view.get_toplevel().present()
            
    pass #end of class
