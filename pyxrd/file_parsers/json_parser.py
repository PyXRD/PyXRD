# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from distutils.version import LooseVersion

import json
import zipfile
import os, io

from shutil import move

from pyxrd.__version import __version__

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
    def _get_file(cls, fp, close=None):
        """
            Returns a three-tuple:
            filename, zipfile-object, close
        """
        if isinstance(fp, str): # fp is a filename
            filename = fp
            if zipfile.is_zipfile(filename):
                fp = zipfile.ZipFile(filename, cls.__file_mode__)
            else:
                fp = unicode_open(filename, cls.__file_mode__)
            close = True if close is None else close
        else: # fp is a file pointer
            filename = getattr(fp, 'name', None)
            if zipfile.is_zipfile(fp):
                fp = zipfile.ZipFile(fp)
            close = False if close is None else close
        return filename, fp, close

    @classmethod
    def _parse_header(cls, filename, fp, data_objects=None, close=False):
        return data_objects # just pass it on, nothing to do

    @classmethod
    def _parse_data(cls, filename, fp, data_objects=None, close=True):
        # At this point filename is just there for information; fp can safely be
        # assumed to be a file pointer - if not, not our problem
        is_zipfile = isinstance(fp, zipfile.ZipFile)
        if is_zipfile: # ZIP files
                namelist = fp.namelist()
                if 'content' in namelist: # Multi-part object (e.g. project)
                    obj = None
                    decoder = json.JSONDecoder()

                    def get_named_item(fpt, name):
                        try:
                            cf = fpt.open(name, cls.__file_mode__)
                            obj = decoder.decode(cf.read().decode("utf-8"))
                        finally:
                            cf.close()
                        return obj
                    
                    # Parse the content file
                    obj = get_named_item(fp, 'content')
                    
                    # Check for a version tag:
                    if 'version' in namelist:
                        namelist.remove('version')
                        version = get_named_item(fp, 'version')
                        if LooseVersion(version) > LooseVersion(__version__.replace("v", "")):
                            raise RuntimeError("Unsupported project" + \
                                  "version '%s', program version is '%s'" % (
                                version, __version__
                            ))
                    else:
                        logging.warn("Loading pre-v0.8 file format, " +
                                     "might be deprecated!")

                    # Make sure we have a dict at this point
                    if not hasattr(obj, "update"):
                        raise RuntimeError("Decoding a multi-part JSON " + \
                          "object requires the root to be a dictionary object!")

                    # Parse all the other files, and set accordingly in the content dict
                    for sub_name in namelist:
                        if sub_name != "content":
                            obj["properties"][sub_name] = get_named_item(
                                fp, sub_name)

                    # Now parse the JSON dict to a Python object
                    data_objects = PyXRDDecoder(mapper=storables).__pyxrd_decode__(obj) or obj
                else: # Multiple objects in one zip file (e.g. phases)
                    data_objects = []
                    for sub_name in namelist:
                        zpf = fp.open(sub_name, cls.__file_mode__)
                        data_objects.append(cls.parse(zpf))
                        zpf.close()
        elif hasattr(fp, 'seek'): # Regular file
            try:
                fp.seek(0) # reset file position
            except io.UnsupportedOperation:
                pass # ignore these
            data_objects = PyXRDDecoder.decode_file(fp, mapper=storables)
        else:
            pass # use filename?

        if close: fp.close()
        return data_objects

    @staticmethod
    def write(obj, file, zipped=False): # @ReservedAssignment
        """
        Saves the output from dump_object() to `filename`, optionally zipping it.
        File can be either a filename or a file-like object. If it is a filename
        extra precautions are taken to prevent malformed data overwriting a good
        file. With file objects this is not the case.
        """
        filename = None
        if isinstance(file, str):
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
