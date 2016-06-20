# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, struct
from io import SEEK_SET, SEEK_CUR

import numpy as np

from pyxrd.generic.io.utils import get_case_insensitive_glob
from pyxrd.generic.utils import u

from ..base_parser import BaseParser
from .namespace import xrd_parsers
from .xrd_parser_mixin import XRDParserMixin

@xrd_parsers.register_parser()
class BrkRAWParser(XRDParserMixin, BaseParser):
    """
        Bruker *.RAW format parser
    """

    description = "Bruker/Siemens Binary V1/V2/V3 *.RAW"
    extensions = get_case_insensitive_glob("*.RAW")
    mimetypes = ["application/octet-stream", ]

    __file_mode__ = "rb"

    @classmethod
    def _clean_bin_str(cls, val):
        return u(str(val).replace("\0", "").strip())

    @classmethod
    def _parse_header(cls, filename, fp, data_objects=None, close=False):
        f = fp

        try:
            basename = u(os.path.basename(filename))
        except:
            basename = None

        # Go to the start of the file
        f.seek(0, SEEK_SET)

        # Read file format version:
        version = str(f.read(4))
        if version == "RAW ":                             version = "RAW1"
        elif version == "RAW2":                           version = "RAW2"
        elif version == "RAW1" and str(f.read(3)) == ".01": version = "RAW3"

        if version == "RAW1":

            # This format does not allow getting the exact number of samples,
            # so start with one and append where needed:
            isfollowed = 1
            num_samples = 0
            while isfollowed > 0:

                twotheta_count = int(struct.unpack("I", f.read(4))[0])
                # Check if this is an early "RAW " formatted file where the
                # "RAW " is repeated for each sample:
                if num_samples > 0 and twotheta_count == int(struct.unpack("I", "RAW ")[0]):
                    twotheta_count = int(struct.unpack("I", f.read(4))[0])

                # Step counting time, 2-theta step size and scanning mode:
                time_step, twotheta_step, scan_mode = struct.unpack("fff", f.read(12)) #@UnusedVariable
                # Skip 4 bytes, and read 2-theta starting position:
                f.seek(4, SEEK_CUR)
                twotheta_min, = struct.unpack("f", f.read(4))
                twotheta_max = twotheta_min + twotheta_step * float(twotheta_count)
                # Skip 12 bytes
                # (contain theta, khi and phi start point for eularian craddles)
                f.seek(12, SEEK_CUR)
                # Read sample name and wavelengths:
                sample_name = cls._clean_bin_str(f.read(32))
                alpha1, alpha2 = struct.unpack("ff", f.read(8))
                # Skip 72 bytes:
                f.seek(72, SEEK_CUR)
                isfollowed, = struct.unpack("I", f.read(4))

                # Get data position and skip for now:
                data_start = f.tell()
                f.seek(twotheta_count * 4, SEEK_CUR)

                # Adapt XRDFile list
                data_objects = cls._adapt_data_object_list(
                    data_objects,
                    num_samples=(num_samples + 1),
                    only_extend=True
                )

                data_objects[num_samples].update(
                    filename=basename,
                    version=version,
                    name=sample_name,
                    time_step=time_step,
                    twotheta_min=twotheta_min,
                    twotheta_max=twotheta_max,
                    twotheta_step=twotheta_step,
                    twotheta_count=twotheta_count,
                    alpha1=alpha1,
                    alpha2=alpha2,
                    data_start=data_start
                )

                num_samples += 1

        elif version == "RAW2":

            # Read number of sample ranges:
            num_samples, = struct.unpack("H", f.read(2))

            # Adapt XRDFile list
            data_objects = cls._adapt_data_object_list(data_objects, num_samples=num_samples)

            # Read sample name:
            f.seek(8, SEEK_SET)
            sample_name = cls._clean_bin_str(f.read(32))
            # Meta-data description, skip for now:
            # description = u(str(f.read(128)).replace("\0", "").strip())
            # date = u(str(f.read(10)).replace("\0", "").strip())
            # time = u(str(f.read(5)).replace("\0", "").strip())

            # Read wavelength information:
            f.seek(148, SEEK_CUR)
            target_type = u(str(f.read(2)).replace("\0", "").strip()) #@UnusedVariable
            alpha1, alpha2, alpha_factor = struct.unpack("fff", f.read(12))

            # Total runtime in seconds: (not used fttb)
            f.seek(8, SEEK_CUR)
            time_total, = struct.unpack("f", f.read(4)) #@UnusedVariable

            # Move to first sample header start:
            f.seek(256, SEEK_SET)

            # Read in per-sample meta data
            for i in range(num_samples):
                header_start = f.tell()
                header_length, twotheta_count = struct.unpack("HH", f.read(4))
                data_start = header_start + header_length

                # Read step size and start angle:
                f.seek(header_start + 12) # = 256 + 4 + 8 skipped bytes
                twotheta_step, twotheta_min = struct.unpack("ff", f.read(8))
                twotheta_max = twotheta_min + twotheta_step * float(twotheta_count)

                # Read up to end of data:
                f.seek(data_start + twotheta_count * 4, SEEK_SET)

                # Update XRDFile object:
                data_objects[i].update(
                    filename=basename,
                    version=version,
                    name=sample_name,
                    twotheta_min=twotheta_min,
                    twotheta_max=twotheta_max,
                    twotheta_step=twotheta_step,
                    twotheta_count=twotheta_count,
                    alpha1=alpha1,
                    alpha2=alpha2,
                    alpha_factor=alpha_factor,
                    data_start=data_start
                )

        elif version == "RAW3":

            # Read file status:    
            f.seek(8, SEEK_SET)       
            file_status = { #@UnusedVariable
                1: "done",
                2: "active",
                3: "aborted",
                4: "interrupted"
            }[int(struct.unpack("I", f.read(4))[0])]

            # Read number of samples inside this file:
            f.seek(12, SEEK_SET)
            num_samples, = struct.unpack("I", f.read(4))

            # Read in sample name:
            f.seek(326, SEEK_SET)
            sample_name =  cls._clean_bin_str(f.read(60))

            # Goniometer radius:
            f.seek(564, SEEK_SET)
            radius = float(struct.unpack("f", f.read(4))[0])

            # Fixed divergence:
            f.seek(568, SEEK_SET)
            divergence = float(struct.unpack("f", f.read(4))[0])

            # Primary soller
            f.seek(576, SEEK_SET)
            soller1 = float(struct.unpack("f", f.read(4))[0])

            # Secondary soller
            f.seek(592, SEEK_SET)
            soller2 = float(struct.unpack("f", f.read(4))[0])

            # Get anode type:
            f.seek(608, SEEK_SET)
            target_type = str(f.read(4)) #@UnusedVariable

            # Get wavelength info:
            f.seek(616, SEEK_SET)
            alpha_average, alpha1, alpha2, beta, alpha_factor = (#@UnusedVariable
                struct.unpack("ddddd", f.read(8 * 5)))

            # Get total recording time:
            f.seek(664, SEEK_SET)
            time_total, = struct.unpack("f", f.read(4)) #@UnusedVariable
            
            # Adapt XRDFile lis & Skip to first block:t
            data_objects = cls._adapt_data_object_list(data_objects, num_samples=num_samples)
            f.seek(712, SEEK_SET)
            
            # Read in per-sample meta data
            for i in range(num_samples):
                # Store the start of the header:
                header_start = f.tell()

                # Get header length
                f.seek(header_start + 0, SEEK_SET)
                header_length, = struct.unpack("I", f.read(4))
                assert header_length == 304, "Invalid format!"
                
                # Get data count and
                f.seek(header_start + 4, SEEK_SET)
                twotheta_count, = struct.unpack("I", f.read(4))
                
                # Get theta start positions
                f.seek(header_start + 8, SEEK_SET)
                theta_min, twotheta_min = struct.unpack("dd", f.read(8 * 2))#@UnusedVariable               

                # Read step size
                f.seek(header_start + 176, SEEK_SET)
                twotheta_step, = struct.unpack("d", f.read(8))

                # Read counting time
                f.seek(header_start + 192, SEEK_SET)
                time_step, = struct.unpack("d", f.read(8))

                # Read the used wavelength
                f.seek(header_start + 240, SEEK_SET)
                alpha_used, = struct.unpack("d", f.read(8))#@UnusedVariable

                # Supplementary header size:
                f.seek(header_start + 256, SEEK_SET)
                supp_headers_size, = struct.unpack("I", f.read(4))
                data_start = header_start + header_length + supp_headers_size

                # Move to the end of the data:
                f.seek(data_start + twotheta_count * 4)
                
                # Calculate last data point
                twotheta_max = twotheta_min + twotheta_step * float(twotheta_count - 0.5)
                
                data_objects[i].update(
                    filename=basename,
                    version=version,
                    name=sample_name,
                    twotheta_min=twotheta_min,
                    twotheta_max=twotheta_max,
                    twotheta_step=twotheta_step,
                    twotheta_count=twotheta_count,
                    alpha1=alpha1,
                    alpha2=alpha2,
                    alpha_factor=alpha_factor,
                    data_start=data_start,
                    radius=radius,
                    soller1=soller1,
                    soller2=soller2,
                    divergence=divergence
                )

        else:
            raise IOError, "Only verson 1, 2 and 3 *.RAW files are supported!"

        if close: f.close()
        return data_objects

    @classmethod
    def _parse_data(cls, filename, fp, data_objects=None, close=False):
        for data_object in data_objects:
            if data_object.data == None:
                data_object.data = []
            
            # Parse data:
            if fp is not None:
                if data_object.version in ("RAW1", "RAW2", "RAW3"):
                    fp.seek(data_object.data_start)
                    n = 0
                    while n < data_object.twotheta_count:
                        y, = struct.unpack("f", fp.read(4))
                        x = data_object.twotheta_min + data_object.twotheta_step * float(n + 0.5)
                        data_object.data.append([x,y])
                        n += 1
                else:
                    raise IOError, "Only verson 1, 2 and 3 *.RAW files are supported!"


            data_object.data = np.array(data_object.data)

        if close: fp.close()
        return data_objects

    pass # end of class
