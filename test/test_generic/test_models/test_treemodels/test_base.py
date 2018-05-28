#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gi
gi.require_version('Gtk', '3.0')  # @UndefinedVariable
from gi.repository import GObject  # @UnresolvedImport

import unittest

from mvc.adapters.gtk_support.treemodels import BaseObjectListStore

__all__ = [
    'TestBaseObjectListStore',
]

class _DummyObject(object):
    class Meta(object):
        @classmethod
        def get_column_properties(cls):
            return [
                ["name", str],
                ["number", float],
                ["test", object]
            ]

    def __init__(self, *args, **kwargs):
        super(_DummyObject, self).__init__()
        for key, val in kwargs.items():
            setattr(self, key, val)

    pass # end of class

class TestBaseObjectListStore(unittest.TestCase):

    def setUp(self):
        self.store = BaseObjectListStore(_DummyObject)

    def tearDown(self):
        del self.store

    def test_setup(self):
        self.assertNotEqual(self.store, None)

    def test_columns(self):
        self.assertEqual(self.store.get_n_columns(), len(self.store._class_type.Meta.get_column_properties()))
        self.assertEqual(self.store.get_column_type(self.store.c_name), GObject.type_from_name("gchararray"))
        self.assertEqual(self.store.get_column_type(self.store.c_number), GObject.type_from_name("gdouble"))
        self.assertEqual(self.store.get_column_type(self.store.c_test), GObject.type_from_name("PyObject"))

    def test_convert(self):
        self.assertEqual(self.store.convert(1, "0.5"), 0.5)

    pass # end of class
