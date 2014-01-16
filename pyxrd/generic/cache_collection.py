# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon, Jason Yosinski
# All rights reserved.
# Complete license can be found in the LICENSE file.

from functools import wraps
from collections import OrderedDict
from pyxrd.data import settings

import logging
logger = logging.getLogger(__name__)

import hashlib
import marshal
from numpy import *
import types
import inspect

"""
    A tiny but memory hungry custom caching lib
    Based on: https://github.com/yosinski/python-numpy-cache/blob/master/cache.py
    Modified to match my needs
    All credits to Jason Yosinski
"""

class CacheDict(OrderedDict):
    """
        OrderedDict with a limited size (default 20 items)
    """
    def __init__(self, *args, **kwds):
        self.size_limit = kwds.pop("limit", 20)
        OrderedDict.__init__(self, *args, **kwds)
        self._check_size_limit()

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self._check_size_limit()

    def _check_size_limit(self):
        if self.size_limit is not None:
            while len(self) > self.size_limit:
                self.popitem(last=False)

class PersistentHasher(object):
    '''Hashes, persistently and consistenly. Suports only two methods:
    update and hexdigest. Supports numpy arrays and dicts.'''

    def __init__(self):
        self.counter = 0
        self.hashAlg = hashlib.sha1()
        self.salt = '3.14159265358979323'

    def update(self, obj, level=0):
        '''A smarter, more persistent verison of hashlib.update'''
        if isinstance(obj, types.BuiltinFunctionType):
            # Function name is sufficient for builtin functions.
            # Built in functions do not have func_code, but their code
            # is unlikely to change anyway.
            self.hashAlg.update(obj.__name__)
        elif isinstance(obj, types.FunctionType):
            # For user defined functions, hash the function name and
            # function code itself (a bit overconservative)
            self.hashAlg.update(obj.__name__)
            self.hashAlg.update(marshal.dumps(obj.func_code))
        elif type(obj) is ndarray:
            # can update directly with numpy arrays
            self.hashAlg.update(self.salt + 'numpy.ndarray')
            self.hashAlg.update(obj)
        elif type(obj) is dict:
            self.hashAlg.update(self.salt + 'dict')
            for key, val in sorted(obj.items()):
                self.hashAlg.update(str(hash(key)))
                self.update(val, level=level + 1)  # recursive call
        elif inspect.isclass(obj):
            raise Exception('Hashing whole classes not supported yet (have not implemented reliable way to hash all methods)')
        else:
            # Just try to hash it
            try:
                self.hashAlg.update(str(hash(obj)))
            except TypeError:
                if type(obj) is tuple or type(obj) is list:
                    # Tuples are only hashable if all their components are.
                    self.hashAlg.update(self.salt + ('tuple' if type(obj) is tuple else 'list'))
                    for item in obj:
                        self.update(item, level=level + 1)  # recursive call
                else:
                    logger.critical('UNSUPPORTED TYPE: FIX THIS: %s, %s' % (type(obj), obj))

        self.counter += 1


    def hexdigest(self):
        return self.hashAlg.hexdigest()

def cache(maxsize=16):
    if not settings.USE_CACHES: # @UndefinedVariable
        def dummy(func):
            func.func = func
            return func
        return dummy
    else:
        def rcache(func):
            @wraps(func)
            def wrapper(*args, **kwargs):

                cached = getattr(func, '__cached', CacheDict(limit=maxsize))
                func.__cached = cached

                # Hash the args and kwargs
                hasher = PersistentHasher()
                hasher.update(args)
                hasher.update(kwargs)

                digest = hasher.hexdigest()

                if not digest in cached:
                    cached[digest] = func(*args, **kwargs)

                return cached[digest]
            wrapper.func = func
            return wrapper
        return rcache
