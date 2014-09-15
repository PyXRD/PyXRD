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

from pyxrd.generic.utils import rec_getattr
from contextlib import contextmanager

class SignalMixin(object):
    """
    A descriptor mixin that will invoke a signal on the instance
    owning this property when set. 
    
    Expects two more keyword arguments to be passed to the property constructor:
        - signal_name: a dotted string describing where to get the signal object
          from the instance
        - hold_signal: a flag indicating whether to hold the signal while setting
          the property (True) or emit it before setting (False)
    """

    signal_name = "data_changed"
    hold_signal = True

    def __get_event_context__(self, instance):
        signal = rec_getattr(instance, self.signal_name, None)
        if self.hold_signal and signal is not None:
            return signal.hold_and_emit
        else:
            def dummy():
                yield
                if signal is not None: signal.emit()
            return contextmanager(dummy)

    def __set__(self, instance, value):
        with self.__get_event_context__(instance)():
            super(SignalMixin, self).__set__(instance, value)

    pass # end of class
