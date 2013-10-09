#!/usr/bin/python
# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.test_generic.test_io.test_file_parsers import TestParserMixin
from pyxrd.generic.io.xrd_parsers import UDFParser


__all__ = [
    'TestUDFParser',
]

class TestUDFParser(TestParserMixin, unittest.TestCase):

    parser_class = UDFParser
    file_data = [
        r"""SampleIdent,Sample5 ,/
Title1,Dat2rit program ,/
Title2,Sample5 ,/
DataAngleRange,   5.0000, 5.6400,/
ScanStepSize,     0.020,/
RawScan
    8000,    7000,    6000,    5000,    4000,    3000,    2000,    1000
    800,     700,     600,     500,     400,     300,     200,     100
    80,      70,      60,      50,      40,      30,      20,      10
    8,       7,       6,       5,       4,       3,       2,       1
    0/""",
    ]

    pass # end of class
