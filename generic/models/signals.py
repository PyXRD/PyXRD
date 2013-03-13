# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

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
