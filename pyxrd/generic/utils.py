# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import time
import hashlib

def rec_getattr(obj, attr, default):
    """Get object's attribute. May use dot notation.

    >>> class C(object): pass
    >>> a = C()
    >>> a.b = C()
    >>> a.b.c = 4
    >>> rec_getattr(a, 'b.c')
    4
    """
    if '.' not in attr:
        return getattr(obj, attr, default)
    else:
        attr, attrs = attr.split('.', 1)
        return rec_getattr(getattr(obj, attr), attrs, default)

def not_none(passed, default):
    """Convenience function to check if a value is None and return a default if so"""
    return passed if passed is not None else default

def print_stack_plus():
    """
    Print the usual traceback information, followed by a listing of all the
    local variables in each frame.
    """
    stack = []
    depth = 1
    while 1:
        try:
            f = sys._getframe(depth)
            depth += 1
            stack.append(f)
        except ValueError:
            break
    print "Locals by frame, innermost last"
    for frame in stack:
        print
        print "Frame %s in %s at line %s" % (frame.f_code.co_name,
                                             frame.f_code.co_filename,
                                             frame.f_lineno)
        for key, value in frame.f_locals.items():
            print "\t%20s = " % key,
            # We have to be careful not to cause a new error in our error
            # printer! Calling str() on an unknown object could cause an
            # error we don't want.
            try:
                print value
            except:
                print "<ERROR WHILE PRINTING VALUE>"

def get_md5_hash(obj):
    hsh = hashlib.md5()
    hsh.update(obj)
    return hsh.digest()

def get_md5_hash_for_args(args):
    hsh = hashlib.md5()
    for arg in args:
        hsh.update(arg)
    return hsh.digest()

def u(string):
    return unicode(string, errors='replace', encoding='UTF-8')

def print_timing(func):
    def wrapper(*args, **kwargs):
        t1 = time.time()
        res = func(*args, **kwargs)
        t2 = time.time()
        print '%s took %0.3f ms' % (func.func_name, (t2 - t1) * 1000.0)
        return res
    return wrapper

class delayed(object):
    def __init__(self, lock=None, delay=250):
        self.__lock = lock
        self.__delay = delay
        self.__tmrid = dict()

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                import gobject
            except ImportError:
                func(*args, **kwargs)
            else:
                instance = args[0] if len(args) > 0 else None
                key = instance or func
                if self.__lock is not None and getattr(instance, self.__lock):
                    return # if the function is locked, do not push back the call
                if key in self.__tmrid:
                    gobject.source_remove(self.__tmrid[key])
                    del self.__tmrid[key]
                delay = 0
                try:
                    delay = int(self.__delay)
                except:
                    delay = getattr(instance, self.__delay)
                self.__tmrid[key] = gobject.timeout_add(delay, self.__timeout_handler__, func, key, *args, **kwargs)
        return wrapper

    def __timeout_handler__(self, func, key, *args, **kwargs):
        func(*args, **kwargs)
        if key in self.__tmrid: del self.__tmrid[key]
        return False
