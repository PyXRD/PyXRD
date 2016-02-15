# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import zipfile

from pyxrd.generic.io import get_case_insensitive_glob, COMPRESSION

from pyxrd.file_parsers.json_parser import JSONParser
from pyxrd.file_parsers.registry import ParserNamespace

phase_parsers = ParserNamespace("PhaseParsers")

@phase_parsers.register_parser()
class JSONPhaseParser(JSONParser):

    description = "Phase file *.PHS"
    extensions = get_case_insensitive_glob("*.PHS")
    mimetypes = ["application/octet-stream", "application/zip"]

    pass #end of class
