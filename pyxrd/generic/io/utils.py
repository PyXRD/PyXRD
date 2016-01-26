# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

"""
    Input/Output related utility functions
"""

import os, sys

from mvc.support.file_utils import get_case_insensitive_glob, retrieve_lowercase_extension, relpath

# Small workaround to provide a unicode-aware open method:
if sys.version_info[0] < 3: # Pre Python 3.0
    import codecs
    _open_func_bak = open # Make a back up, just in case
    open = codecs.open #@ReservedAssignment

def sizeof_fmt(num):
    ''' Returns a human-friendly string when given a size in bytes '''
    for x in ['bytes', 'kB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

def get_size(path='.', maxsize=None):
    ''' Gets the recursive size of a path, can be limited to a maxsize '''
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path): #@UnusedVariable
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
            if maxsize is not None and total_size > maxsize:
                break
        if maxsize is not None and total_size > maxsize:
            break
    return total_size

def unicode_open(*args, **kwargs):
    """
        Opens files in UTF-8 encoding by default, unless an 'encoding'
        keyword argument is passed. Returns a file object.
    """
    if not "encoding" in kwargs:
        kwargs["encoding"] = "utf-8"
    return open(*args, **kwargs)