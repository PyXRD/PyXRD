# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.generic.io import get_case_insensitive_glob

from pyxrd.file_parsers.json_parser import JSONParser

from .namespace import project_parsers

@project_parsers.register_parser()
class JSONProjectParser(JSONParser):

    description = "Project file *.PYXRD"
    extensions = get_case_insensitive_glob("*.PYXRD")
    mimetypes = ["application/octet-stream", "application/zip"]


    @classmethod
    def _parse_data(cls, filename, fp, data_objects=None, close=True):
        project = super(JSONProjectParser, cls)._parse_data(filename, fp, data_objects=data_objects, close=close)
        project.filename = filename
        return project

    pass #end of class
