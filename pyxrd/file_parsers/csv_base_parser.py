# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import csv

from .ascii_parser import ASCIIParser

class CSVBaseParser(ASCIIParser):
    """
        CSV parser base functionality
    """

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
    def parse_raw_line(cls, line, conv, **fmt_params):
        """ Parses a single raw line (read as a string) """
        fmt_params = dict(cls.default_fmt_params, **fmt_params)
        for row in csv.reader([line, ], **fmt_params):
            return map(conv, row)
            break # stop after first 'line' (there should only be one anyway)

    @classmethod
    def sniff(cls, f, **fmt_params):
        """ CSV Dialect guessing - f needs to be a file object! """
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
        return dict(default_fmt_params, **fmt_params)

    pass # end of class
