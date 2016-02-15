# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import zipfile

from pyxrd.generic.io import get_case_insensitive_glob, COMPRESSION

from pyxrd.file_parsers.json_parser import JSONParser

from .namespace import atom_type_parsers

@atom_type_parsers.register_parser()
class JSONAtomTypeParser(JSONParser):
    """
        Atomic scattering factors JSON file parser
    """

    description = "Atom types JSON file *.ZTL"
    extensions = get_case_insensitive_glob("*.ZTL")
    mimetypes = ["application/octet-stream", "application/zip"]

    __file_mode__ = "rb"

    @classmethod
    def _parse_header(cls, filename, fp, data_objects=None, close=False):
        return data_objects # just pass it on, nothing to do

    @classmethod
    def write(cls, filename, items, props):
        """
            Saves multiple AtomTypes to a single (JSON) file.
        """
        with zipfile.ZipFile(filename, 'w', compression=COMPRESSION) as zfile:
            for i, atom_type in enumerate(items):
                zfile.writestr("%d###%s" % (i, atom_type.uuid), atom_type.dump_object())

    pass # end of class
