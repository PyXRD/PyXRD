# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from .base_parser import BaseParser

class ASCIIParser(BaseParser):
    """
        ASCII Parser
    """
    description = "ASCII data"
    mimetypes = ["text/plain", ]
    can_write = True

    @classmethod
    def get_last_line(cls, f):
        i = -1
        f.seek(0)
        for i, l in enumerate(f):
            pass
        return i + 1, l

    @classmethod
    def write(cls, filename, x, ys, header="", delimiter=",", **kwargs):
        """
            Writes the header to the first line, and will write x, y1, ..., yn
            rows for each column inside the x and ys arguments.
            Header argument should not include a newline, and can be a string or
            any iterable containing strings.
        """
        f = open(filename, 'w')
        if not isinstance(header, basestring): # python 3: ... , str)!
            header = delimiter.join(header) # assume this is an iterable
        f.write(u"%s\n" % header)
        np.savetxt(f, np.insert(ys, 0, x, axis=0).transpose(), fmt="%.8f", delimiter=delimiter)
        f.close()

    pass # end of class
