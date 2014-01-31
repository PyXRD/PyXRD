#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from .base import AbstractTestProbModel

from test.utils import create_object_attribute_test

from pyxrd.probabilities.models.R2models import *
import unittest

__all__ = [
    'TestR2G2Model',
    'TestR2G3Model',
]

class TestR2G2Model(AbstractTestProbModel, unittest.TestCase):

    prob_model_type = R2G2Model

    test_W1 = create_object_attribute_test("prob_model", "W1", 0.7)
    test_P112_or_P211 = create_object_attribute_test("prob_model", "P112_or_P211", 0.7)
    test_P21 = create_object_attribute_test("prob_model", "P21", 0.7)
    test_P122_or_P221 = create_object_attribute_test("prob_model", "P122_or_P221", 0.7)

    pass # end of class

class TestR2G3Model(AbstractTestProbModel, unittest.TestCase):

    prob_model_type = R2G3Model

    test_W1 = create_object_attribute_test("prob_model", "W1", 0.7)
    test_P111_or_P212 = create_object_attribute_test("prob_model", "P111_or_P212", 0.7)
    test_G1 = create_object_attribute_test("prob_model", "G1", 0.7)
    test_G2 = create_object_attribute_test("prob_model", "G2", 0.7)
    test_G3 = create_object_attribute_test("prob_model", "G3", 0.7)
    test_G4 = create_object_attribute_test("prob_model", "G4", 0.7)

    pass # end of class
