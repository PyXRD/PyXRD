# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

from pyxrd.gtkmvc.adapters import Adapter

class TextBufferAdapter(Adapter):

    def __init__(self, model, prop_name):
        super(TextBufferAdapter, self).__init__(
            model, prop_name,
            prop_cast=False
        )
        self._buffer = gtk.TextBuffer()

    def connect_widget(self, widget):
        self._wid = widget
        self._wid.set_buffer(self._buffer)
        super(TextBufferAdapter, self).connect_widget(
                self._buffer,
                TextBufferAdapter._get_text, gtk.TextBuffer.set_text,
                update=True, signal="changed"
        )

    @staticmethod
    def _get_text(bfr):
        return str(bfr.get_text(*bfr.get_bounds()))


class StoreAdapter(object):

    def __init__(self, model, prop_name, store_setter, store_getter=None):
        super(StoreAdapter, self).__init__()
        self._prop_name = prop_name
        self._model = model
        self._store_setter = store_setter
        self._store_getter = store_getter

    def get_property_name(self):
        return self._prop_name

    def _get_store(self):
        if callable(self._store_getter):
            return self._store_getter(self._model, self._prop_name)
        else:
            return getattr(self._model, self._prop_name)

    def connect_widget(self, widget):
        self._wid = widget
        self._store_setter(widget, self._get_store())

    pass # end of class

class DummyAdapter(object):
    """
        A dummy adapter for those cases where we don't really need to 'adapt'
        things, or where we just want to do it differently...
    """
    def __init__(self, prop_name, *args, **kwargs):
        super(DummyAdapter, self).__init__()
        self._prop_name = prop_name

    def get_property_name(self):
        return self._prop_name

    pass # end of class

class ComboAdapter(Adapter):

    def __init__(self, model, prop_name, list_prop_name=None, list_data=None, store=None):

        if store == None:
            if list_data is not None:
                store = gtk.ListStore(str, str)
            elif list_prop_name is not None:
                store = gtk.ListStore(str, str)
                list_data = getattr(model, list_prop_name)
            else:
                raise AttributeError, "Either one of list_prop_name, list_data or store is required to be passed!"
            for key in list_data:
                store.append([key, list_data[key]])
        self._store = store

        super(ComboAdapter, self).__init__(
            model, prop_name,
            prop_read=self.prop_read, prop_write=self.prop_write,
            prop_cast=False
        )

    def prop_write(self, itr):
        if itr is not None:
            return self._store.get_value(itr, 0)

    def prop_read(self, val):
        for row in self._store:
            if self._store.get_value(row.iter, 0) == str(val):
                return row.iter

    def connect_widget(self, wid):

        store = self._store

        # Set up the combo box layout and set the model:
        cell = gtk.CellRendererText()
        wid.clear()
        wid.pack_start(cell, True)
        wid.add_attribute(cell, 'text', 1)
        cell.set_property('family', 'Monospace')
        cell.set_property('size-points', 10)
        wid.set_model(store)

        # Setter and getters
        setter = gtk.ComboBox.set_active_iter
        getter = gtk.ComboBox.get_active_iter

        # Continue as usual:
        super(ComboAdapter, self).connect_widget(wid, getter, setter, update=True, signal="changed")
