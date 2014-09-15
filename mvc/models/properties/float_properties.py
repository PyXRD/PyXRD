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
from .cast_choice_property import CastChoiceProperty


class FloatProperty(CastProperty):
    """
     A descriptor that will cast values to floats and can optionally clamp
     values to a minimum and maximum.
     Expects its label to be set or passed to __init__.
    """

    data_type = float
    widget_type = 'scale' # | float_entry | entry | spin | label

    def __init__(self, *args, **kwargs):
        super(FloatProperty, self).__init__(cast_to=float, *args, **kwargs)

    pass #end of class

class FloatChoiceProperty(CastChoiceProperty):
    """
     A descriptor that will cast values to floats and can optionally clamp
     values to a minimum and maximum.
     It also expects the (cast and clamped) value to be in a set of choices or
     it will raise a ValueError.
     Expects its label to be set or passed to __init__.
    """

    data_type = float
    widget_type = 'option_list'

    def __init__(self, choices=[], *args, **kwargs):
        super(FloatChoiceProperty, self).__init__(
            cast_to=float,
            choices=choices,
            *args, **kwargs
        )

    pass #end of class