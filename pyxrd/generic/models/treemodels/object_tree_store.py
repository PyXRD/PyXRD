# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from traceback import print_exc

try:
    import gtk, gobject
except ImportError:
    GOBJECT_AVAILABLE = False
else:
    GOBJECT_AVAILABLE = True

from pyxrd.generic.io import storables

from base_models import BaseObjectListStore

class ObjectTreeNode(object):

    def insert(self, index, child_node):
        if not isinstance(child_node, ObjectTreeNode):
            child_node = ObjectTreeNode(child_node)
        child_node.parent = self
        self._children.insert(index, child_node)
        return child_node

    def append(self, child_node):
        if not isinstance(child_node, ObjectTreeNode):
            child_node = ObjectTreeNode(child_node)
        child_node.parent = self
        self._children.append(child_node)
        return child_node

    def remove(self, child_node):
        self._children.remove(child_node)
        child_node._parent = None

    _parent = None
    @property
    def parent(self):
        return self._parent
    @parent.setter
    def parent(self, parent):
        if self._parent:
            self._parent.remove(self)
        self._parent = parent

    @property
    def has_children(self):
        return bool(self._children)

    @property
    def child_count(self):
        return len(self._children)

    def __init__(self, obj=None, children=()):
        super(ObjectTreeNode, self).__init__()
        self.object = obj
        self._children = list()
        for child in children: self.append(child)

    def get_child_node_index(self, child_node):
        return self._children.index(child_node)

    def get_root_node(self):
        parent = self.parent
        while parent.parent is not None:
            parent = parent.parent
        return parent

    def get_next_node(self):
        try:
            return self.parent.get_child_node(
                self.parent.get_child_node_index(self) + 1)
        except IndexError:
            return None

    def get_prev_node(self):
        try:
            return self.parent.get_child_node(
                self.parent.get_child_node_index(self) - 1)
        except IndexError:
            return None

    def get_indeces(self):
        parent = self.parent
        node = self
        indeces = tuple()
        while parent is not None:
            indeces += (parent.get_child_node_index(node),)
            node = parent
            parent = parent.parent
        return indeces[::-1] or None

    def get_child_node(self, *indeces):
        node = self
        for index in indeces:
            try:
                node = node._children[index]
            except IndexError:
                return None
        return node

    def get_first_child_node(self):
        try:
            return self._children[0]
        except IndexError:
            return None

    def get_child_object(self, *indeces):
        return self.get_child_node(*indeces).object

    def clear(self):
        for c in self.iter_children(reverse=True, recursive=True):
            yield c
            c.parent = None

    def iter_children(self, reverse=False, recursive=False):
        children = self._children if not reverse else self._children[::-1]
        for child_node in children:
            if recursive and child_node.has_children:
                for c in child_node.iter_children(reverse=reverse, recursive=recursive):
                    yield c
            yield child_node

    def __repr__(self):
        return '%s(%s - %s)' % (type(self).__name__, self.object, "%d child nodes" % len(self._children))

class ObjectTreeStore(BaseObjectListStore):
    """
        GenericTreeModel implementation that holds a tree with objects.
        It expects all objects to be of a certain type, which needs to be
        passed to the __init__ as the first argument. 
    """

    # MODEL INTEL:
    store_id = "ObjectTreeStore"

    # PROPERTIES:
    _root_node = None
    _object_node_map = None

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, class_type, parent=None):
        if isinstance(class_type, basestring):
            class_type = storables[class_type]
        BaseObjectListStore.__init__(self, class_type)
        self._root_node = ObjectTreeNode()
        self._object_node_map = dict()

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    if GOBJECT_AVAILABLE:
        def on_get_flags(self):
            return gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_iter(self, path):
        try:
            if hasattr(path, 'split'): path = map(int, path.split(":"))
            return self._root_node.get_child_node(*path)
        except IndexError, msg:
            print "IndexError in on_get_iter of %s caused by %s" % (self, path)
            print_exc()
            return None

    def on_get_path(self, node):
        try:
            return ":".join(map(str, node.get_indeces()))
        except ValueError:
            print "ValueError in on_get_path of %s caused by %s" % (self, node)
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

    def append(self, parent, item):
        if not isinstance(item, self._class_type):
            raise ValueError, 'Invalid type, must be %s but got %s instead' % (self._class_type, type(item))
        else:
            parent = parent or self._root_node
            node = parent.append(item)
            return self._emit_added(node)
    def insert(self, parent, pos, item):
        if not isinstance(item, self._class_type):
            raise ValueError, 'Invalid type, must be %s but got %s instead' % (self._class_type, type(item))
        else:
            parent = parent or self._root_node
            node = parent.insert(pos, item)
            return self._emit_added(node)
    def _emit_added(self, node):
        self._object_node_map[node.object] = node
        itr = self.create_tree_iter(node)
        path = self.get_path(itr)
        self.row_inserted(path, itr)
        return node

    def remove(self, itr):
        self.remove_item(self.get_tree_node(itr))
    def remove_item(self, node):
        indeces = node.get_indeces()
        node.parent = None # break link
        del self._object_node_map[node.object]
        self.row_deleted(indeces)

    def clear(self, callback=None):
        for node in self._root_node.clear():
            self.remove_item(node)
            if callable(callback): callback(node)

    def get_data(self):
        return self._root_node

    def iter_objects(self):
        for node in self._root_node.iter_children(recursive=True):
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

if GOBJECT_AVAILABLE:
    gobject.type_register(ObjectTreeStore) # @UndefinedVariable
