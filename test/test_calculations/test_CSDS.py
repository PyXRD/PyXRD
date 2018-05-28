#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

import numpy as np

from pyxrd.calculations.data_objects import CSDSData
from pyxrd.calculations.CSDS import calculate_distribution

__all__ = [
    'TestCSDSCalcs',
]

class TestCSDSCalcs(unittest.TestCase):

    def setUp(self):
        self.CSDS_data_kwargs = dict(
            average = 10,
            maximum = 50,
            minimum = 1,
            alpha_scale = 0.9485,
            alpha_offset = 0.017,
            beta_scale = 0.1032,
            beta_offset = 0.0034
        )
        self.CSDS_data = CSDSData(**self.CSDS_data_kwargs)

    def tearDown(self):
        del self.CSDS_data

    def test_not_none(self):
        self.assertIsNotNone(self.CSDS_data)
        
    def test_attributes(self):
        for key, value in self.CSDS_data_kwargs.items():
            self.assertEquals(getattr(self.CSDS_data, key), value)

    def test_calculate_distribution(self):
        result = calculate_distribution(
            self.CSDS_data
        )
        self.assertIsNotNone(result)
        self.assertEquals(len(result), 2)

    pass # end of class


calculate_distribution