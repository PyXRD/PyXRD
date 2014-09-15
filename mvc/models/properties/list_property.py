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

class ListProperty(CastProperty):
    """
     A descriptor that will cast values to lists.
     Expects its label to be set or passed to __init__.
    """

    widget_type = 'object_list_view' # | object_tree_view | xy_list_view | custom

    def __cast_and_clamp__(self, instance, value):
        if self.cast_to is not None and value is not None and not isinstance(value, self.cast_to):
            value = self.cast_to(value)
        return value

    def __init__(self, *args, **kwargs):
        if not "cast_to" in kwargs:
            kwargs["cast_to"] = list
        super(ListProperty, self).__init__(*args, **kwargs)

    pass #end of class