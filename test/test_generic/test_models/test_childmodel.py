#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from pyxrd.gtkmvc.model import Observer
from pyxrd.generic.models import ChildModel

__all__ = [
    'TestChildModel',
]

class TestChildModel(unittest.TestCase):

    def setUp(self):
        self.childmodel = ChildModel()

        class ChildObserver(Observer):

            added_recieved = False
            @Observer.observe("added", signal=True)
            def notify_added(self, model, prop_name, info):
                self.added_recieved = True

            removed_recieved = False
            @Observer.observe("removed", signal=True)
            def notify_removed(self, model, prop_name, info):
                self.removed_recieved = True

        self.observer = ChildObserver(model=self.childmodel)

    def tearDown(self):
        self.observer.relieve_model(self.childmodel)
        del self.observer
        del self.childmodel

    def test_not_none(self):
        self.assertIsNotNone(self.childmodel)

    def test_signals(self):
        # Reset flags:
        self.observer.removed_recieved = False
        self.observer.added_recieved = False

        # No parent set, only the added signal is fired,
        self.childmodel.parent = object()

        self.assertFalse(self.observer.removed_recieved)
        self.assertTrue(self.observer.added_recieved)

        # Reset flags:
        self.observer.removed_recieved = False
        self.observer.added_recieved = False

        # Setting a parent when there is one set; both signals should be fired:
        parent = object()
        self.childmodel.parent = parent

        self.assertTrue(self.observer.removed_recieved)
        self.assertTrue(self.observer.added_recieved)

        # Reset flags:
        self.observer.removed_recieved = False
        self.observer.added_recieved = False

        # Setting an identical parent does not fire anything:
        self.childmodel.parent = parent

        self.assertFalse(self.observer.removed_recieved)
        self.assertFalse(self.observer.added_recieved)

        # Reset flags:
        self.observer.removed_recieved = False
        self.observer.added_recieved = False

        # Setting the parent to None when it was set; should only fire the removed signal:
        self.childmodel.parent = None

        self.assertTrue(self.observer.removed_recieved)
        self.assertFalse(self.observer.added_recieved)

    pass # end of class
