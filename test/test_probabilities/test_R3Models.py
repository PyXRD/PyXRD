#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from .base import AbstractTestProbModel

from test.utils import create_object_attribute_test

from pyxrd.probabilities.models.R3models import *
import unittest

__all__ = [
    'TestR3G2Model'
]

class TestR3G2Model(AbstractTestProbModel, unittest.TestCase):

    prob_model_type = R3G2Model

    test_W1 = create_object_attribute_test("prob_model", "W1", 0.7)
    test_P1111_or_P2112 = create_object_attribute_test("prob_model", "P1111_or_P2112", 0.7)

    pass # end of class
