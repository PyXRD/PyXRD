# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#  Copyright (C) 2005 by Roberto Cavada <roboogle@gmail.com>
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


class DecoratorError (SyntaxError):
    """Used to report syntax errors occurring when decorators are
    used in models and observers."""
    pass


class TooManyCandidatesError (ValueError):
    """This class is used for distinguishing between a
    multiple candidates matched and no candidates matched. The
    latter is not necessarily an issue, as a missed match can
    be skipped when searching for a match for *all* the
    properties in the model (no params to adapt()), which may
    fail in one single view, as multiple views may be used to
    represent different parts of the model"""
    pass


class ViewError (ValueError):
    """General issue with view content"""
    pass

