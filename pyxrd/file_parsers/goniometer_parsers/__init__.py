# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import zipfile

from pyxrd.generic.io import get_case_insensitive_glob, COMPRESSION

from pyxrd.file_parsers.json_parser import JSONParser
from pyxrd.file_parsers.registry import ParserNamespace

goniometer_parsers = ParserNamespace("GoniometerParsers")

@goniometer_parsers.register_parser()
class JSONGoniometerParser(JSONParser):

    description = "Goniometer file *.GON"
    extensions = get_case_insensitive_glob("*.GON")
    mimetypes = ["application/octet-stream", "application/zip"]

    pass #end of class
