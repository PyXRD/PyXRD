#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.utils import create_object_attribute_test

from mvc import Observer
from pyxrd.generic.models import (
    PyXRDLine,
    CalculatedLine,
    ExperimentalLine,
)

__all__ = [
    'TestPyXRDLine',
    'TestCalculatedLine',
    'TestExperimentalLine',
]

class LineObserver(Observer):
    needs_update_recieved = False
    @Observer.observe("data_changed", signal=True)
    @Observer.observe("visuals_changed", signal=True)
    def on_update_needed(self, model, prop_name, info):
        self.needs_update_recieved = True

class BaseTestLines():

    class BaseTestLine(unittest.TestCase):

        def setUp(self):
            self.line = self.line_type()
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

        def _set_some_data(self):
            x = [1, 2, 3, 4, 5, 6, 7 , 8 , 9 , 10, 11, 12 , 13, 14, 15, 16, 17, 18, 19, 20]
            y = [0, 0, 0, 0, 0, 0, 10, 20, 30, 40, 80, 160, 80, 40, 30, 20, 10, 0 , 0 , 0 ]
            y = list(zip(y, y))
            self.line.set_data(x, y)

        def test_updates(self):
            self.observer.needs_update_recieved = False
            self._set_some_data()
            self.assertTrue(self.observer.needs_update_recieved)

        def test_data(self):
            self._set_some_data()
            self.assertEqual(self.line.num_columns, 3)
            self.assertEqual(self.line.max_display_y, 160)
            self.assertEqual(self.line.size, 20)
            self.assertEqual(self.line.get_y_at_x(7), 10)
            self.assertEqual(self.line.get_y_at_x(10.5), 60)

        def test_names(self):
            self.observer.needs_update_recieved = False
            self._set_some_data()
            names = ["TestName"]
            self.line.y_names = names
            self.assertEqual(self.line.get_y_name(0), names[0])

        def test_append_valid(self):
            self.line.append(0, 0)
            self.assertEqual(self.line[0], (0.0, [0.0]))

        def test_append_valid_multi(self):
            self.line.append(0, [0, 1, 2])
            self.assertEqual(self.line[0], (0.0, [0.0, 1.0, 2.0]))

        def test_signal(self):
            self.observer.needs_update_recieved = False
            self.line.lw = 10
            self.assertTrue(self.observer.needs_update_recieved)

        def test_serialisation(self):
            x = [1, 2, 3, 4, 5, 6, 7 , 8 , 9 , 10, 11, 12 , 13, 14, 15, 16, 17, 18, 19, 20]
            y = [0, 0, 0, 0, 0, 0, 10, 20, 30, 40, 80, 160, 80, 40, 30, 20, 10, 0 , 0 , 0 ]
            self.line.set_data(x, y)
            serialised1 = self.line._serialize_data()
            self.line._set_from_serial_data(serialised1)
            serialised2 = self.line._serialize_data()
            self.assertEqual(serialised1, serialised2)

        pass # end of class
        
    pass # end of class

class TestPyXRDLine(BaseTestLines.BaseTestLine):

    line_type = PyXRDLine

    pass # end of class

class TestCalculatedLine(BaseTestLines.BaseTestLine):

    line_type = CalculatedLine

    pass # end of class

class TestExperimentalLine(BaseTestLines.BaseTestLine):

    line_type = ExperimentalLine

    # TODO:
    # test bg substr
    # test smooth
    # test strip
    # test capping -> max intensity

    pass # end of class
