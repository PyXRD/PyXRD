# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.generic.io import get_case_insensitive_glob

from pyxrd.project.importing import create_project_from_sybilla_xml

from ..base_parser import BaseParser
from ..xml_parser_mixin import XMLParserMixin
from .namespace import project_parsers

@project_parsers.register_parser()
class SybillaProjectParser(XMLParserMixin, BaseParser):

    description = "Sybilla XML files"
    extensions = get_case_insensitive_glob("*.XML")
    mimetypes = ["application/xml", "text/xml"]

    @classmethod
    def parse(cls, fp, data_objects=None, close=True):
        """
            This method parses the file and return a list of DataObjects
            with both header and data properties filled in accordingly.
            The filename argument is always required. If no file object is passed
            as keyword argument, it only serves as a label. Otherwise a new file
            object is created.
            File objects are closed unless close is set to False.
            Existing DataObjects can be passed as well and will then 
            be used instead of creating new ones.
        """
        filename, fp, close = cls._get_file(fp, close=close)
        data_objects = create_project_from_sybilla_xml(filename)
        if close: fp.close()
        return data_objects

    pass #end of class
