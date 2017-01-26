# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

from pyxrd.generic.views import DialogView

class AddMixtureView(DialogView):
    title = "Add Mixture"
    subview_builder = resource_filename(__name__, "glade/add_mixture.glade")
    subview_toplevel = "add_mixture_container"

    active_type = "mixture" # | insitu

    def __init__(self, *args, **kwargs):
        DialogView.__init__(self, *args, **kwargs)

    def get_mixture_type(self):
        return self.active_type

    def update_sensitivities(self):
        if self["rdb_mixture"].get_active():
            self.active_type = "mixture"
        elif self["rdb_insitu"].get_active():
            self.active_type = "insitu"

    pass # end of class