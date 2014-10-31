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

import logging
logger = logging.getLogger(__name__)
import weakref

from .metaclasses import MetaAdapter

class AbstractAdapter(object):
    """
        An semi-abstract class all Adapters have to derive from.
    """
    __metaclass__ = MetaAdapter

    widget_types = []

    __prop = None
    @property
    def _prop(self):
        if callable(self.__prop):
            return self.__prop()
        else:
            return self.__prop
    @_prop.setter
    def _prop(self, value):
        if value is None:
            self.__prop = None
        else:
            self.__prop = weakref.ref(value, lambda: self.disconnect())

    __controller = None
    @property
    def _controller(self):
        if callable(weakref.ReferenceType):
            return self.__controller()
        else:
            return self.__controller
    @_controller.setter
    def _controller(self, value):
        if value is None:
            self.__controller = None
        else:
            self.__controller = weakref.ref(value, lambda c: self.disconnect())

    __widget = None
    @property
    def _widget(self):
        if callable(weakref.ReferenceType):
            return self.__widget()
        else:
            return self.__widget
    @_widget.setter
    def _widget(self, value):
        if value is None:
            self.__widget = None
        else:
            self.__widget = weakref.ref(value, lambda w: self.disconnect(widget=w()))

    # ----------------------------------------------------------------------
    #  Construction:
    # ----------------------------------------------------------------------
    def __init__(self, controller, prop, widget, *args, **kwargs):
        super(AbstractAdapter, self).__init__(*args, **kwargs)

        self._prop = prop
        self._controller = controller
        self._widget = widget

    # ----------------------------------------------------------------------
    #  Public interface:
    # ----------------------------------------------------------------------
    def update_model(self):
        """Forces the property to be updated from the value hold by
        the widget. This method should be called directly by the
        user in very unusual conditions."""
        self._write_property(self._read_widget())
        return

    def update_widget(self):
        """Forces the widget to be updated from the property
        value. This method should be called directly by the user
        when the property is not observable, or in very unusual
        conditions."""
        self._write_widget(self._read_property())
        return

    def disconnect(self, model=None, widget=None):
        """Disconnects the adapter from the model and the widget."""
        self._disconnect_model(model=model)
        self._disconnect_widget(widget=widget)

    # ----------------------------------------------------------------------
    #  Widget connecting & disconnecting:
    # ----------------------------------------------------------------------
    def _connect_widget(self):
        raise NotImplementedError("Please Implement this method")

    def _disconnect_widget(self, widget=None):
        raise NotImplementedError("Please Implement this method")

    # ----------------------------------------------------------------------
    #  Model connecting & disconnecting:
    # ----------------------------------------------------------------------
    def _connect_model(self):
        raise NotImplementedError("Please Implement this method")

    def _disconnect_model(self, model=None):
        raise NotImplementedError("Please Implement this method")

    # ----------------------------------------------------------------------
    #  Widget-side reading and writing
    # ----------------------------------------------------------------------
    def _read_widget(self):
        raise NotImplementedError("Please Implement this method")

    def _write_widget(self, val):
        raise NotImplementedError("Please Implement this method")

    # ----------------------------------------------------------------------
    #  Model-side reading and writing
    # ----------------------------------------------------------------------
    def _read_property(self, *args):
        raise NotImplementedError("Please Implement this method")

    def _write_property(self, value, *args):
        raise NotImplementedError("Please Implement this method")

    pass # end of class
