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

class ObserveMixin(object):
    """
    A descriptor mixin that will make the instance observe and relieve the
    objects set.
    """

    def __relieve_old(self, instance, old, new):
        if old is not None:
            instance.relieve_model(old)

    def __observe_new(self, instance, old, new):
        if new is not None:
            instance.observe_model(new)

    def _set(self, instance, value):
        old = getattr(instance, self.label)
        if old != value:
            self.__relieve_old(instance, old, value)
            super(ObserveMixin, self)._set(instance, value)
            self.__observe_new(instance, old, value)

    pass
