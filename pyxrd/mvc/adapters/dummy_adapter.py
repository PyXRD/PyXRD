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

from .abstract_adapter import AbstractAdapter

class DummyAdapter(AbstractAdapter):
    """
        An adapter that does nothing. Really nothing.
    """

    def __init__(self, controller=None, prop=None, widget=None):
        super(DummyAdapter, self).__init__(controller, prop, widget)

    def _connect_widget(self):
        pass # nothing to do

    def _disconnect_widget(self, widget=None):
        pass # nothing to do

    def _connect_model(self):
        pass # nothing to do

    def _disconnect_model(self, model=None):
        pass # nothing to do

    def _read_widget(self):
        pass # nothing to do

    def _write_widget(self, val):
        pass # nothing to do

    def _read_property(self, *args):
        pass # nothing to do

    def _write_property(self, value, *args):
        pass # nothing to do

    pass # end of class