#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import time
import gtk

def create_object_attribute_test(object_name, attribute, value):
    """
        Helper function to create simple attribute setter/getter tests.
    """
    def test_attribute(self):
        obj = getattr(self, object_name)
        setattr(obj, attribute, value)
        self.assertEqual(getattr(obj, attribute), value)
    return test_attribute

# Stolen from Kiwi
def refresh_gui(delay=0):
    while gtk.events_pending():
        gtk.main_iteration_do(block=False)
    time.sleep(delay)
