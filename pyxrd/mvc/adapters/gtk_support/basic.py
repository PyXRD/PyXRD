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

from contextlib import contextmanager
from pyxrd.mvc.adapters.model_adapter import ModelAdapter
from pyxrd.generic.utils import not_none

class GtkAdapter(ModelAdapter):
    """
        A base class for Gtk-widget Adapters
    """
    toolkit = "gtk"

    # Widget-side value handling:
    _wid_read = None
    _wid_write = None
    _signal = None
    _signal_id = None
    _signal_args = []
    _check_widget_type = None

    def __init__(self, controller, prop, widget,
            prop_read=None, prop_write=None,
            value_error=None, spurious=False,
            wid_read=None, wid_write=None,
            signal=None, signal_args=None, update=True):
        """
            wid_read and wid_write are the methods used for reading and writing the
            widget's value.
            
            signal is the signal name to listen to for widget updates  
            signal_args is the (optional) (list of) argument(s) that will be
            passed when connecting the signal.
    
            Finally, if update is false, the widget will not be initially updated
        """
        super(GtkAdapter, self).__init__(
            controller, prop, widget,
            prop_read=prop_read, prop_write=prop_write,
            value_error=value_error, spurious=spurious
        )
        # Widget-side value handling:
        self._wid_read = not_none(wid_read, self._wid_read)
        self._wid_write = not_none(wid_write, self._wid_write)
        self._signal = not_none(signal, self._signal)
        self._signal_id = None
        self._signal_args = not_none(signal_args, self._signal_args)
        self._update = update

        if self._check_widget_type is not None:
            widget_type = type(widget)
            if not isinstance(widget, self._check_widget_type):
                msg = "Property '%s' has a widget type '%s', which can only be " \
                      "used for (a subclass of) a '%s' widget, " \
                      "and not for a '%s'!" % (prop.name, type(self), self._check_widget_type, widget_type)
                raise TypeError, msg
        # Connect the widget:
        self._connect_widget()

    # ----------------------------------------------------------------------
    #  Widget connecting & disconnecting:
    # ----------------------------------------------------------------------
    def _connect_widget(self):
        """Called when the adapter is ready to connect to the widget"""

        # Connect the widget
        if self._signal:
            self._signal_id = self._widget.connect(
               self._signal, self._on_wid_changed, self._signal_args)

        # Updates the widget:
        if self._update: self.update_widget()
        return

    def _on_wid_changed(self, wid, *args):
        """Called when the widget is changed"""
        if self._ignoring_notifs: return
        self.update_model()
        return

    def _disconnect_widget(self, widget=None):
        """Disconnects the widget"""
        if self._signal is not None and self._signal_id is not None:
            widget = not_none(self._widget, widget)
            if widget is not None:
                widget.disconnect(self._signal_id)
            self._signal, self._signal_id = None, None

    # ----------------------------------------------------------------------
    #  Widget-side reading and writing
    # ----------------------------------------------------------------------
    @contextmanager
    def _block_widget_signal(self):
        self._widget.handler_block(self._signal_id)
        yield
        self._widget.handler_unblock(self._signal_id)

    def _read_widget(self):
        """Returns the value currently stored into the widget."""
        return self._wid_read(self._widget)

    def _write_widget(self, val):
        """Writes value into the widget. If specified, user setter
        is invoked."""
        with self._ignore_notifications():
            return self._wid_write(self._widget, val)

    @staticmethod
    def static_to_class(func):
        def wrapper(c, *args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    pass # end of class
