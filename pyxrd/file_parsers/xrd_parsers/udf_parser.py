# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os

import numpy as np

from pyxrd.generic.io.utils import get_case_insensitive_glob
from pyxrd.generic.utils import u

from ..base_parser import BaseParser
from .namespace import xrd_parsers
from .xrd_parser_mixin import XRDParserMixin

@xrd_parsers.register_parser()
class UDFParser(XRDParserMixin, BaseParser):
    """
        ASCII Philips *.UDF format
    """

    description = "Philips *.UDF"
    extensions = get_case_insensitive_glob("*.UDF")

    @classmethod
    def _parse_header(cls, filename, fp, data_objects=None, close=False):
        f = fp
        try:
            basename = u(os.path.basename(filename))
        except:
            basename = None
        # Adapt XRDFile list
        data_objects = cls._adapt_data_object_list(data_objects, num_samples=1)

        # Move to the start of the file
        f.seek(0)

        # Go over the header:
        header_dict = {}

        for lineno, line in enumerate(f):
            # Start of data after this line:
            if line.strip() == "RawScan":
                data_start = f.tell()
                break
            else:
                # Break header line into separate parts, and strip trailing whitespace:
                parts = map(str.strip, line.split(','))

                # If length is shorter then three, somethings wrong
                if len(parts) < 3:
                    raise IOError, "Header of UDF file is malformed at line %d" % lineno

                # Handle some of the header's arguments manually, the rest is
                # just passed to the data object as keyword arguments...
                if parts[0] == "SampleIdent":
                    name = parts[1]
                elif parts[0] == "DataAngleRange":
                    twotheta_min = float(parts[1])
                    twotheta_max = float(parts[2])
                elif parts[0] == "ScanStepSize":
                    twotheta_step = float(parts[1])

                # TODO extract other keys and replace with default names
                header_dict[parts[0]] = ','.join(parts[1:-1])

        twotheta_count = int((twotheta_max - twotheta_min) / twotheta_step)

        data_objects[0].update(
            filename=basename,
            name=name,
            twotheta_min=twotheta_min,
            twotheta_max=twotheta_max,
            twotheta_step=twotheta_step,
            twotheta_count=twotheta_count,
            data_start=data_start,
            **header_dict
        )

        if close: f.close()
        return data_objects

    @classmethod
    def _parse_data(cls, filename, fp, data_objects=None, close=False):
        f = fp

        # UDF files are singletons, so no need to iterate over the list,
        # there is only one data object instance:
        if data_objects[0].data == None:
            data_objects[0].data = []

        if f is not None:
            f.seek(data_objects[0].data_start)
            n = 0
            last_value_reached = False
            while n <= data_objects[0].twotheta_count and not last_value_reached:
                parts = map(str.strip, f.readline().split(','))
                for part in parts:
                    # Last value ends with a slash:
                    if part.endswith('/'):
                        part = part[:-1] # remove the ending "/"
                        last_value_reached = True
                    n += 1
                    data_objects[0].data.append([ float(data_objects[0].twotheta_min + data_objects[0].twotheta_step * n), float(part) ])

        data_objects[0].data = np.array(data_objects[0].data)

        if close: f.close()
        return data_objects

    pass # end of class
