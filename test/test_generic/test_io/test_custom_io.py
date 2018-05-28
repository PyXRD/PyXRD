#!/usr/bin/python
# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os
import unittest
from io import StringIO

from pyxrd.generic.io import storables, Storable

from pyxrd.file_parsers.json_parser import JSONParser

__all__ = [
    'TestParserMixin',
]


def load_data_from_files(*files):
    basepath = os.path.realpath(os.getcwd())
    for fname in files:
        with open(basepath + "/" + fname, 'rb') as f:
            yield f.read()

class TestStorable(unittest.TestCase):

    @storables.register()
    class DummyStorable(Storable):

        __storables__ = [
            "name",
            "data",
            "my_daddy"
        ]

        class Meta(Storable.Meta):
            store_id = "DummyStorable"

        def __init__(self, name, data, my_daddy):
            super(TestStorable.DummyStorable, self).__init__()
            self.name = name
            self.data = data
            self.my_daddy = my_daddy

    def setUp(self):
        self.daddy = self.DummyStorable('Daddy Dummy', list(range(50)), None)
        self.child = self.DummyStorable('Child Dummy', list(range(5)), self.daddy)

    def tearDown(self):
        del self.daddy
        del self.child

    def test_setup(self):
        self.assertNotEqual(self.daddy, None)
        self.assertNotEqual(self.child, None)

    def test_encoding(self):
        self.daddy_dump = self.daddy.dump_object()
        self.child_dump = self.child.dump_object()
        self.assertIn("".join(self.daddy_dump.split()), "".join(self.child_dump.split()))


    def test_decoding(self):

        child_encoded = """
{
    "type": "DummyStorable", 
    "properties": {
        "name": "Child Dummy", 
        "data": [
            0, 
            1, 
            2, 
            3, 
            4
        ], 
        "my_daddy": {
            "type": "DummyStorable", 
            "properties": {
                "name": "Daddy Dummy", 
                "data": [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ], 
                "my_daddy": null
            }
        }
    }
}"""
        f = StringIO(child_encoded)
        decoded_child = JSONParser.parse(f)

        self.assertNotEqual(decoded_child, None)
        self.assertNotEqual(decoded_child.my_daddy, None)

    pass # end of class
