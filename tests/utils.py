#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

def create_object_attribute_test(object_name, attribute, value):
    """
        Helper function to create simple attribute setter/getter tests.
    """
    def test_attribute(self):
        obj = getattr(self, object_name)
        setattr(obj, attribute, value)
        self.assertEqual(getattr(obj, attribute), value)
    return test_attribute
