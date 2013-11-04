#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.utils import create_object_attribute_test

from pyxrd.phases.models.unit_cell_prop import UnitCellProperty

__all__ = [
    'TestPhase',
]

class TestPhase(unittest.TestCase):

    phase = None

    def setUp(self):
        self.ucp = UnitCellProperty(
            name="TestUCP",
            value=0.0,
            enabled=False,
            factor=0.0,
            constant=0.0,
            prop=None,
            parent=None
        )

    def tearDown(self):
        del self.ucp

    def test_not_none(self):
        self.assertIsNotNone(self.ucp)

    def test_value_of_prop(self):
        class Dummy():
            attribute = "Test123"

        dummy = Dummy()
        self.ucp.prop = (dummy, "attribute")
        self.assertEqual(self.ucp.get_value_of_prop(), dummy.attribute)

        self.ucp.prop = (None, "attribute")
        self.assertEqual(self.ucp.get_value_of_prop(), 0.0)

    def test_update_value(self):
        class Dummy():
            attribute = 0.5

        dummy = Dummy()
        self.ucp.prop = (dummy, "attribute")
        self.ucp.factor = 0.5
        self.ucp.constant = 1.0

        self.ucp.value = 0.075
        self.assertEqual(self.ucp.value, 0.075)

        self.ucp.enabled = True
        self.assertEqual(self.ucp.value, 0.5 * 0.5 + 1.0)

    test_name = create_object_attribute_test("ucp", "name", "Test Name")
    test_name = create_object_attribute_test("ucp", "value", 0.5)
    test_name = create_object_attribute_test("ucp", "factor", 0.5)
    test_name = create_object_attribute_test("ucp", "constant", 0.5)
    test_name = create_object_attribute_test("ucp", "prop", (None, ""))
    test_name = create_object_attribute_test("ucp", "enabled", True)
    test_name = create_object_attribute_test("ucp", "inherited", True)

    pass # end of class
