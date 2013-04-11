# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk, sys

class FloatEntryValidator:
    def __init__(self, entry):
        self.last_valid_val = 0
        self.has_valid_val = True
    
        self.entry = entry
        self.entry.connect("activate", self.entry_activate)
        self.entry.connect("focus_out_event", self.entry_focus_out)
        self.insert_handlerid = self.entry.connect("insert-text", self.entry_insert_text)
        self.delete_handlerid = self.entry.connect("delete-text", self.entry_delete_text)

    def validate(self, text=None, reset_if_invalid=False):
        text = text or self.entry.get_chars(0, -1)
        try:
            self.last_valid_val = float(text)
            self.has_valid_val = True
        except StandardError, e:
            self.has_valid_val = False
        if reset_if_invalid and not self.has_valid_val:
            self.entry.handler_block(self.insert_handlerid)
            self.entry.set_text("%f" % self.last_valid_val)
            self.has_valid_val = True
            self.entry.handler_unblock(self.insert_handlerid)

    def entry_activate(self, entry):
        self.validate(reset_if_invalid=True)

    def entry_focus_out(self, entry, event):
        self.validate(reset_if_invalid=True)
        return gtk.FALSE

    def entry_insert_text(self, entry, new_text, new_text_length, position):
        self.entry.stop_emission('insert-text')
        self.entry.handler_block(self.insert_handlerid)
        pos = self.entry.get_position()
        
        text = self.entry.get_chars(0, -1)
        old_text = text
        
        text = text[:pos] + new_text + text[pos:]
        
        self.validate(text)
        if self.has_valid_val:
            new_text = text
            self.entry.set_text(new_text)
            gtk.idle_add(lambda: self.entry.set_position(pos + (len(new_text) - len(old_text))))
        #while gtk.events_pending():
        #    gtk.main_iteration(False)
        self.entry.handler_unblock(self.insert_handlerid)        
        
    def entry_delete_text(self, entry, start, end):
       self.validate()
