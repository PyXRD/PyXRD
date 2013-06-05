#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from tests.utils import create_object_attribute_test

from gtkmvc.model import Observer
from generic.models import (
    PyXRDLine,
    CalculatedLine,
    ExperimentalLine,
)

__all__ = [
    'TestPyXRDLine',
    'TestCalculatedLine',
    'TestExperimentalLine',
]

class TestLineMixin():

    def setUp(self):
        self.line = self.line_type()

        class LineObserver(Observer):
            needs_update_recieved = False
            @Observer.observe("needs_update", signal=True)
            def on_update_needed(self, model, prop_name, info):
                self.needs_update_recieved = True

        self.observer = LineObserver(model=self.line)    

    def tearDown(self):
        self.observer.relieve_model(self.line)
        del self.observer
        del self.line
        
    def test_not_none(self):
        self.assertIsNotNone(self.line)
        
    test_lw = create_object_attribute_test('line', 'lw', 5)
    test_color = create_object_attribute_test('line', 'color', '#FF0000')
    test_label = create_object_attribute_test('line', 'label', '#FF0000')
      
    def test_store(self):
        self.observer.needs_update_recieved = False
        x = [1,2,3,4,5,6,7 ,8 ,9 ,10,11,12 ,13,14,15,16,17,18,19,20]
        y = [0,0,0,0,0,0,10,20,30,40,80,160,80,40,30,20,10,0 ,0 ,0 ]
        self.line.set_data(x, y)
        self.assertTrue(self.observer.needs_update_recieved)
        self.assertEqual(self.line.max_intensity, 160)
        self.assertEqual(self.line.size, 20)
        self.assertEqual(self.line.xy_store.get_y_at_x(7), 10)
        self.assertEqual(self.line.xy_store.get_y_at_x(10.5), 60)        
        
    def test_signal(self):
        self.observer.needs_update_recieved = False
        self.line.lw = 10
        self.assertTrue(self.observer.needs_update_recieved)
        
    pass #end of class

class TestPyXRDLine(TestLineMixin, unittest.TestCase):

    line_type = PyXRDLine
        
    pass #end of class
    
class TestCalculatedLine(TestLineMixin, unittest.TestCase):
    
    line_type = CalculatedLine
    
    def test_store(self):
        self.observer.needs_update_recieved = False
        x = [1,2,3,4,5,6,7 ,8 ,9 ,10,11,12 ,13,14,15,16,17,18,19,20]
        y = [0,0,0,0,0,0,10,20,30,40,80,160,80,40,30,20,10,0 ,0 ,0 ]
        self.line.set_data(x, y, phase_patterns=[list(y)], phases=[])
        self.assertTrue(self.observer.needs_update_recieved)
        self.assertEqual(self.line.max_intensity, 160)
        self.assertEqual(self.line.size, 20)
        self.assertEqual(self.line.xy_store.get_y_at_x(7), 10)
        self.assertEqual(self.line.xy_store.get_y_at_x(10.5), 60)
        
    def test_phases(self):
        class DummyPhase(object):
            def __init__(self, name, *args, **kwargs):
                super(DummyPhase, self).__init__(*args, **kwargs)
                self.name = name
                
        phase_name = "Dummy Phase"
        phase = DummyPhase(name=phase_name)
                        
        self.observer.needs_update_recieved = False
        x = [1,2,3,4,5,6,7 ,8 ,9 ,10,11,12 ,13,14,15,16,17,18,19,20]
        y = [0,0,0,0,0,0,10,20,30,40,80,160,80,40,30,20,10,0 ,0 ,0 ]
        self.line.set_data(x, y, phase_patterns=[list(y)], phases=[phase])
        self.assertEqual(self.line.xy_store.get_y_name(0), phase_name)
        self.assertEqual(self.line.xy_store.on_get_n_columns(), 3)

    pass #end of class
    
class TestExperimentalLine(TestLineMixin, unittest.TestCase):
    
    line_type = ExperimentalLine
    
    #TODO:
    # test bg substr
    # test smooth
    # test strip
    # test capping -> max intensity

    pass #end of class
