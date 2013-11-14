# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os

import numpy as np

from pyxrd.generic.io.file_parsers import BaseParser, register_parser
from pyxrd.generic.io.utils import get_case_insensitive_glob
from pyxrd.generic.utils import u

from .xrd_parser_mixin import XRDParserMixin

@register_parser()
class CPIParser(XRDParserMixin, BaseParser):
    """
        ASCII Sietronics *.CPI format parser
    """
    description = "Sietronics *.CPI"
    namespace = "xrd"
    extensions = get_case_insensitive_glob("*.CPI", "*.CPD", "*.CPS")

    @classmethod
    def parse_header(cls, filename, f=None, data_objects=None, close=False):
        filename, f, close = cls._get_file(filename, f=f, close=close)

        # Adapt XRDFile list
        data_objects = cls._adapt_data_object_list(data_objects, num_samples=1)

        # Move to the start of the file
        f.seek(0)
        # Skip a line: file type header
        f.readline()
        # Read data limits
        twotheta_min = float(f.readline().replace(",", ".").strip())
        twotheta_max = float(f.readline().replace(",", ".").strip())
        twotheta_step = float(f.readline().replace(",", ".").strip())
        twotheta_count = int((twotheta_max - twotheta_min) / twotheta_step)
        # Read target element name
        target_type = f.readline()
        # Read wavelength
        alpha1 = float(f.readline().replace(",", ".").strip())
        # Read up to SCANDATA and keep track of the line before,
        # it contains the sample description
        name = ""
        while True:
            line = f.readline().strip()
            if line == "SCANDATA" or line == "":
                data_start = f.tell()
                break;
            else:
                name = line

        data_objects[0].update(
            filename=u(os.path.basename(filename)),
            name=name,
            target_type=target_type,
            alpha1=alpha1,
            twotheta_min=twotheta_min,
            twotheta_max=twotheta_max,
            twotheta_step=twotheta_step,
            twotheta_count=twotheta_count,
            data_start=data_start,
        )

        if close: f.close()
        return data_objects

    @classmethod
    def parse_data(cls, filename, f=None, data_objects=None, close=False):
        filename, f, close = cls._get_file(filename, f=f, close=close)

        data_objects = cls.parse_header(filename, f=f, data_objects=data_objects)

        # CPI files are singletons, so no need to iterate over the list,
        # there is only one data object instance:
        if data_objects[0].data == None:
            data_objects[0].data = []

        if f is not None:
            f.seek(data_objects[0].data_start)
            n = 0
            while n <= data_objects[0].twotheta_count:
                line = f.readline().strip("\n").replace(",", ".")
                if line != "":
                    data_objects[0].data.append([ float(data_objects[0].twotheta_min + data_objects[0].twotheta_step * n), float(line) ])
                n += 1

        data_objects[0].data = np.array(data_objects[0].data)

        if close: f.close()
        return data_objects

    pass # end of class
