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

import gtk
from .basic import GtkAdapter

class TextViewAdapter(GtkAdapter):
    """
        An adapter for a TextView widget.
    """
    widget_types = ["text_view", ]
    _check_widget_type = gtk.TextView

    _prop_cast = False

    def _read_widget(self):
        """Returns the value currently stored into the widget."""
        return str(self._buffer.get_text(*self._buffer.get_bounds()))

    def _write_widget(self, val):
        """Writes value into the widget. If specified, user setter
        is invoked."""
        with self._ignore_notifications():
            return self._buffer.set_text(val)


    _signal = "changed"

    def __init__(self, controller, prop, widget,
                 value_error=None, spurious=False, update=True):

        if prop.data_type == object: # assume TextBuffer type
            # TODO
            self._buffer = self._read_property()
        else: # assume string type
            self._buffer = gtk.TextBuffer()

        super(TextViewAdapter, self).__init__(controller, prop, widget,
                 value_error=value_error, spurious=spurious, update=update)

        self._widget.set_buffer(self._buffer)

    def _connect_widget(self):
        """Called when the adapter is ready to connect to the widget"""

        # Connect the widget
        if self._signal:
            self._signal_id = self._buffer.connect(
               self._signal, self._on_wid_changed, self._signal_args)

        # Updates the widget:
        if self._update: self.update_widget()
        return

    def _disconnect_widget(self, widget=None):
        """Disconnects the widget"""
        if self._signal is not None and self._signal_id is not None:
            self._buffer.disconnect(self._signal_id)

    def _set_property_value(self, val):
        """Private method that sets the property value stored in the model,
        without transformations."""
        return setattr(self._model, self._prop.name, val)

    pass # end of class

