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

import types
import gtk

class BaseObjectListStore(gtk.GenericTreeModel):
    """
        Base mixin for creating GenericTreeModel implementations for lists of
        objects. It maps the columns of the store with properties of the object.
        If the PyGTK modules are not available (e.g. on a headless HPC cluster),
        a dummy gtk module is loaded. Not all (GTK) functionality is enabled in that case.
    """

    # PROPERTIES
    _columns = None # list of tuples (name, type)
    _class_type = None

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, class_type):
        gtk.GenericTreeModel.__init__(self)
        self.set_property("leak-references", False)
        if class_type is None:
            raise ValueError, 'Invalid class_type for %s! Expecting object, but None was given' % type(self)
        elif not hasattr(class_type, "Meta") or not hasattr(class_type.Meta, 'get_column_properties'):
            raise ValueError, 'Invalid class_type for %s! %s.Meta does not have get_column_properties method!' % (type(self), class_type)
        else:
            self.setup_class_type(class_type)

    def setup_class_type(self, class_type):
        self._class_type = class_type
        self._columns = []
        for item in self._class_type.Meta.get_column_properties():
            title, col_type = item
            if col_type in types.StringTypes:
                col_type = 'gchararray'
            # TODO map other types we might encounter...
            self._columns.append((title, col_type))

        i = 0
        for col in self._columns:
            setattr(self, "c_%s" % col[0], i)
            i += 1

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY | gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_n_columns(self):
        return len(self._columns)

    def on_get_column_type(self, index):
        return self._columns[index][1]

    def get_user_data_from_path(self, path):
        return self.on_get_iter(path)

    def convert(self, col, new_val):
        if isinstance(self._columns[col][1], str):
            return str(new_val)
        else:
            return self._columns[col][1](new_val)

    def get_objects(self):
        raise NotImplementedError

    def iter_objects(self):
        raise NotImplementedError

    def __reduce__(self):
        raise NotImplementedError

    pass # end of class
