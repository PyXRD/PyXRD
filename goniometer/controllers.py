# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import locale

import gtk

from gtkmvc import Controller

from generic.validators import FloatEntryValidator
from generic.controllers import DialogController

class GoniometerController (DialogController):

    def register_adapters(self):
        print "GoniometerController.register_adapters() model = %s" % self.model
        if self.model is not None:
            for name in self.model.get_properties():
                if name in ("data_radius", "data_divergence", "data_soller1", "data_soller2", "data_min_2theta", "data_max_2theta", "data_lambda"):
                    FloatEntryValidator(self.view["gonio_%s" % name])
                    self.adapt(name)
                else:
                    self.adapt(name)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    #def on_btn_ok_clicked(self, event):
    #    #self.parent.pop_status_msg('edit_gonio')
    #    return DialogController.on_btn_ok_clicked(self, event)
        
    pass # end of class
