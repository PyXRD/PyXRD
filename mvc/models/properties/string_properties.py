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

class StringProperty(CastProperty):
    """
     A descriptor that will cast values to strings and can optionally clamp
     values to a minimum and maximum.
     Expects its label to be set or passed to __init__.
    """

    data_type = str
    widget_type = 'entry' # | label | color | color-selection | file | link | text_view

    def __init__(self, *args, **kwargs):
        super(StringProperty, self).__init__(cast_to=str, *args, **kwargs)

    pass #end of class

class ColorProperty(StringProperty):
    """
     A descriptor that will cast values to strings and can optionally clamp
     values to a minimum and maximum. Has a color widget as the default widget.
     Expects its label to be set or passed to __init__.
    """

    widget_type = 'color' # entry | label | color-selection | file | link | text_view

    pass #end of class

class StringChoiceProperty(CastChoiceProperty):
    """
     A descriptor that will cast values to strings and can optionally clamp
     values to a minimum and maximum.
     It also expects the (cast and clamped) value to be in a set of choices or
     it will raise a ValueError.
     Expects its label to be set or passed to __init__.
    """

    data_type = str
    widget_type = 'option_list'

    def __init__(self, choices=[], *args, **kwargs):
        super(StringChoiceProperty, self).__init__(
            cast_to=str,
            choices=choices,
            *args, **kwargs
        )

    pass #end of class
