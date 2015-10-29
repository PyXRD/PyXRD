# coding=UTF-8
# ex:ts=4:sw=4:et:
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#
#  mvc is a framework derived from the original pygtkmvc framework
#  hosted at: <http://sourceforge.net/projects/pygtkmvc/>
#
#  mvc is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  mvc is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor,
#  Boston, MA 02110, USA.
#  -------------------------------------------------------------------------

import gtk, gobject

from mvc.support.utils import round_sig

class ScaleEntry(gtk.HBox):
    """
        The ScaleEntry combines the generic GtkEntry and GtkScale widgets in
        one widget, with synchronized values and one changed signal.
    """

    __gsignals__ = {
        'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []), #@UndefinedVariable
    }

    @property
    def lower(self):
        return self.adjustment.get_lower()
    @lower.setter
    def lower(self, value):
        return self.adjustment.set_lower(value)

    @property
    def upper(self):
        return self.adjustment.get_upper()
    @upper.setter
    def upper(self, value):
        return self.adjustment.set_upper(value)

    def __init__(self, lower=0, upper=10, enforce_range=False):
        gtk.HBox.__init__(self, spacing=5)

        self.enforce_range = enforce_range

        if lower == None: lower = 0
        if upper == None: upper = 10
        lower = min(upper, lower)
        upper = max(upper, lower)

        step = max((upper - lower) / 200.0, 0.01)
        self.adjustment = gtk.Adjustment(
            0.0, lower, upper, step, step, 0.0)

        self.adjustment.connect('value-changed', self.on_adj_value_changed)

        self.scale = gtk.HScale(self.adjustment)
        self.scale.set_draw_value(False)
        self.scale.set_size_request(50, -1)
        self.scale.set_update_policy(gtk.UPDATE_DELAYED)

        self.entry = gtk.SpinButton(self.adjustment)
        self.entry.set_digits(5)
        self.entry.set_numeric(True)
        self.entry.set_size_request(150, -1)

        self.set_value(self.scale.get_value())

        gtk.HBox.pack_start(self, self.scale, expand=False)
        gtk.HBox.pack_start(self, self.entry, expand=False)
        self.set_focus_chain((self.entry,))


    _idle_changed_id = None
    def _idle_emit_changed(self):
        if self._idle_changed_id is not None:
            gobject.source_remove(self._idle_changed_id)
        self._idle_changed_id = gobject.idle_add(self._emit_changed)

    def _emit_changed(self):
        self.emit('changed')

    def on_adj_value_changed(self, adj, *args):
        self._idle_emit_changed()

    def _update_adjustment(self, lower, upper):
        step = round_sig(max((upper - lower) / 200.0, 0.0005))
        self.adjustment.configure(lower, upper,
            step, step, 0.0)

    def _update_range(self, value):
        lower, upper = self.lower, self.upper
        if not self.enforce_range:
            if value < (lower + abs(lower) * 0.05):
                lower = value - abs(value) * 0.2
            if value > (upper - abs(lower) * 0.05):
                upper = value + abs(value) * 0.2
            self._update_adjustment(lower, upper)

    def set_value(self, value):
        self._update_range(value)
        self.adjustment.set_value(value)

    def get_value(self):
        return self.adjustment.get_value()

    def get_children(self, *args, **kwargs):
        return []
    def add(self, *args, **kwargs):
        raise NotImplementedError
    def add_with_properties(self, *args, **kwargs):
        raise NotImplementedError
    def child_set(self, *args, **kwargs):
        raise NotImplementedError
    def child_get(self, *args, **kwargs):
        raise NotImplementedError
    def child_set_property(self, *args, **kwargs):
        raise NotImplementedError
    def child_get_property(self, *args, **kwargs):
        raise NotImplementedError
    def remove(self, *args, **kwargs):
        raise NotImplementedError
    def set_child_packing(self, *args, **kwargs):
        raise NotImplementedError
    def query_child_packing(self, *args, **kwargs):
        raise NotImplementedError
    def reorder_child(self, *args, **kwargs):
        raise NotImplementedError
    def pack_start(self, *args, **kwargs):
        raise NotImplementedError
    def pack_end(self, *args, **kwargs):
        raise NotImplementedError

    pass # end of class

gobject.type_register(ScaleEntry) #@UndefinedVariable
