#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.utils import create_object_attribute_test

from pyxrd.atoms.models import AtomType

__all__ = [
    'TestAtomType',
]

class TestAtomType(unittest.TestCase):

    atom_type = None

    def setUp(self):
        self.atom_type = AtomType()

    def tearDown(self):
        del self.atom_type

    def test_not_none(self):
        self.assertIsNotNone(self.atom_type)

    def test_data_object(self):
        self.assertIsNotNone(self.atom_type.data_object)

    test_name = create_object_attribute_test("atom_type", "name", "Test Name")
    test_charge = create_object_attribute_test("atom_type", "charge", -5)
    test_debye = create_object_attribute_test("atom_type", "debye", 1.0)
    test_weight = create_object_attribute_test("atom_type", "weight", 60.123)
    test_atom_nr = create_object_attribute_test("atom_type", "atom_nr", 20)
    test_par_c = create_object_attribute_test("atom_type", "par_c", 10.2)
    test_par_a1 = create_object_attribute_test("atom_type", "par_a1", 10.2)
    test_par_a2 = create_object_attribute_test("atom_type", "par_a2", 10.2)
    test_par_a3 = create_object_attribute_test("atom_type", "par_a3", 10.2)
    test_par_a4 = create_object_attribute_test("atom_type", "par_a4", 10.2)
    test_par_a5 = create_object_attribute_test("atom_type", "par_a5", 10.2)
    test_par_b1 = create_object_attribute_test("atom_type", "par_b1", 10.2)
    test_par_b2 = create_object_attribute_test("atom_type", "par_b2", 10.2)
    test_par_b3 = create_object_attribute_test("atom_type", "par_b3", 10.2)
    test_par_b4 = create_object_attribute_test("atom_type", "par_b4", 10.2)
    test_par_b5 = create_object_attribute_test("atom_type", "par_b5", 10.2)

    def test_parent(self):
        parent_atom_type = AtomType(name="Parent")
        self.atom_type.parent = parent_atom_type
        self.assertEqual(self.atom_type.parent, parent_atom_type)
        
    def test_get_atomic_scattering_factors(self):
        import numpy as np
        stl_range = np.array([ 0.1152, 0.5756, 1.1469 ])
        self.atom_type.par_a1 = 10.2
        self.atom_type.par_a2 = 10.2
        self.atom_type.par_a3 = 10.2
        self.atom_type.par_a4 = 10.2
        self.atom_type.par_a5 = 10.2
        self.atom_type.par_b1 = 10.2
        self.atom_type.par_b2 = 10.2
        self.atom_type.par_b3 = 10.2
        self.atom_type.par_b4 = 10.2
        self.atom_type.par_b5 = 10.2
        self.atom_type.par_c = 20.2
        self.assertListEqual(
            self.atom_type.get_atomic_scattering_factors(stl_range).tolist(),
            [ 71.1827439324707, 70.77093939463964, 69.51772020477823 ]
        )

    pass # end of class
