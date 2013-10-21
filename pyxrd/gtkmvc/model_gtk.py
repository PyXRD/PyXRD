# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

from pyxrd.gtkmvc.support import metaclasses
from pyxrd.gtkmvc.model import Model

class TreeStoreModel (Model, gtk.TreeStore):
    """Use this class as base class for your model derived by
    gtk.TreeStore"""
    __metaclass__ = metaclasses.ObservablePropertyGObjectMeta

    def __init__(self, column_type, *args):
        gtk.TreeStore.__init__(self, column_type, *args)
        Model.__init__(self)
        return

    pass # end of class

class ListStoreModel (Model, gtk.ListStore):
    """Use this class as base class for your model derived by
    gtk.ListStore"""
    __metaclass__ = metaclasses.ObservablePropertyGObjectMeta

    def __init__(self, column_type, *args):
        gtk.ListStore.__init__(self, column_type, *args)
        Model.__init__(self)
        return

    pass # end of class

class TextBufferModel (Model, gtk.TextBuffer):
    """Use this class as base class for your model derived by
    gtk.TextBuffer"""
    __metaclass__ = metaclasses.ObservablePropertyGObjectMeta

    def __init__(self, table=None):
        gtk.TextBuffer.__init__(self, table)
        Model.__init__(self)
        return

    pass # end of class
