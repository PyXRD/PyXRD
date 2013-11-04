#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.utils import create_object_attribute_test

from pyxrd.phases.models.CSDS import LogNormalCSDSDistribution, DritsCSDSDistribution

__all__ = [
    'TestLogNormalCSDSDistribution',
    'TestDritsCSDSDistribution'
]

class TestLogNormalCSDSDistribution(unittest.TestCase):

    component = None

    def setUp(self):
        self.CSDS = LogNormalCSDSDistribution()

    def tearDown(self):
        del self.CSDS

    def test_not_none(self):
        self.assertIsNotNone(self.CSDS)

    def test_data_object(self):
        self.assertIsNotNone(self.CSDS.data_object)

    test_average = create_object_attribute_test("CSDS", "average", 15)
    test_alpha_scale = create_object_attribute_test("CSDS", "alpha_scale", 0.5)
    test_alpha_offset = create_object_attribute_test("CSDS", "alpha_offset", 0.6)
    test_beta_scale = create_object_attribute_test("CSDS", "alpha_scale", 0.5)
    test_beta_offset = create_object_attribute_test("CSDS", "alpha_offset", 0.6)

    pass # end of class

class TestDritsCSDSDistribution(unittest.TestCase):

    component = None

    def setUp(self):
        self.CSDS = DritsCSDSDistribution()

    def tearDown(self):
        del self.CSDS

    def test_not_none(self):
        self.assertIsNotNone(self.CSDS)

    def test_data_object(self):
        self.assertIsNotNone(self.CSDS.data_object)

    test_average = create_object_attribute_test("CSDS", "average", 15)

    pass # end of class