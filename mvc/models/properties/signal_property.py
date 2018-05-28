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

from mvc.support.observables.signal import Signal

from .labeled_property import LabeledProperty

class SignalProperty(LabeledProperty):
    """
    A descriptor for signals.
    Expects a single additional keyword argument (or not for default of Signal):
        - data_type: the type of signal to initialize this property with.
    """

    data_type = Signal

    def _get(self, instance):
        signal = getattr(instance, self._get_private_label(), None)
        if signal is None: # If accesed for the first time set the Signal
            signal = self.data_type()
            setattr(instance, self._get_private_label(), signal)
        return signal

    def __set__(self, instance, value):
        raise AttributeError("Cannot set a Signal property!")

    pass # end of class
