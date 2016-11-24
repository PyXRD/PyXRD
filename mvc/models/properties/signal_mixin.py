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

from mvc.support.utils import rec_getattr
from mvc.support import observables

class SignalMixin(object):
    """
    A descriptor mixin that will invoke a signal on the instance
    owning this property when set. 
    
    Expects two more keyword arguments to be passed to the property constructor:
        - signal_name: a dotted string describing where to get the signal object
          from the instance
    """

    signal_name = "data_changed"

    def __set__(self, instance, value):
        signal = rec_getattr(instance, self.signal_name, None)
        if signal is not None:
            # Get the old value
            old = getattr(instance, self.label)
            with signal.ignore():
                super(SignalMixin, self).__set__(instance, value)
            # Get the new value
            new = getattr(instance, self.label)
            # Check if we're dealing with some special class (in case we
            # emit the signal anyway) or immutables (in case we only emit
            # when the value has changed)  
            if isinstance(old, observables.ObsWrapperBase) or old != new:
                signal.emit()
        else:
            super(SignalMixin, self).__set__(instance, value)
            
    pass # end of class
