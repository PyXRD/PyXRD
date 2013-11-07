#!/usr/bin/python
# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import shutil
import os
import tempfile

import unittest

from pyxrd.generic.exceptions import AlreadyRegistered, NotRegistered
from pyxrd.generic.io.data_registry import DataRegistry

__all__ = [
    'TestDataRegistry',
]


class TestDataRegistry(unittest.TestCase):

    def setUp(self):

        self.base_temp_dir = tempfile.mkdtemp()

        self.dirs = [
            ("TEST1", os.path.join(self.base_temp_dir, "test1/"), None),
            ("TEST2", "test2/", "TEST1"),
        ]
        self.files = [
            ("ROOTFILE", "root.txt", None),
            ("TEST1_FILE", "test1file.txt", "TEST1"),
            ("TEST2_FILE", "test2file.txt", "TEST2"),
        ]
        self.data_reg = DataRegistry(dirs=self.dirs, files=self.files)
        pass

    def tearDown(self):
        shutil.rmtree(self.base_temp_dir)
        del self.data_reg
        pass

    def test_exceptions(self):
        with self.assertRaises(NotRegistered):
            self.data_reg.get_directory_path("TEST3")

        with self.assertRaises(AlreadyRegistered):
            self.data_reg.register_data_directory("TEST1", "false_test1/", None)

    def test_iter(self):
        for path in self.data_reg.get_all_files():
            self.assertNotIn(path, [None, ""])

    pass # end of class
