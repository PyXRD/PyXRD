#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.utils import create_object_attribute_test

from pyxrd.phases.models.atom_relations import AtomRatio

__all__ = [
    'TestAtomRatio',
]

class DummyHoldableSignal():
    def ignore(self):
        return self
    def __enter__(self):
        pass
    def __exit__(self, *args):
        pass

class DummyAtom():
    data_changed = DummyHoldableSignal()
    attribute = 0.0

class DummyParent():
    inherit_atom_relations = False

class TestAtomRatio(unittest.TestCase):

    phase = None

    def setUp(self):
        self.atom1 = DummyAtom()
        self.atom2 = DummyAtom()
        self.parent = DummyParent()
        self.atom_ratio = AtomRatio(
            name="TestRatio",
            sum=2,
            value=0.5,
            atom1=[self.atom1, "attribute"],
            atom2=[self.atom2, "attribute"],
            parent=self.parent
        )
        self.atom_ratio.resolve_relations()

    def tearDown(self):
        del self.atom1
        del self.atom2
        del self.atom_ratio

    def test_not_none(self):
        self.assertIsNotNone(self.atom_ratio)
        self.assertIsNotNone(self.atom_ratio.atom1[0])
        self.assertIsNotNone(self.atom_ratio.atom2[0])

    def test_apply_relation(self):
        self.atom_ratio.enabled = True
        self.atom_ratio.apply_relation()
        self.assertEqual(self.atom1.attribute, 1.0)
        self.assertEqual(self.atom2.attribute, 1.0)
        self.atom_ratio.value = 0.1
        self.atom_ratio.apply_relation()
        self.assertEqual(self.atom1.attribute, 0.2)
        self.assertEqual(self.atom2.attribute, 1.8)

    test_name = create_object_attribute_test("atom_ratio", "name", "Test Name")
    test_name = create_object_attribute_test("atom_ratio", "value", 0.5)
    test_name = create_object_attribute_test("atom_ratio", "sum", 6)
    test_name = create_object_attribute_test("atom_ratio", "atom1", (None, "Test"))
    test_name = create_object_attribute_test("atom_ratio", "atom2", (None, "Test"))

    pass # end of class
