# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.generic.io.utils import get_case_insensitive_glob

from pyxrd.file_parsers.registry import ParserNamespace
from pyxrd.file_parsers.xrd_parsers.csv_parser import GenericXYCSVParser

wld_parsers = ParserNamespace("WLDParsers")

@wld_parsers.register_parser()
class WLDParser(GenericXYCSVParser):
    """
        ASCII *.WLD format parser
    """

    description = "Wavelength distribution file"
    extensions = get_case_insensitive_glob("*.WLD")

    pass # end of class