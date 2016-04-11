# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, csv

import numpy as np

from pyxrd.generic.io.utils import get_case_insensitive_glob
from pyxrd.generic.utils import u

from ..csv_base_parser import CSVBaseParser
from .namespace import xrd_parsers
from .xrd_parser_mixin import XRDParserMixin

class GenericXYCSVParser(XRDParserMixin, CSVBaseParser):
    """
        Generic xy-data CSV parser. Does not care about extensions. 
        Should be sub-classed!
    """

    description = "ASCII XY data"

    default_fmt_params = {
        "delimiter": ',',
        "doublequote": True,
        "escapechar": None,
        "quotechar": "\"",
        "quoting": csv.QUOTE_MINIMAL,
        "skipinitialspace": True,
        "strict": False
    }

    @classmethod
    def _parse_header(cls, filename, fp, data_objects=None, close=False, **fmt_params):
        fmt_params = dict(cls.default_fmt_params, **fmt_params)
        f = fp

        # Goto start of file
        f.seek(0)

        # Get base filename:
        try:
            basename = u(os.path.basename(filename))
        except:
            basename = None

        # Read in the first and last data line and put the file cursor back
        # at its original position
        header = f.readline().strip()
        data_start_pos = f.tell()
        first_line = f.readline().strip()
        twotheta_count, last_line = cls.get_last_line(f)
        last_line = last_line.strip()
        f.seek(data_start_pos)

        # Extract the data from the first & last data lines:
        first_line_vals = cls.parse_raw_line(first_line, float, **fmt_params)
        last_line_vals = cls.parse_raw_line(last_line, float, **fmt_params)
        num_samples = len(first_line_vals) - 1 # first column is 2-theta
        twotheta_min = first_line_vals[0]
        twotheta_max = last_line_vals[0]
        twotheta_step = int((twotheta_max - twotheta_min) / twotheta_count)

        # Parse the header line:
        sample_names = cls.parse_raw_line(header, lambda s: s, **fmt_params)[1:]
        if len(sample_names) < num_samples:
            sample_names.extend([""] * (num_samples - len(sample_names)))
        if len(sample_names) > num_samples:
            sample_names = sample_names[:num_samples]

        # Adapt DataObject list
        data_objects = cls._adapt_data_object_list(data_objects, num_samples=num_samples)

        # Fill in header info:
        for i, sample_name in enumerate(sample_names):
            data_objects[i].update(
                filename=basename,
                name=sample_name,
                twotheta_min=twotheta_min,
                twotheta_max=twotheta_max,
                twotheta_step=twotheta_step,
                twotheta_count=twotheta_count
            )

        if close: f.close()
        return data_objects
    @classmethod
    def _parse_data(cls, filename, fp, data_objects=None, close=False, **fmt_params):
        f = fp

        if f is not None:
            for row in csv.reader(f, **fmt_params):
                if row:
                    data = map(float, row)
                    x, ay = data[0], data[1:] # ay contains columns with y values
                    for data_object, y in zip(data_objects, ay):
                        if getattr(data_object, "data", None) is None:
                            data_object.data = []
                        data_object.data.append([x, y])

            for data_object in data_objects:
                data_object.data = np.array(data_object.data)

        if close: f.close()
        return data_objects

    @classmethod
    def parse(cls, fp, data_objects=None, close=True, **fmt_params):
        """
            Files are sniffed for the used csv dialect, but an optional set of
            formatting parameters can be passed that will override the sniffed
            parameters.
        """
        filename, f, close = cls._get_file(fp, close=close)

        # Guess dialect:
        fmt_params = cls.sniff(f, **fmt_params)

        # Parse header:
        data_objects = cls._parse_header(filename, f, data_objects=data_objects, **fmt_params)

        # Parse data:
        data_objects = cls._parse_data(filename, f, data_objects=data_objects, **fmt_params)

        if close: f.close()
        return data_objects

    pass # end of class

@xrd_parsers.register_parser()
class CSVParser(GenericXYCSVParser):
    """
        ASCII *.DAT, *.CSV and *.TAB format parser
    """

    description = "ASCII XRD data"
    extensions = get_case_insensitive_glob("*.DAT", "*.CSV", "*.TAB")

    pass # end of class
