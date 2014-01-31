#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from .base import AbstractTestProbModel

from test.utils import create_object_attribute_test

from pyxrd.probabilities.models.R0models import *
import unittest

__all__ = [
    'TestR0G1Model',
    'TestR0G2Model',
    'TestR0G3Model',
    'TestR0G4Model',
    'TestR0G5Model',
    'TestR0G6Model'
]

class TestR0G1Model(AbstractTestProbModel, unittest.TestCase):

    prob_model_type = R0G1Model

    pass # end of class

class TestR0G2Model(AbstractTestProbModel, unittest.TestCase):

    prob_model_type = R0G2Model

    test_F1 = create_object_attribute_test("prob_model", "F1", 0.7)

    pass # end of class

class TestR0G3Model(AbstractTestProbModel, unittest.TestCase):

    prob_model_type = R0G3Model

    test_F1 = create_object_attribute_test("prob_model", "F1", 0.7)
    test_F2 = create_object_attribute_test("prob_model", "F2", 0.7)

    pass # end of class

class TestR0G4Model(AbstractTestProbModel, unittest.TestCase):

    prob_model_type = R0G4Model

    test_F1 = create_object_attribute_test("prob_model", "F1", 0.7)
    test_F2 = create_object_attribute_test("prob_model", "F2", 0.7)
    test_F3 = create_object_attribute_test("prob_model", "F3", 0.7)

    pass # end of class

class TestR0G5Model(AbstractTestProbModel, unittest.TestCase):

    prob_model_type = R0G5Model

    test_F1 = create_object_attribute_test("prob_model", "F1", 0.7)
    test_F2 = create_object_attribute_test("prob_model", "F2", 0.7)
    test_F3 = create_object_attribute_test("prob_model", "F3", 0.7)
    test_F4 = create_object_attribute_test("prob_model", "F4", 0.7)


    pass # end of class

class TestR0G6Model(AbstractTestProbModel, unittest.TestCase):

    prob_model_type = R0G6Model

    test_F1 = create_object_attribute_test("prob_model", "F1", 0.7)
    test_F2 = create_object_attribute_test("prob_model", "F2", 0.7)
    test_F3 = create_object_attribute_test("prob_model", "F3", 0.7)
    test_F4 = create_object_attribute_test("prob_model", "F4", 0.7)
    test_F5 = create_object_attribute_test("prob_model", "F5", 0.7)

    pass # end of class
