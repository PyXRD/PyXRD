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


class UUIDProperty(LabeledProperty):
    """
     A descriptor that handles removing and adding objects to a pool of unique
     objects. Expects the class type of the instance having this property to
     implement a 'remove_object' and 'add_object' method.
    """

    def __set__(self, instance, value):
        type(instance).object_pool.remove_object(instance)
        retval = super(UUIDProperty, self).__set__(instance, value)
        type(instance).object_pool.add_object(instance)
        return retval

    pass #end of class
