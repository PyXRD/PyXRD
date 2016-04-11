# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os
from datetime import date

import numpy as np

from pyxrd.generic.io.utils import get_case_insensitive_glob
from pyxrd.generic.utils import u

from ..base_parser import BaseParser
from .namespace import xrd_parsers
from .xrd_parser_mixin import XRDParserMixin

@xrd_parsers.register_parser()
class CPIParser(XRDParserMixin, BaseParser):
    """
        ASCII Sietronics *.CPI format parser
    """

    description = "Sietronics *.CPI"
    extensions = get_case_insensitive_glob("*.CPI", "*.CPD", "*.CPS")

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
            filename=basename,
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
    def _parse_data(cls, filename, fp, data_objects=None, close=False):
        f = fp

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

    @classmethod
    def write(cls, filename, x, ys, radiation="Cu", wavelength=1.54060, tps=48.0, sample="", **kwargs):
        """
            Writes a SIETRONICS cpi text file. x and ys should be numpy arrays.
        """
        start_angle = x[0]
        end_angle = x[-1]
        step_size = (end_angle - start_angle) / (x.size - 1)
        with open(filename, 'w') as f:
            f.write("SIETRONICS XRD SCAN\n")
            f.write("%.4f\n" % start_angle)
            f.write("%.4f\n" % end_angle)
            f.write("%.4f\n" % step_size)
            f.write("%s\n" % radiation)
            f.write("%.5f\n" % wavelength)
            f.write("%s\n" % date.today().strftime('%d/%m/%y %H:%M:%S'))
            f.write("%.1f\n" % tps)
            f.write("%s\n" % sample)
            f.write("SCANDATA\n")
            for y in ys[0, :]:
                f.write("%.7f\n" % y)

    pass # end of class
