#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

__all__ = [
    'AbstractTestProbModel',
]

class AbstractTestProbModel():

    prob_model = None
    prob_model_type = None

    def setUp(self):
        self.prob_model = self.prob_model_type()

    def tearDown(self):
        del self.prob_model

    def test_not_none(self):
        self.assertIsNotNone(self.prob_model)

    pass # end of class
