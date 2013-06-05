#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gobject
import unittest

from gtkmvc.model import Observer
from generic.models.treemodels.base_models import BaseObjectListStore

__all__ = [
    'TestBaseObjectListStore',
]

class TestBaseObjectListStoreMixin(object):

    class DummyObject(object):
        __columns__ = [
            ["name", str],
            ["number", float],
            ["object", object]
        ]
        
        def __init__(self, *args, **kwargs):
            super(TestBaseObjectListStoreMixin.DummyObject, self).__init__()
            for key,val in kwargs.iteritems():
                setattr(self, key, val)
                
        pass #end of class

    def setUp(self):
        self.store = self.store_type(self.DummyObject)

    def tearDown(self):
        del self.store

    def test_setup(self):
        self.assertNotEqual(self.store, None)
        
    def test_columns(self):
        self.assertEqual(self.store.get_n_columns(), len(self.DummyObject.__columns__))
        self.assertEqual(self.store.get_column_type(self.store.c_name), gobject.type_from_name("gchararray"))
        self.assertEqual(self.store.get_column_type(self.store.c_number), gobject.type_from_name("gdouble"))
        self.assertEqual(self.store.get_column_type(self.store.c_object), gobject.type_from_name("PyObject"))
                
    def test_convert(self):
        self.assertEqual(self.store.convert(1, "0.5"), 0.5)

class TestBaseObjectListStore(TestBaseObjectListStoreMixin, unittest.TestCase):
    
    store_type = BaseObjectListStore
        
    pass #end of class
