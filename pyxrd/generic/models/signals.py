# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.mvc import Signal

class HoldableSignal(Signal):
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

    # INIT:
    def __init__(self, *args, **kwargs):
        super(HoldableSignal, self).__init__(*args, **kwargs)
        self._counter = 0
        self._emissions_pending = False
        self._ignore_levels = []

    # WITH FUNCTIONALITY:
    def __enter__(self):
        self._counter += 1;

    def __exit__(self, *args):
        self._counter -= 1;
        if self._counter < 0:
            raise RuntimeError, "Negative counter in CounterLock object! Did you call __exit__ too many times?"
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

    # STANDARD EMIT OVERRID:
    def emit(self, *args, **kwargs):
        if self._counter == 0:
            self._emissions_pending = False
            super(HoldableSignal, self).emit(*args, **kwargs)
        else:
            self._emit_pending()

    def _emit_pending(self):
        if not self._emissions_pending:
            self._emissions_pending = bool(len(self._ignore_levels) == 0)

class DefaultSignal (Signal):
    """
        A signal that can (optionally) call a before and after handler before
        the actuall signal will be emitted.
        
        If a before handler is set, it will recieve a wrapper for
        the actual signals emit method as a positional argument. It is the
        before handler's job to also call this.
    """
    def __init__(self, before=None, after=None):
        Signal.__init__(self)
        self.before = before
        self.after = after
        return

    def emit(self):
        def after():
            Signal.emit(self)
            if callable(self.after): self.after()
        if callable(self.before): self.before(after)
        else: after()

    pass # end of class
