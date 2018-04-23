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
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .basic import GtkAdapter
from ._gtk_color_utils import _parse_color_string, _parse_color_value

class ColorButtonAdapter(GtkAdapter):
    """
        An adapter for a Gtk.Label widget
    """
    widget_types = ["color", "color_button"]
    _check_widget_type = Gtk.ColorButton

    _wid_read = lambda s, w: w.get_rgba()
    _wid_write = lambda s, w, v: w.set_rgba(v) if w.get_realized() else None
    _signal = "color-set"

    _prop_read = lambda s, *a: _parse_color_string(*a)
    _prop_write = lambda s, *a: _parse_color_value(*a)

    pass # end of class
