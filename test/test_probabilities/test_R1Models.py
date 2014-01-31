#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from .base import AbstractTestProbModel

from test.utils import create_object_attribute_test

from pyxrd.probabilities.models.R1models import *
import unittest

__all__ = [
    'TestR1G2Model',
    'TestR1G3Model',
    'TestR1G4Model',
]

class TestR1G2Model(AbstractTestProbModel, unittest.TestCase):

    prob_model_type = R1G2Model

    test_W1 = create_object_attribute_test("prob_model", "W1", 0.7)
    test_P11_or_P22 = create_object_attribute_test("prob_model", "P11_or_P22", 0.7)

    pass # end of class

class TestR1G3Model(AbstractTestProbModel, unittest.TestCase):

    prob_model_type = R1G3Model

    test_W1 = create_object_attribute_test("prob_model", "W1", 0.7)
    test_P11_or_P22 = create_object_attribute_test("prob_model", "P11_or_P22", 0.7)
    test_G1 = create_object_attribute_test("prob_model", "G1", 0.7)
    test_G2 = create_object_attribute_test("prob_model", "G2", 0.7)
    test_G3 = create_object_attribute_test("prob_model", "G3", 0.7)
    test_G4 = create_object_attribute_test("prob_model", "G4", 0.7)

    pass # end of class

class TestR1G4Model(AbstractTestProbModel, unittest.TestCase):

    prob_model_type = R1G4Model

    test_W1 = create_object_attribute_test("prob_model", "W1", 0.7)
    test_P11_or_P22 = create_object_attribute_test("prob_model", "P11_or_P22", 0.7)
    test_R1 = create_object_attribute_test("prob_model", "R1", 0.7)
    test_R2 = create_object_attribute_test("prob_model", "R2", 0.7)
    test_G1 = create_object_attribute_test("prob_model", "G1", 0.7)
    test_G2 = create_object_attribute_test("prob_model", "G2", 0.7)
    test_G11 = create_object_attribute_test("prob_model", "G11", 0.7)
    test_G12 = create_object_attribute_test("prob_model", "G12", 0.7)
    test_G21 = create_object_attribute_test("prob_model", "G21", 0.7)
    test_G22 = create_object_attribute_test("prob_model", "G22", 0.7)
    test_G31 = create_object_attribute_test("prob_model", "G31", 0.7)
    test_G22 = create_object_attribute_test("prob_model", "G32", 0.7)

    pass # end of class
