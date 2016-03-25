# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)
import json
import zipfile
import types
import os

from shutil import move
from traceback import format_exc

from pyxrd.file_parsers.base_parser import BaseParser
from pyxrd.generic.io.json_codec import PyXRDDecoder, PyXRDEncoder
from pyxrd.generic.io.custom_io import storables, COMPRESSION

from pyxrd.generic.io.utils import unicode_open

class JSONParser(BaseParser):
    """
        PyXRD Object JSON Parser
    """

    description = "PyXRD Object JSON"
    mimetypes = ["application/octet-stream", "application/zip"]

    __file_mode__ = "r"

    @classmethod
    def _parse_header(cls, filename, fp, data_objects=None, close=False):
        return data_objects # just pass it on, nothing to do

    @classmethod
    def _parse_data(cls, filename, fp, data_objects=None, close=True):
        f = fp
        try: # Assume filename is a path
            pre_pos = f.tell()
            is_zipfile = zipfile.is_zipfile(f)
            f.seek(pre_pos)
            if is_zipfile: # ZIP files
                    if filename is not None:
                        zf = zipfile.ZipFile(filename, cls.__file_mode__)
                    else:
                        f.seek(0)
                        zf = zipfile.ZipFile(f, cls.__file_mode__)

                    namelist = zf.namelist()

                    if 'content' in namelist: # Multi-part object
                        obj = None
                        decoder = json.JSONDecoder()

                        # Parse the content file
                        #with zf.open('content') as cf:
                        #    obj = decoder.decode(cf.read())
                        cf = zf.open('content', cls.__file_mode__)
                        obj = decoder.decode(cf.read())
                        cf.close()


                        # Make sure we have a dict at this point
                        if not hasattr(obj, "update"):
                            raise RuntimeError, "Decoding a multi-part JSON object requires the root to be a dictionary object!"

                        # Parse all the other files, and set accordingly in the content dict
                        for sub_name in namelist:
                            if sub_name != "content":
                                zpf = zf.open(sub_name, cls.__file_mode__) #with zf.open(sub_name) as zpf:
                                obj["properties"][sub_name] = decoder.decode(zpf.read())
                                zpf.close()

                        # Now parse the JSON dict to a Python object
                        data_objects = PyXRDDecoder(mapper=storables).__pyxrd_decode__(obj) or obj

                    else: # Multiple objects
                        data_objects = []
                        for sub_name in namelist:
                            zpf = zf.open(sub_name, cls.__file_mode__) #with zf.open(sub_name) as zpf:
                            data_objects.append(cls.parse(zpf))
                            zpf.close()
                    zf.close()
            else: # REGULAR files
                data_objects = PyXRDDecoder(mapper=storables).decode(f.read()) # json.load(f, cls=PyXRDDecoder, mapper=storables)
        except Exception as error: # Maybe filename is a file-like object?
            logger.debug("Handling run-time error: %s" % error)
            tb = format_exc()
            try:
                data_objects = PyXRDDecoder.decode_file(f, mapper=storables)
            except:
                print tb
                raise # re-raise last error, filename is something weird

        return data_objects
        if close: f.close()

    @staticmethod
    def write(obj, file, zipped=False): # @ReservedAssignment
        """
        Saves the output from dump_object() to `filename`, optionally zipping it.
        File can be either a filename or a file-like object. If it is a filename
        extra precautions are taken to prevent malformed data overwriting a good
        file. With file objects this is not the case.
        """
        filename = None
        if isinstance(file, types.StringTypes):
            # We have a filename, not a file object
            filename = file
            # Create temporary filenames for output, and a backup filename if
            # the file already exists.
            file = filename + ".tmp" # @ReservedAssignment
            backup_name = filename + "~"
        try:
            if zipped:
                # Try to safe the file as a zipfile:
                with zipfile.ZipFile(file, mode="w", compression=COMPRESSION) as f:
                    for partname, json_object in obj.to_json_multi_part():
                        f.writestr(partname, PyXRDEncoder.dump_object(json_object))
            else:
                # Regular text file:
                if filename is not None:
                    with unicode_open(file, 'w') as f:
                        PyXRDEncoder.dump_object_to_file(obj, f)
                else:
                    PyXRDEncoder.dump_object_to_file(obj, file)
        except:
            # In case saving fails, remove the temporary file:
            if filename is not None and os.path.exists(file):
                os.remove(file)
            raise

        if filename is not None:
            # If target file exists, back it up:
            if os.path.exists(filename):
                move(filename, backup_name)
            # Rename temporary saved file:
            move(file, filename)

    pass # end of class
