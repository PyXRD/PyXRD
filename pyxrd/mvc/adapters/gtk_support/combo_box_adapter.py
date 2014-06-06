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
import logging
from pyxrd.generic.utils import not_none
logger = logging.getLogger(__name__)

import gtk
from .basic import GtkAdapter
import types

class ComboBoxAdapter(GtkAdapter):
    """
        An adapter that adapts a ComboBox widget to an OptionPropIntel property.
    """
    widget_types = ["option_list", ]
    _check_widget_type = gtk.ComboBox

    _wid_read = lambda c, w, *a: gtk.ComboBox.get_active_iter(w, *a)
    _wid_write = lambda c, w, *a: gtk.ComboBox.set_active_iter(w, *a)
    _signal = "changed"

    _prop_cast = False

    def _parse_prop(self, prop, model):
        """Parses (optional) prop strings for the given model"""
        prop, model = super(ComboBoxAdapter, self)._parse_prop(prop, model)
        if not isinstance(prop.options, types.DictionaryType):
            raise ValueError, "ComboBox widget handler requires a PropIntel with an 'options' dictionary!"
        else:
            self._store = gtk.ListStore(str, str)
            for key, value in prop.options.iteritems():
                self._store.append([key, value])
        return prop, model

    def _prop_write(self, itr):
        if itr is not None:
            return self._store.get_value(itr, 0)

    def _prop_read(self, val):
        for row in self._store:
            if self._store.get_value(row.iter, 0) == str(val):
                return row.iter

    def _connect_widget(self):
        # Set up the combo box layout:
        cell = gtk.CellRendererText()
        self._widget.clear()
        self._widget.pack_start(cell, True)
        self._widget.add_attribute(cell, 'text', 1)
        cell.set_property('family', 'Monospace')
        cell.set_property('size-points', 10)

        # Set the model:
        self._widget.set_model(self._store)

        # Continue as usual:
        super(ComboBoxAdapter, self)._connect_widget()

    def disconnect(self, model=None, widget=None):
        widget = not_none(self._widget, widget)
        if widget is not None: widget.set_model(None)
        super(ComboBoxAdapter, self).disconnect(model=model, widget=widget)

    pass # end of class
