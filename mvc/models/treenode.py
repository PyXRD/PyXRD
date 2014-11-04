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

class TreeNode(object):
    """
        A TreeNode can be used to build a Tree of objects with parents & 
        children and support for inserting, appending, removing, iterating and
        inspecting them.
        This is the type that models should use.
        The root object can than be wrapped easily by a UI-toolkit specific 
        wrapper, like the gtk ObjectTreeStore wrapper. 
    """
    def insert(self, index, child_node):
        """
            Inserts the 'child_node' in this TreeNode at the given index.
            If the passed argument is not a TreeNode instance, it is wrapped
            in one. So you can safely pass in arbitrary objects.
            This functions returns the (wrapped) child_node.
        """
        assert isinstance(child_node, type(self))
        child_node.parent = self
        self._children.insert(index, child_node)
        self.on_grandchild_inserted(child_node)
        return child_node

    def append(self, child_node):
        """
            Appends the 'child_node' to this TreeNode. If the passed
            argument is not a TreeNode instance, it is wrapped in one.
            So you can safely pass in arbitrary objects.
            This functions returns the (wrapped) child_node.
        """
        assert isinstance(child_node, TreeNode)
        return self.insert(len(self._children), child_node)

    def remove(self, child_node):
        """
            Removes the given child_node from this TreeNode's list of children.
            'child_node' *must* be a TreeNode instance. 
        """
        assert isinstance(child_node, type(self))
        self.on_grandchild_removed(child_node)
        self._children.remove(child_node)
        child_node._parent = None

    def on_grandchild_removed(self, child_node):
        if self.parent is not None:
            self.parent.on_grandchild_removed(child_node)

    def on_grandchild_inserted(self, child_node):
        if self.parent is not None:
            self.parent.on_grandchild_removed(child_node)

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
        super(TreeNode, self).__init__()
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
        for c in self.iter_children(reverse=True):
            c.parent = None

    def iter_children(self, reverse=False, recursive=True):
        children = self._children if not reverse else self._children[::-1]
        for child_node in children:
            if recursive and child_node.has_children:
                for c in child_node.iter_children(reverse=reverse, recursive=recursive):
                    yield c
            yield child_node

    def __repr__(self):
        return '%s(%s - %s)' % (type(self).__name__, self.object, "%d child nodes" % len(self._children))
