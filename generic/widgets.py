# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import types
import gobject
import gtk
from gtk import Entry, HScale, HBox

from gtkmvc.adapters.default import add_adapter

from generic.validators import FloatEntryValidator
from generic.custom_math import round_sig
from generic.utils import delayed


class ScaleEntry(HBox):
  
    __gsignals__ = { 
        'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
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
        HBox.__init__(self, spacing=5)
        
        self.enforce_range = enforce_range

        if lower==None: lower = 0
        if upper==None: upper = 10
        lower = min(upper, lower)
        upper = max(upper, lower)
        
        step = max((upper-lower)/200.0, 0.01)
        self.adjustment = gtk.Adjustment(
            0.0, lower, upper, step, step, 1.0)
        
        self.scale = gtk.HScale(self.adjustment)
        self.scale.set_draw_value(False)
        self.scale.set_size_request(50, -1)
        self.scale.set_update_policy(gtk.UPDATE_DELAYED)
        self.scale.connect('value-changed', self.on_scale_value_changed)
        
        self.entry = Entry()
        FloatEntryValidator(self.entry)
        self.entry.set_size_request(200,-1)
        self.entry.connect('changed', self.on_entry_changed)
        
        self.set_value(self.scale.get_value())
        
        HBox.pack_start(self, self.scale, expand=False)
        HBox.pack_start(self, self.entry, expand=False)

    def on_scale_value_changed(self, *args, **kwargs):
        self._update_value_and_range(self.scale.get_value())
        return False

    def on_entry_changed(self, *args, **kwargs):
        self._update_value_and_range(self.get_text())
        return False

    def _update_adjustment(self, value, lower, upper):
        step = round_sig(max((upper-lower)/200.0, 0.01))
        self.adjustment.configure(value, lower, upper, 
            step, step, 1.0)

    inhibit_updates = False
    def _update_value_and_range(self, value):
        if not self.inhibit_updates:
            self.inhibit_updates = True   
            #set scale value:
            try: value = float(value)
            except ValueError:
               self.inhibit_updates = False
               return
            lower, upper = self.lower, self.upper
            if not self.enforce_range:
                if value < (lower + abs(lower)*0.05):
                    lower = value - abs(value)*0.2
                if value > (upper - abs(lower)*0.05):
                    upper = value + abs(value)*0.2
            else:
                value = max(min(value, upper), lower)
            self._update_adjustment(value, lower, upper)
            #set entry text:     
            self.entry.set_text(str(self.scale.get_value()))
            #emit 'toplevel' changed signal:
            self._delay_emit_changed()
            self.inhibit_updates = False
        
    @delayed(delay=100)
    def _delay_emit_changed(self):
        self.emit('changed')
        
    def set_value(self, value):
        self.set_text(value)

    def get_value(self):
        return float(self.get_text())

    def set_text(self, text):
        self._update_value_and_range(text)
        
    def get_text(self):
        return float(self.entry.get_text())

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
        
gobject.type_register(ScaleEntry)
add_adapter(ScaleEntry, "changed", ScaleEntry.get_value, ScaleEntry.set_value, types.FloatType)
