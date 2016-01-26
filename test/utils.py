#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import time
import mock
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
    
def _mocked_parse_args():
    args = mock.Mock()
    args.script.return_value = True
    args.script.filename = ""
    args.script.debug = False
    return args

def mock_settings():
    from pyxrd.data import settings
    settings._parse_args = mock.Mock(return_value=_mocked_parse_args())
    settings.initialize()
    