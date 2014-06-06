# coding=UTF-8
# ex:ts=4:sw=4:et

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk
from .event_delegator import MPLCanvasEventDelegator

class EyeDropper():
    """
        A wrapper that makes eye-dropping a plot possible. Will call
        the click_callback with an x position and the click event object as
        arguments.
    """
    def __init__(self, canvas, window, click_callback=None):
        self._canvas = canvas
        self._window = window
        self._click_callback = click_callback
        self.connect()

    def _on_motion(self, event):
        if self._window is not None:
            self._window.set_cursor(gtk.gdk.Cursor(gtk.gdk.CROSSHAIR)) # @UndefinedVariable
        return True

    def _on_click(self, event):
        x_pos = -1
        if event.inaxes:
            x_pos = event.xdata
        if callable(self._click_callback):
            self._click_callback(x_pos, event)
        if self._window is not None:
            self._window.set_cursor(None)
        return True

    def connect(self):
        delegator = MPLCanvasEventDelegator.wrap_canvas(self._canvas)

        delegator.connect('motion_notify_event', self._on_motion, first=True)
        delegator.connect('button_press_event', self._on_click, first=True)

    def disconnect(self):
        if self._window is not None:
            self._window.set_cursor(None)

        delegator = MPLCanvasEventDelegator.wrap_canvas(self._canvas)
        delegator.disconnect('motion_notify_event', self._on_motion)
        delegator.disconnect('button_press_event', self._on_click)

    pass #end of class
