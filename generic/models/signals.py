# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from gtkmvc.model import Signal

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
