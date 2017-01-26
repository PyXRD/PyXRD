# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

from pyxrd.generic.views import DialogView

class AddInSituBehaviourView(DialogView):
    title = "Add Behaviour"
    subview_builder = resource_filename(__name__, "glade/add_behaviour.glade")
    subview_toplevel = "add_behaviour_container"

    def __init__(self, *args, **kwargs):
        DialogView.__init__(self, *args, **kwargs)

    def get_behaviour_type(self):
        itr = self.behaviour_combo_box.get_active_iter()
        val = self.behaviour_combo_box.get_model().get_value(itr, 1) if itr else None
        return val

    @property
    def behaviour_combo_box(self):
        return self["cmb_behaviours"]

    pass # end of class