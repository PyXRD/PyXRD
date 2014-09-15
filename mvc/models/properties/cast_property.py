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

from .labeled_property import LabeledProperty

class CastProperty(LabeledProperty):
    """
     A descriptor that can cast the values to a given type and clamp values to a
     minimum and maximum. 
     Expects its label to be set or passed to __init__.
    """

    def __init__(self,
            minimum=None, maximum=None,
            cast_to=None,
            *args, **kwargs):
        super(CastProperty, self).__init__(*args, **kwargs)
        self.minimum = minimum
        self.maximum = maximum
        self.cast_to = cast_to

    def __cast_and_clamp__(self, instance, value):
        if self.minimum is not None:
            value = max(value, self.minimum)
        if self.maximum is not None:
            value = min(value, self.maximum)
        if self.cast_to is not None and value is not None:
            value = self.cast_to(value)
        return value

    def __set__(self, instance, value):
        value = self.__cast_and_clamp__(instance, value)
        if getattr(instance, self.label) != value:
            super(CastProperty, self).__set__(instance, value)

    pass #end of class