#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.utils import create_object_attribute_test

from pyxrd.phases.models import Phase

__all__ = [
    'TestPhase',
]

class TestPhase(unittest.TestCase):

    phase = None

    def setUp(self):
        self.phase = Phase(R=0, G=1)

    def tearDown(self):
        del self.phase

    def test_not_none(self):
        self.assertIsNotNone(self.phase)

    def test_data_object(self):
        self.assertIsNotNone(self.phase.data_object)

    def test_R_G(self):
        self.assertIsNotNone(Phase(R=0, G=1))
        self.assertIsNotNone(Phase(R=0, G=2))
        self.assertIsNotNone(Phase(R=0, G=3))
        self.assertIsNotNone(Phase(R=0, G=4))
        self.assertIsNotNone(Phase(R=0, G=5))
        self.assertIsNotNone(Phase(R=0, G=6))

        self.assertIsNotNone(Phase(R=1, G=2))
        self.assertIsNotNone(Phase(R=1, G=3))
        self.assertIsNotNone(Phase(R=1, G=4))

        self.assertIsNotNone(Phase(R=2, G=2))
        self.assertIsNotNone(Phase(R=2, G=3))

        self.assertIsNotNone(Phase(R=3, G=2))

    test_name = create_object_attribute_test("phase", "name", "Test Name")
    test_display_color = create_object_attribute_test("phase", "display_color", "#FF00FF")
    test_default_c = create_object_attribute_test("phase", "default_c", 0.646)
    test_sigma_star = create_object_attribute_test("phase", "sigma_star", 12.5)
    test_inherit_display_color = create_object_attribute_test("phase", "inherit_display_color", True)
    test_inherit_CSDS_distribution = create_object_attribute_test("phase", "inherit_CSDS_distribution", True)
    test_inherit_sigma_star = create_object_attribute_test("phase", "inherit_sigma_star", True)
    test_inherit_probabilities = create_object_attribute_test("phase", "inherit_probabilities", True)

    pass # end of class
