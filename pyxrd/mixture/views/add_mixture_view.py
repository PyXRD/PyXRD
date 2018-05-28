# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from pyxrd.generic.views import DialogView

class AddMixtureView(DialogView):
    title = "Add Mixture"
    subview_builder = resource_filename(__name__, "glade/add_mixture.glade")
    subview_toplevel = "add_mixture_container"

    active_type = "mixture" # | insitu

    def __init__(self, type_dict, *args, **kwargs):
        DialogView.__init__(self, *args, **kwargs)
        self.type_dict = type_dict
        self.active_type=list(type_dict.keys())[0]
        self.create_radios()

    def create_radios(self):
        box = self["add_mixture_box"]
        box.clear()
        group = None
        self.radios = []
        for mixture_type, label in self.type_dict.items():
            radio = Gtk.RadioButton.new(group, label)
            radio.mixture_type = mixture_type
            group = radio if group is None else group 
            self.radios.append(radio)
            radio.connect('toggled', self.on_rdb_toggled)
            box.pack_start(radio, False, False, 2)

    def get_mixture_type(self):
        return self.active_type

    def on_rdb_toggled(self):
        for radio in self.radios:
            if radio.get_active():
                self.active_type = radio.mixture_type
    pass # end of class