#!/usr/bin/python
# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.test_generic.test_io.test_file_parsers import TestParserMixin, load_data_from_files
from pyxrd.generic.io.xrd_parsers import BrkRAWParser


__all__ = [
    'TestRAWParser',
]

class TestRAWParser(TestParserMixin, unittest.TestCase):

    parser_class = BrkRAWParser
    file_data = load_data_from_files(
        "test/test_generic/test_io/test_xrd_parsers/brk_raw1.raw",
        "test/test_generic/test_io/test_xrd_parsers/brk_raw2.raw"
    )

    pass # end of class
