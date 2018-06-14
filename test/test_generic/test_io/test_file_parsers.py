#!/usr/bin/python
# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, unittest

from pyxrd.file_parsers.base_parser import BaseParser

__all__ = [
    'TestParserMixin',
]


def load_data_from_files(*files):
    basepath = os.path.realpath(os.getcwd())
    for fname in files:
        with open(basepath + "/" + fname, 'rb') as fp:
            yield fp

class BaseTestParsers(object):

    class BaseTestParser(unittest.TestCase):

        parser_class = BaseParser
        file_data = [
            "",
        ]

        def test_description(self):
            self.assertNotEqual(self.parser_class.description, "")

        def test_filters(self):
            self.assertIsNotNone(self.parser_class.file_filter)

        def test_parsing(self):
            for fp in self.file_data:
                data_objects = self.parser_class.parse(fp)
                self.assertGreater(len(data_objects), 0)

        # TODO:
        # - check arguments such as close.
