#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from generic.models import PyXRDModel

__all__ = [
    'TestPyXRDModel',
]

class TestPyXRDModel(unittest.TestCase):

    def setUp(self):
        self.pyxrdmodel = PyXRDModel()

    def tearDown(self):
        del self.pyxrdmodel
        
    def test_not_none(self):
        self.assertIsNotNone(self.pyxrdmodel)
        
    #TODO everything else
        
    pass #end of class
