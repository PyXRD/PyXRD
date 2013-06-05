#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gobject, gtk
import unittest

from gtkmvc.model import Observer
from generic.models.treemodels import ObjectListStore

from tests.test_generic.test_models.test_treemodels.test_base import TestBaseObjectListStoreMixin

__all__ = [
    'TestObjectListStore',
]

class TestObjectListStore(TestBaseObjectListStoreMixin, unittest.TestCase):
    
    store_type = ObjectListStore
                
    class StoreObserver(object):
        last_item_removed = None
        last_item_inserted = None
    
        def __init__(self, store, *args, **kwargs):
            super(TestObjectListStore.StoreObserver, self).__init__(*args, **kwargs)
            store.connect("item-removed", self.on_item_removed)
            store.connect("item-inserted", self.on_item_inserted)
                
        def on_item_removed(self, store, item, *args, **kwargs):
            self.last_item_removed = item
                
        def on_item_inserted(self, store, item, *args, **kwargs):
            self.last_item_inserted = item
        
        pass #end of class
              
    def setUp(self):
        super(TestObjectListStore, self).setUp()
        self.observer = TestObjectListStore.StoreObserver(self.store)
        self.obj1 = TestObjectListStore.DummyObject(name="Test", number=0.5, object=None)
        self.obj2 = TestObjectListStore.DummyObject(name="Test", number=0.5, object=self.obj1)
        
    def tearDown(self):
        super(TestObjectListStore, self).tearDown()
        del self.observer
        del self.obj1
        del self.obj2
        
    def test_operations(self):
        self.store.clear()
        self.store.append(self.obj1)
        self.assertEqual(self.store.get_user_data_from_index(0), self.obj1)
        self.store.remove_item(self.obj1)
        self.store.insert(0, self.obj1)
        self.assertEqual(self.store.get_user_data_from_index(0), self.obj1)
        self.store.remove_item(self.obj1)
        self.store.append(self.obj1)
        self.store.append(self.obj2)
        self.assertEqual(self.store.get_user_data_from_index(0), self.obj1)
        self.assertEqual(self.store.get_user_data_from_index(1), self.obj2)
        self.store.reposition_item(self.obj2, 0)
        self.assertEqual(self.store.get_user_data_from_index(0), self.obj2)
        self.store.move_item_down(self.obj2)
        self.assertEqual(self.store.get_user_data_from_index(1), self.obj2)
        self.store.move_item_up(self.obj2)
        self.assertEqual(self.store.get_user_data_from_index(0), self.obj2)
        self.store.clear()
        
    def test_signals(self):
        self.observer.last_item_removed = None
        self.observer.last_item_inserted = None
        
        self.store.clear()
        self.store.append(self.obj1)
        self.store.append(self.obj2)
        
        self.assertEqual(self.observer.last_item_inserted, self.obj2)
        
        self.store.remove_item(self.obj1)
        self.assertEqual(self.observer.last_item_removed, self.obj1)

    def test_paths_iters(self):
        self.store.append(self.obj1)
        
        path1 = self.store.on_get_path(self.obj1)
        self.assertEqual(path1, (0,))
        iter1 = self.store.on_get_iter(path1)
        self.assertEqual(iter1, self.obj1)
        real_iter1 = self.store.get_iter(path1)
        self.assertIsInstance(real_iter1, gtk.TreeIter)
        
    def test_values(self):
        self.store.clear()
        self.store.append(self.obj1)
        pth = self.store.on_get_path(self.obj1)
        itr = self.store.get_iter(pth)

        new_name = "Crazy name"
        self.obj1.name = new_name
        self.assertEqual(self.store.get_value(itr, self.store.c_name), new_name)

        new_name = "Crazy name2"
        self.store.set_value(itr, self.store.c_name, new_name)
        self.assertEqual(self.obj1.name, new_name)        
    
    # TODO:
    # - test JSON serialisation
    # - test raw data
        
    pass #end of class
