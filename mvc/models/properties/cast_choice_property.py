# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
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

from .cast_property import CastProperty

class CastChoiceProperty(CastProperty):
    """
     A descriptor that can cast the values to a given type, clamp values to a
     minimum and maximum.
     It also expects the (cast and clamped) value to be in a list or dict of
     choices or it will raise a ValueError.
     Expects its label to be set or passed to __init__.
    """

    choices = None
    widget_type = 'option_list'

    def __init__(self, choices=[], *args, **kwargs):
        super(CastChoiceProperty, self).__init__(*args, **kwargs)
        self.choices = choices

    def __set__(self, instance, value):
        value = self.__cast_and_clamp__(instance, value)
        if value in self.choices:
            super(CastProperty, self).__set__(instance, value) #Call grandparent __set__
        else:
            raise ValueError("'%s' is not a valid value for %s!" % (value, self.label))

    pass #end of class
