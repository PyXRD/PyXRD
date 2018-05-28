# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#  Copyright (C) 2005 by Tobias Weber
#  Copyright (C) 2005 by Roberto Cavada <roboogle@gmail.com>
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

import threading

from .observable import Observable

class Signal(Observable):
    """
        A Signal that can either:
         - be 'held' from firing until a code block has finished, e.g. to
           prevent numerous events from firing, when one final event would
           be enough
         - be stopped from firing altogether, even after the code block has
           finished 
        
        Holding signals back:
         ...
         object.hold_signal = HoldableSignal()
         ...
         with object.hold_signal.hold():
             # this code block can call emit() on the hold_signal but it will not
             # actually emit the signal until the 'with' block is left
         ...
         
        Ignoring signals:
         ...
         object.hold_signal =  HoldableSignal()
         ...
         with object.hold_signal.ignore():
             # this code block can call emit() on the hold_signal but it will not
             # actually emit the signal, even after leaving the 'with' block
    """
    # PROPERTIES:
    clock = threading.RLock()

    # INIT:
    def __init__(self, *args, **kwargs):
        super(Signal, self).__init__(*args, **kwargs)
        self._counter = 0
        self._emissions_pending = False
        self._ignore_levels = []

    # WITH FUNCTIONALITY:
    def __enter__(self):
        with self.clock:
            self._counter += 1;

    def __exit__(self, *args):
        with self.clock:
            self._counter -= 1;
            if self._counter < 0:
                raise RuntimeError("Negative counter in CounterLock object! Did you call __exit__ too many times?")
            if len(self._ignore_levels) > 0 and self._counter == self._ignore_levels[-1]:
                self._ignore_levels.pop()
            elif self._counter == 0 and self._emissions_pending:
                # Fire the signal when we leave the with block
                self.emit()

    def hold(self):
        return self

    def ignore(self):
        self._ignore_levels.append(self._counter)
        return self

    def hold_and_emit(self):
        self._emit_pending() # set our pending flag
        return self

    def emit(self, arg=None):
        if self._counter == 0:
            self._emissions_pending = False
            for model, name in self.__get_models__():
                model.notify_signal_emit(name, arg)
                pass
        else:
            self._emit_pending()

    def _emit_pending(self):
        if not self._emissions_pending:
            self._emissions_pending = bool(len(self._ignore_levels) == 0)

    pass #end of class