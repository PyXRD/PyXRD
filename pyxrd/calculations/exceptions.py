# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import multiprocessing
from functools import wraps
import traceback, sys

class WrapException(Exception):
    """
        A wrapped exception used by the :meth:`~wrap_exceptions` decorator.
    """
    def __init__(self):
        exc_type, exc_value, exc_tb = sys.exc_info()
        self.exception = exc_value
        self.formatted = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    def __str__(self):
        return '%s\nOriginal traceback:\n%s' % (Exception.__str__(self), self.formatted)

def wrap_exceptions(func):
    """
        Function decorator that allows to provide useable tracebacks when the
        function is called asynchronously and raises an error.
     """
    @wraps(func)
    def exception_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            if multiprocessing.current_process().daemon:
                raise WrapException()
            else:
                raise
    return exception_wrapper