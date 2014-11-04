# coding=UTF-8
# ex:ts=4:sw=4:et=on
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

import re
import gtk
from .entry_adapter import EntryAdapter

class FloatEntryAdapter(EntryAdapter):
    """
        An adapter for a gtk.Entry widget holding a float.
    """
    widget_types = ["float_entry", "float_input"]
    _check_widget_type = gtk.Entry
    _signal = "changed"

    def __init__(self, *args, **kwargs):
        super(FloatEntryAdapter, self).__init__(*args, **kwargs)
        numeric_const_pattern = r"""
        [-+]? # optional sign
        (?:
            (?: \d* \. \d+ ) # .1 .12 .123 etc 9.1 etc 98.1 etc
            |
            (?: \d+ \.? ) # 1. 12. 123. etc 1 12 123 etc
        )
        # followed by optional exponent part if desired
        (?: [Ee] [+-]? \d+ ) ?
        """
        self.rx = re.compile(numeric_const_pattern, re.VERBOSE)

    def _prop_read(self, *args):
        return str(*args)

    def _prop_write(self, *args):
        try:
            return float(*args)
        except ValueError:
            return self._get_property_value()

    def _on_wid_changed(self, widget, *args):
        """Called when the widget is changed"""
        with self._block_widget_signal():
            if self._ignoring_notifs: return
            self._validate_float(widget)
            super(FloatEntryAdapter, self)._on_wid_changed(widget, *args)

    def _validate_float(self, entry):
        entry_text = entry.get_text()
        newtext = self.rx.findall(entry_text)
        if len(newtext) > 0:
            entry.set_text(newtext[0])
        else:
            entry.set_text("")

    pass # end of class
