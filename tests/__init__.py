#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

def run_all_tests(*args, **kwargs):
    all_tests = unittest.TestLoader().discover('.')
    unittest.TextTestRunner().run(all_tests)
