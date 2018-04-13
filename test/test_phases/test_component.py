#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.utils import create_object_attribute_test

from pyxrd.phases.models import Component

__all__ = [
    'TestComponent',
]

class TestComponent(unittest.TestCase):

    component = None

    def setUp(self):
        self.component = Component()

    def tearDown(self):
        del self.component

    def test_not_none(self):
        self.assertIsNotNone(self.component)

    def test_data_object(self):
        self.assertIsNotNone(self.component.data_object)

    test_name = create_object_attribute_test("component", "name", "Test Name")
    test_d001 = create_object_attribute_test("component", "d001", 0.789)
    test_default_c = create_object_attribute_test("component", "default_c", 0.646)
    test_delta_c = create_object_attribute_test("component", "delta_c", 0.002)
    test_inherit_atom_relations = create_object_attribute_test("component", "inherit_atom_relations", True)
    test_inherit_interlayer_atoms = create_object_attribute_test("component", "inherit_interlayer_atoms", True)
    test_inherit_layer_atoms = create_object_attribute_test("component", "inherit_layer_atoms", True)
    test_inherit_delta_c = create_object_attribute_test("component", "inherit_delta_c", True)
    test_inherit_default_c = create_object_attribute_test("component", "inherit_default_c", True)
    test_inherit_ucp_a = create_object_attribute_test("component", "inherit_ucp_a", True)
    test_inherit_ucp_b = create_object_attribute_test("component", "inherit_ucp_b", True)
    test_inherit_d001 = create_object_attribute_test("component", "inherit_d001", True)

    def _setup_inheritance(self):
        self.component2 = Component()
        self.component2.linked_with = self.component
        self.component2.inherit_atom_relations = True # TODO
        self.component2.inherit_interlayer_atoms = True # TODO
        self.component2.inherit_layer_atoms = True # TODO
        self.component2.inherit_delta_c = True
        self.component2.inherit_default_c = True
        self.component2.inherit_ucp_a = True # TODO
        self.component2.inherit_ucp_b = True # TODO
        self.component2.inherit_d001 = True

    def test_inheritance_for_delta_c(self):
        self._setup_inheritance()

        self.component.delta_c = 0.005
        self.assertEqual(self.component2.delta_c, 0.005)

    def test_inheritance_for_default_c(self):
        self._setup_inheritance()

        self.component.default_c = 0.750
        self.assertEqual(self.component2.default_c, 0.750)

    def test_inheritance_for_d001(self):
        self._setup_inheritance()

        self.component.d001 = 0.750
        self.assertEqual(self.component2.d001, 0.750)

    pass # end of class