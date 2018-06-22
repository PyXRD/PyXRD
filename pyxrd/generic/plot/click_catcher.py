# coding=UTF-8
# ex:ts=4:sw=4:et

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from .event_delegator import MPLCanvasEventDelegator

class ClickCatcher():
    """
        This class can be used to register matplotlib artists, which will
        fire the update_callback method when clicked. When registering
        the artist, an arbitrary object can be passed which is passed to the
        callback. 
    """
    def __init__(self, plot_controller, update_callback=None):
        self.plot_controller = plot_controller
        self._canvas = plot_controller.canvas
        self._window = self._canvas.get_window()
        self._update_callback = update_callback
        self.connect()
        self._artists = {}

    def register_artist(self, artist, obj):
        self._artists[artist] = obj
        artist.set_picker(True)
   
    def _on_pick(self, event):
        if event.artist is not None:
            obj = self._artists.get(event.artist, None)
            self._update_callback(obj)
        return False

    def connect(self):
        delegator = MPLCanvasEventDelegator.wrap_canvas(self._canvas)
        delegator.connect('pick_event', self._on_pick, first=True)

    def disconnect(self):
        delegator = MPLCanvasEventDelegator.wrap_canvas(self._canvas)
        delegator.disconnect('pick_event', self._on_pick)

    pass #end of class