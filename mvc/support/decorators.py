# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#  Copyright (C) 2006 by Roberto Cavada <roboogle@gmail.com>
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


# This file contains decorators to be used (privately) by other parts
# of the framework

import types

def good_decorator(decorator):
    """This decorator makes decorators behave well wrt to decorated
    functions names, doc, etc."""
    def new_decorator(f):
        g = decorator(f)
        g.__name__ = f.__name__
        g.__doc__ = f.__doc__
        g.__dict__.update(f.__dict__)
        return g

    new_decorator.__name__ = decorator.__name__
    new_decorator.__doc__ = decorator.__doc__
    new_decorator.__dict__.update(decorator.__dict__)

    return new_decorator


def good_classmethod_decorator(decorator):
    """This decorator makes class method decorators behave well wrt
    to decorated class method names, doc, etc."""
    def new_decorator(cls, f):
        g = decorator(cls, f)
        g.__name__ = f.__name__
        g.__doc__ = f.__doc__
        g.__dict__.update(f.__dict__)
        return g

    new_decorator.__name__ = decorator.__name__
    new_decorator.__doc__ = decorator.__doc__
    new_decorator.__dict__.update(decorator.__dict__)

    return new_decorator


def good_decorator_accepting_args(decorator):
    """This decorator makes decorators behave well wrt to decorated
    functions names, doc, etc. 

    Differently from good_decorator, this accepts decorators possibly
    receiving arguments and keyword arguments.

    This decorato can be used indifferently with class methods and
    functions."""
    def new_decorator(*f, **k):
        g = decorator(*f, **k)
        if 1 == len(f) and isinstance(f[0], types.FunctionType):
            g.__name__ = f[0].__name__
            g.__doc__ = f[0].__doc__
            g.__dict__.update(f[0].__dict__)
            pass
        return g

    new_decorator.__name__ = decorator.__name__
    new_decorator.__doc__ = decorator.__doc__
    new_decorator.__dict__.update(decorator.__dict__)
    # Required for Sphinx' automodule.
    new_decorator.__module__ = decorator.__module__
    return new_decorator
