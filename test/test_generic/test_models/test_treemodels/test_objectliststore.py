#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gobject
import unittest

from pyxrd.generic.models import DataModel

from mvc.adapters.gtk_support.treemodels import ObjectListStore
from mvc.models.properties import (
    LabeledProperty, StringProperty, FloatProperty
)

__all__ = [
    'TestObjectListStore',
]


class _DummyObject(DataModel):

    name = StringProperty(text="Name", tabular=True, default="")
    number = FloatProperty(text="Number", tabular=True, default=0)
    test = LabeledProperty(text="Test", tabular=True, default=[])

    pass # end of class

class _DummyParent(DataModel):

    attrib = LabeledProperty(text="Attrib", default=[], tabular=True, data_type=_DummyObject)

    pass # end of class


class TestObjectListStore(unittest.TestCase):

    def setUp(self):
        self.model = _DummyParent()
        prop = type(self.model).attrib
        self.store = ObjectListStore(self.model, prop)

    def tearDown(self):
        super(TestObjectListStore, self).tearDown()
        del self.model

    def test_columns(self):
        self.assertEqual(self.store.get_n_columns(), len(_DummyObject.Meta.get_column_properties()))
        self.assertEqual(self.store.get_column_type(self.store.c_name), gobject.type_from_name("gchararray"))
        self.assertEqual(self.store.get_column_type(self.store.c_number), gobject.type_from_name("gdouble"))
        self.assertEqual(self.store.get_column_type(self.store.c_test), gobject.type_from_name("PyObject"))

    def test_convert(self):
        self.assertEqual(self.store.convert(self.store.c_number, "0.5"), 0.5)

    # TODO:
    # - test JSON serialisation
    # - test raw data

    pass # end of class
