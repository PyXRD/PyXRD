# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.generic.io.file_parsers import create_group_parser

################################################################################
#   xrd namespace parsers:
################################################################################

from rd_parser import RDParser
from udf_parser import UDFParser
from csv_parser import CSVParser
from brk_raw_parser import BrkRAWParser
from cpi_parser import CPIParser

XRDParser = create_group_parser(
    "XRDParser",
    RDParser, UDFParser, CSVParser, BrkRAWParser, CPIParser,
    namespace="xrd"
)

__ALL__ = [
    "RDParser",
    "CSVParser",
    "BrkRAWParser",
    "CPIParser",
    "XRDParser",
]
