#!/usr/bin/python
# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import unittest

from test.test_generic.test_io.test_file_parsers import TestParserMixin
from pyxrd.generic.io.xrd_parsers import CPIParser


__all__ = [
    'TestCPIParser',
]

class TestCPIParser(TestParserMixin, unittest.TestCase):

    parser_class = CPIParser
    file_data = [
        r"""SIETRONICS XRD SCAN
3.01
3.73
0.02
Cu
1,5406
11/10/2012 14:41:24
2,0
08-946 Sample
SCANDATA
60.0000000
50.0000000
40.0000000
30.0000000
20.0000000
10.0000000
5.5106383
18.1276596
8.7446809
-2.6382979
4.9787234
-9.4042553
15.2127660
30.8297872
-1.5531915
13.0638298
-1.3191489
-6.7021277
-18.0851064
-13.4680851
-17.8510638
6.7659574
1.3829787
0.0000000
37.6960784
27.3921569
12.0882353
2.7843137
19.4803922
-11.8235294
4.8725490
21.5686275
-19.7352941
2.9607843
3.6568627
-4.6470588
-6.9509804""",
    ]

    pass # end of class
