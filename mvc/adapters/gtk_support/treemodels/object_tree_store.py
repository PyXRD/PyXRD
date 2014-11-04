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

from traceback import print_exc
import logging
logger = logging.getLogger(__name__)

import gtk, gobject

from .base_models import BaseObjectListStore
from ....observers import TreeObserver

class ObjectTreeStore(BaseObjectListStore):
    """
        GenericTreeModel implementation that holds a tree with objects.
        It expects all objects to be of a certain type, which needs to be
        passed to the __init__ as the first argument. 
    """

    # PROPERTIES:
    _object_node_map = None

    @property
    def _root_node(self):
        return getattr(self._model, self._prop_name, None)

    def is_wrapping(self, model, prop_name):
        return self._model == model and self._prop_name == prop_name

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, model, prop):
        _root = getattr(model, prop.name, None)

        # Then continue:
        BaseObjectListStore.__init__(self, prop.class_type)
        self._model = model
        self._prop_name = prop.name
        self._object_node_map = dict()

        self._observer = TreeObserver(
            self.on_item_inserted, self.on_item_deleted,
            on_deleted_before=self.on_item_deleted_before,
            prop_name=self._prop_name, model=self._model
        )

    def on_item_inserted(self, item):
        try:
            itr = self.create_tree_iter(item)
            path = self.get_path(itr)
            # self._observe_item(item)
            self.row_inserted(path, itr)
        except ValueError:
            logger.debug("Invalid rowref passed: %s", item)
            pass # invalid rowref

    _deleted_paths = []
    def on_item_deleted_before(self, item):
        # self._unobserve_item(item)
        self._deleted_paths.append(self.on_get_path(item))

    def on_item_deleted(self, item):
        for path in self._deleted_paths:
            self.row_deleted(path)
        self._deleted_paths = []

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def on_get_flags(self):
        return gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_iter(self, path):
        try:
            if hasattr(path, 'split'): path = map(int, path.split(":"))
            return self._root_node.get_child_node(*path)
        except IndexError as err:
            err.args = "IndexError in on_get_iter of %s caused by %s" % (self, path)
            print_exc()
            return None

    def on_get_path(self, node):
        try:
            return ":".join(map(str, node.get_indeces()))
        except ValueError as err:
            err.args = "ValueError in on_get_path of %s caused by %s" % (self, node)
            print_exc()
            return None

    def set_value(self, itr, column, value):
        user_data = self.get_user_data(itr)
        setattr(user_data, self._columns[column][0], value)
        self.row_changed(self.get_path(itr), itr)

    def on_get_value(self, node, column):
        try:
            return getattr(node.object, self._columns[column][0])
        except:
            return ""

    def on_iter_next(self, node):
        return node.get_next_node()

    def on_iter_children(self, node):
        node = node or self._root_node
        return node.get_first_child_node()

    def on_iter_has_child(self, node):
        node = node or self._root_node
        return node.has_children

    def on_iter_n_children(self, node):
        node = node or self._root_node
        return node.child_count

    def on_iter_nth_child(self, parent, n):
        node = parent or self._root_node
        try:
            return node.get_child_node(n)
        except:
            return None

    def on_iter_parent(self, node):
        return node.parent

    def iter_objects(self):
        for node in self._root_node.iter_children():
            yield node.object

    def get_tree_node(self, itr):
        path = self.get_path(itr)
        return self.get_tree_node_from_path(path)

    def get_tree_node_from_path(self, path):
        return BaseObjectListStore.get_user_data_from_path(self, path)

    def get_user_data(self, itr):
        path = self.get_path(itr)
        return self.get_tree_node_from_path(path).object

    def get_user_data_from_path(self, path):
        return self.get_tree_node_from_path(path).object

    pass # end of class

gobject.type_register(ObjectTreeStore) # @UndefinedVariable
