# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, csv

import numpy as np

from pyxrd.generic.io.file_parsers import ASCIIParser, register_parser
from pyxrd.generic.io.utils import get_case_insensitive_glob
from pyxrd.generic.utils import u

from .xrd_parser_mixin import XRDParserMixin

@register_parser()
class CSVParser(XRDParserMixin, ASCIIParser):
    """
        ASCII *.DAT, *.CSV and *.TAB format parser
    """

    namespace = "xrd"
    description = "ASCII XRD data"
    extensions = get_case_insensitive_glob("*.DAT", "*.CSV", "*.TAB")

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
    def parse_line(cls, line, conv, **fmt_params):
        fmt_params = dict(cls.default_fmt_params, **fmt_params)
        for row in csv.reader([line, ], **fmt_params):
            return map(conv, row)
            break # stop after first 'line' (there is only one anyway)

    @classmethod
    def parse_header(cls, filename, f=None, data_objects=None, close=False, **fmt_params):
        fmt_params = dict(cls.default_fmt_params, **fmt_params)
        filename, f, close = cls._get_file(filename, f=f, close=close)

        # Goto start of file
        f.seek(0)

        # Get base filename:
        basename = u(os.path.basename(filename))

        # Read in the first and last data line and put the file cursor back
        # at its original position
        header = f.readline().strip()
        data_start_pos = f.tell()
        first_line = f.readline().strip()
        twotheta_count, last_line = cls.get_last_line(f)
        last_line = last_line.strip()
        f.seek(data_start_pos)

        # Extract the data from the first & last data lines:
        first_line_vals = cls.parse_line(first_line, float, **fmt_params)
        last_line_vals = cls.parse_line(last_line, float, **fmt_params)
        num_samples = len(first_line_vals) - 1 # first column is 2-theta
        twotheta_min = first_line_vals[0]
        twotheta_max = last_line_vals[0]
        twotheta_step = int((twotheta_max - twotheta_min) / twotheta_count)

        # Parse the header line:
        sample_names = cls.parse_line(header, lambda s: s, **fmt_params)[1:]
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
    def parse_data(cls, filename, f=None, data_objects=None, close=False, **fmt_params):
        filename, f, close = cls._get_file(filename, f=f, close=close)

        data_objects = cls.parse_header(filename, f=f, data_objects=data_objects, **fmt_params)

        if f is not None:
            for row in csv.reader(f, **fmt_params):
                if row:
                    data = map(float, row)
                    x, ay = data[0], data[1:] # ay contains columns with y values
                    for data_object, y in zip(data_objects, ay):
                        if data_object.data == None:
                            data_object.data = []
                        data_object.data.append([x, y])

            for data_object in data_objects:
                data_object.data = np.array(data_object.data)

        if close: f.close()
        return data_objects

    @classmethod
    def parse(cls, filename, f=None, data_objects=None, close=True, **fmt_params):
        """
            Files are sniffed for the used csv dialect, but an optional set of
            formatting parameters can be passed that will override the sniffed
            parameters.
        """
        filename, f, close = cls._get_file(filename, f=f, close=close)

        # Guess dialect, and then:
        # - update default class dialect parameters with the sniffed dialect
        # - override the obtained dialect with any user-passed parameters
        dialect = None
        if f is not None:
            try:
                # skip (potential) header as these are sometimes formatted differently
                f.readline()
                dialect = csv.Sniffer().sniff(f.read(1024))
                f.seek(0)
            except:
                pass # ignore failures
        default_fmt_params = dict(cls.default_fmt_params, **{
            param: getattr(dialect, param) for param in cls.default_fmt_params.keys() if hasattr(dialect, param)
        })
        fmt_params = dict(default_fmt_params, **fmt_params)

        data_objects = cls.parse_header(filename, f=f, data_objects=data_objects, **fmt_params)
        data_objects = cls.parse_data(filename, f=f, data_objects=data_objects, **fmt_params)
        if close: f.close()
        return data_objects

    pass # end of class
