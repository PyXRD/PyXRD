#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

def run_all_tests(*args, **kwargs):
    all_tests = get_all_tests()
    unittest.TextTestRunner().run(all_tests)

def get_all_tests():
    return unittest.TestLoader().discover('.')
