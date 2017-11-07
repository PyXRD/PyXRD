# coding=UTF-8
# ex:ts=4:sw=4:et

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from .event_delegator import MPLCanvasEventDelegator

class MotionTracker():
    """
        A wrapper that tracks mouse movements on a plot. Will call
        the update_callback with an x position and the click event object as
        arguments.
    """
    def __init__(self, plot_controller, update_callback=None):
        self._canvas = plot_controller.canvas
        self._window = self._canvas.get_window()
        self._update_callback = update_callback
        self.connect()

    def _on_motion(self, event):
        x_pos = -1
        if event.inaxes:
            x_pos = event.xdata
        if callable(self._update_callback):
            self._update_callback(x_pos, event)
        return False

    def connect(self):
        delegator = MPLCanvasEventDelegator.wrap_canvas(self._canvas)
        delegator.connect('motion_notify_event', self._on_motion, first=True)

    def disconnect(self):
        delegator = MPLCanvasEventDelegator.wrap_canvas(self._canvas)
        delegator.disconnect('motion_notify_event', self._on_motion)

    pass #end of class
