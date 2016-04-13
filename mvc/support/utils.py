# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#  Copyright (C) 2007 by Roberto Cavada <roboogle@gmail.com>
#
#  mvc is a framework derived from the original pygtkmvc framework
#  hosted at: <http://sourceforge.net/projects/pygtkmvc/>
#
#  mvc is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  mvc is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor,
#  Boston, MA 02110, USA.
#  -------------------------------------------------------------------------

import os
from uuid import uuid4 as get_uuid

def round_sig(x, sig=1):
    if x == 0:
        return 0
    else:
        return round(x, sig - int(floor(log10(abs(x)))) - 1)

def not_none(passed, default):
    """Returns `passed` if not None, else `default` is returned"""
    return passed if passed is not None else default

def getmembers(_object, _predicate):
    """This is an implementation of inspect.getmembers, as in some versions 
    of python it may be buggy. 
    See issue at http://bugs.python.org/issue1785"""
    # This should be:
    # return inspect.getmembers(_object, _predicate)

    # ... and it is re-implemented as:
    observers = []
    for key in dir(_object):
        try: m = getattr(_object, key)
        except AttributeError: continue
        if _predicate(m): observers.append((key, m))
        pass
    return observers

def get_new_uuid():
    return unicode(get_uuid().hex)

def get_unique_list(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if x not in seen and not seen_add(x)]

def pop_kwargs(kwargs, *keys):
    return {
        key: kwargs.pop(key) for key in keys if key in kwargs
    }