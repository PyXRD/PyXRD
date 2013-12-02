#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.utils import create_object_attribute_test

from pyxrd.project.models import Project
from pyxrd.mixture.models import Mixture

__all__ = [
    'TestMixture',
]

class TestMixture(unittest.TestCase):

    atom_type = None

    def setUp(self):
        self.project = Project(name="TestProject")
        self.mixture = Mixture(name="TestMixture", parent=self.project)

    def tearDown(self):
        del self.mixture
        del self.project

    def test_not_none(self):
        self.assertIsNotNone(self.mixture)

    def test_data_object(self):
        self.assertIsNotNone(self.mixture.data_object)

    test_name = create_object_attribute_test("mixture", "name", "Test Name")

    def test_parent(self):
        parent_project = Project(name="Parent2")
        self.mixture.parent = parent_project
        self.assertEqual(self.mixture.parent, parent_project)

    def test_add_phase_slot(self):
        index = self.mixture.add_phase_slot("TestPhase", 0.5)
        self.assertEqual(index, 0, "Adding a phase slot should return the correct index!")

    def test_add_specimen_slot(self):
        index = self.mixture.add_specimen_slot(None, 1.0, 0)
        self.assertEqual(index, 0, "Adding a specimen slot should return the correct index!")

    def test_add_order1(self):
        self.mixture.add_specimen_slot(None, 1.0, 0)
        self.assertEqual(len(self.mixture.specimens), 1)
        self.assertEqual(len(self.mixture.phases), 0)
        self.assertEqual(len(self.mixture.fractions), 0)
        self.assertEqual(self.mixture.phase_matrix.shape, (1, 0))
        self.mixture.add_phase_slot("TestPhase", 0.5)
        self.assertEqual(len(self.mixture.specimens), 1)
        self.assertEqual(len(self.mixture.phases), 1)
        self.assertEqual(len(self.mixture.fractions), 1)
        self.assertEqual(self.mixture.phase_matrix.shape, (1, 1))
        self.assertEqual(self.mixture.phase_matrix[0, 0], None)

    def test_add_order2(self):
        self.mixture.add_phase_slot("TestPhase", 0.5)
        self.assertEqual(len(self.mixture.specimens), 0)
        self.assertEqual(len(self.mixture.phases), 1)
        self.assertEqual(len(self.mixture.fractions), 1)
        self.assertEqual(self.mixture.phase_matrix.shape, (0, 1))
        self.mixture.add_specimen_slot(None, 1.0, 0)
        self.assertEqual(len(self.mixture.specimens), 1)
        self.assertEqual(len(self.mixture.phases), 1)
        self.assertEqual(len(self.mixture.fractions), 1)
        self.assertEqual(self.mixture.phase_matrix.shape, (1, 1))
        self.assertEqual(self.mixture.phase_matrix[0, 0], None)

    def test_add_multiple(self):
        self.mixture.add_phase_slot("TestPhase", 0.5)
        self.mixture.add_specimen_slot(None, 1.0, 0)
        self.mixture.add_specimen_slot(None, 1.0, 0)
        self.mixture.add_phase_slot("TestPhase2", 0.5)
        self.mixture.add_phase_slot("TestPhase3", 0.5)
        self.assertEqual(len(self.mixture.specimens), 2)
        self.assertEqual(len(self.mixture.phases), 3)
        self.assertEqual(len(self.mixture.fractions), 3)
        self.assertEqual(self.mixture.phase_matrix.shape, (2, 3))

    pass # end of class
