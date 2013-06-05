#!/usr/bin/python
# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from generic.exceptions import AlreadyRegistered, NotRegistered
from generic.io.data_registry import DataRegistry

__all__ = [
    'TestDataRegistry',
]


class TestDataRegistry(unittest.TestCase):

    def setUp(self):
        self.dirs = [
            ("TEST1",        "test1/",      None),
            ("TEST2",        "test2/",      "TEST1"),
        ]
        self.files = [
            ("ROOTFILE",    "root.txt",       None),
            ("TEST1_FILE",  "test1file.txt",  "TEST1"),
            ("TEST2_FILE",  "test2file.txt",  "TEST2"),
        ]
        self.data_reg = DataRegistry(dirs=self.dirs, files=self.files)
        pass
        
    def tearDown(self):
        del self.data_reg
        pass
        
    def test_exceptions(self):
        with self.assertRaises(AlreadyRegistered):
            self.data_reg.register_data_directory("TEST1", "false_test1/", None)

        with self.assertRaises(NotRegistered):
            self.data_reg.get_directory_path("TEST3")
        
    def test_dirs(self):
        test1 = self.data_reg.get_directory_path("TEST1")
        self.assertEqual(test1, "/test1/")
        self.data_reg.set_base_directory("/base_dir")
        test1 = self.data_reg.get_directory_path("TEST1")
        self.assertEqual(test1, "/base_dir/test1/")
        test2 = self.data_reg.get_directory_path("TEST2")
        self.assertEqual(test2, "/base_dir/test1/test2/")

    def test_dirs(self):
        self.data_reg.set_base_directory("")
        rootfile = self.data_reg.get_file_path("ROOTFILE")
        self.assertEqual(rootfile, "/root.txt")
        self.data_reg.set_base_directory("/base_dir")
        test1_file = self.data_reg.get_file_path("TEST1_FILE")
        self.assertEqual(test1_file, "/base_dir/test1/test1file.txt")
        test2_file = self.data_reg.get_file_path("TEST2_FILE")
        self.assertEqual(test2_file, "/base_dir/test1/test2/test2file.txt")
        
    def test_iter(self):
        for path in self.data_reg.get_all_files():
            self.assertNotIn(path, [None, ""])
        
    pass #end of class
