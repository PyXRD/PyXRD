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

from collections import namedtuple

from ....observers import Observer
from ....models.xydata import XYData

import gtk, gobject

from base_models import BaseObjectListStore

class PointMeta():
    @classmethod
    def get_column_properties(cls):
        return [
            ('x', float),
            ('y', float)
        ]
Point = namedtuple('Point', ['x', 'y'], verbose=False)
Point.Meta = PointMeta

class XYListStore(BaseObjectListStore, Observer):
    """
        GenericTreeModel implementation that wraps an XYData model.
    """
    _model = None
    _prop_name = None
    _last_lenght = 0

    __gsignals__ = {
        'columns-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())  # @UndefinedVariable
    }

    @property
    def _data(self):
        return getattr(self._model, self._prop_name, None)

    def is_wrapping(self, model, prop_name):
        return self._model == model and self._prop_name == prop_name

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, model, prop):
        # Check this really is an XYData property:
        self._model = model
        self._prop_name = prop.name
        _data = getattr(self._model, self._prop_name, None)
        assert isinstance(_data, XYData), \
            "Can only wrap XYData (or subclasses) instances to a " + \
            "XYListStore, but got '%s' instead." % _data

        # Continue initialisation:
        BaseObjectListStore.__init__(self, Point)
        Observer.__init__(self, model=self._data)
        self.set_property("leak-references", True)

        self._last_length = len(self)
        self._last_num_col = self._data.num_columns

        # Force update:
        self._emit_update()

    @Observer.observe("data_changed", signal=True)
    def on_data_changed(self, model, name, info):
        if model == self._data:
            self._emit_update()

    def _emit_update(self):
        # 1. check if number of columns has changed since last update
        #    if it has changed, emit the corresponding event
        if self._last_num_col != self._data.num_columns:
            self.emit("columns-changed")
            self._last_num_col = self._data.num_columns

        # 2. check if length has changed, if shorter emit removed signals
        #    for the lost elements, if longer emit insert signals
        row_diff = len(self._data) - self._last_length
        if row_diff > 0:
            for i in range(self._last_length, self._last_length + row_diff, 1):
                path = self.on_get_path(i)
                itr = self.get_iter(path)
                self.row_inserted(path, itr)
        elif row_diff < 0:
            for i in range(self._last_length, self._last_length + row_diff - 1, -1):
                path = self.on_get_path(i)
                self.row_deleted(path)
        self._last_length = len(self._data)

        # 3. Emit row-changed signals for all other rows:
        for i in range(0, len(self._data)):
            path = self.on_get_path(i)
            itr = self.get_iter(path)
            self.row_changed(path, itr)

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY

    def on_get_iter(self, path): # returns a rowref, they're actually just paths
        try:
            i = path[0]
            if i >= 0 and i < len(self):
                return [i, ]
            else:
                return None
        except IndexError:
            return None

    def on_get_value(self, rowref, column):
        if column == self.c_x:
            return self._data.data_x[rowref[0]]
        elif column >= self.c_y:
            return self._data.data_y[rowref[0], column - 1]
        else:
            raise AttributeError

    def on_get_path(self, rowref): # rowrefs are paths, unless they're None
        if rowref is None:
            return None
        if isinstance(rowref, tuple):
            return rowref
        elif isinstance(rowref, list):
            return tuple(rowref)
        else:
            return rowref,

    def on_iter_next(self, rowref):
        if rowref is not None:
            itr = self.on_get_iter((rowref[0] + 1,))
            return itr
        else:
            return None

    def on_iter_children(self, rowref):
        if rowref is not None:
            return None
        elif len(self) > 0:
            return self.on_get_iter((0,))
        return None

    def on_iter_has_child(self, rowref):
        if rowref is not None:
            return False
        elif len(self) > 0:
            return True
        return False

    def on_iter_n_children(self, rowref):
        if rowref is not None:
            return 0
        return self._data_x.size

    def on_iter_nth_child(self, rowref, n):
        if rowref is not None:
            return None
        if n < 0 or n >= len(self):
            return None
        return self.on_get_iter((n,))

    def on_iter_parent(self, rowref):
        return None

    def on_get_n_columns(self):
        return self._data.num_columns

    def on_get_column_type(self, index):
        return float

    def __len__(self):
        return self._data.size

    pass # end of class

gobject.type_register(XYListStore)  # @UndefinedVariable
