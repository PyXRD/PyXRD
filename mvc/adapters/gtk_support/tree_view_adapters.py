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
from ..abstract_adapter import AbstractAdapter

def wrap_property_to_treemodel_type(model, prop, treemodel_type):
    prop_value = getattr(model, prop.name)
    if not isinstance(prop_value, gtk.TreeModel):
        wrapper = getattr(model, "__%s_treemodel_wrapper" % prop.name, None)
        if wrapper is None or not wrapper.is_wrapping(model, prop.name):
            wrapper = treemodel_type(model, prop)
        setattr(model, "__%s_treemodel_wrapper" % prop.name, wrapper)
        prop_value = wrapper
    return prop_value

def wrap_treenode_property_to_treemodel(model, prop):
    """
        Convenience function that (sparsely) wraps a TreeNode property
        to an ObjectTreeStore. If the property is a gtk.TreeModel instance,
        it returns it without wrapping.
    """
    from .treemodels import ObjectTreeStore
    return wrap_property_to_treemodel_type(model, prop, ObjectTreeStore)

def wrap_list_property_to_treemodel(model, prop):
    """
        Convenience function that (sparsely) wraps a list property
        to an ObjectListStore. If the property is an gtk.TreeModel instance,
        it returns it without wrapping.
    """
    from .treemodels import ObjectListStore
    return wrap_property_to_treemodel_type(model, prop, ObjectListStore)

def wrap_xydata_to_treemodel(model, prop):
    """
        Convenience function that (sparsely) wraps an XYData model
        to an XYListStore. If the property is an gtk.TreeModel instance,
        it returns it without wrapping.
    """
    from .treemodels import XYListStore
    return wrap_property_to_treemodel_type(model, prop, XYListStore)

class AbstractTreeViewAdapter(AbstractAdapter):
    """
        Abstract base class for the ObjectTreeViewAdapter and
        XYTreeViewAdapter.
    """
    toolkit = "gtk"
    _check_widget_type = gtk.TreeView

    _signal = "changed"

    def __init__(self, controller, prop, widget):
        super(AbstractTreeViewAdapter, self).__init__(controller, prop, widget)
        if self._check_widget_type is not None:
            widget_type = type(widget)
            if not isinstance(widget, self._check_widget_type):
                msg = "A '%s' can only be used for (a subclass of) a '%s' widget," + \
                    " and not for a '%s'!" % (type(self), self._check_widget_type, widget_type)
                raise TypeError, msg
        self._connect_widget()

    def _connect_widget(self):
        self._widget.set_model(self._treestore)
        setup = getattr(self._controller, "setup_%s_tree_view" % self._prop.name, None)
        if callable(setup):
            setup(self._treestore, self._widget)

    def _disconnect_widget(self, widget=None):
        # TODO reset_tree_view support
        self._widget.set_model(None)

    def _connect_model(self):
        pass # nothing to do

    def _disconnect_model(self, model=None):
        pass # nothing to do

    def _read_widget(self):
        pass # nothing to do

    def _write_widget(self, val):
        pass # nothing to do

    def _read_property(self, *args):
        pass # nothing to do

    def _write_property(self, value, *args):
        pass # nothing to do

    pass # end of class

class ObjectListViewAdapter(AbstractTreeViewAdapter):
    """
        An adapter for a TreeView widget, representing a list of objects.
    """

    widget_types = ["object_list_view", ]

    def __init__(self, controller, prop, widget):
        assert hasattr(prop, "class_type"), "ObjectTreeViewAdapter requires the " + \
            "'class_type' attribute to be set on the PropIntel to adapt.\n" + \
            "Controller: '%s', Model: '%s', Property: '%s'" % (controller, controller.model, prop.name)
        self._treestore = wrap_list_property_to_treemodel(controller.model, prop)
        super(ObjectListViewAdapter, self).__init__(controller, prop, widget)

    pass # end of class

class XYListViewAdapter(AbstractTreeViewAdapter): # TODO move this back outside this namespace or move the XYData object back in here...
    """
        An adapter for a TreeView widget, representing an XYData model.
    """

    widget_types = ["xy_list_view", ]

    def __init__(self, controller, prop, widget):
        self._treestore = wrap_xydata_to_treemodel(controller.model, prop)
        super(XYListViewAdapter, self).__init__(controller, prop, widget)

    pass # end of class

class ObjectTreeViewAdapter(AbstractTreeViewAdapter):
    """
        An adapter for a TreeView widget, representing a tree of objects.
    """

    widget_types = ["object_tree_view", ]

    def __init__(self, controller, prop, widget):
        self._treestore = wrap_treenode_property_to_treemodel(controller.model, prop)
        super(ObjectTreeViewAdapter, self).__init__(controller, prop, widget)

    pass # end of class