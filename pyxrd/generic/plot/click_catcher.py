# coding=UTF-8
# ex:ts=4:sw=4:et

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from .event_delegator import MPLCanvasEventDelegator

class ClickCatcher():
    """
        A wrapper that tracks mouse movements on a plot. Will call
        the update_callback with an x position and the click event object as
        arguments.
    """
    def __init__(self, plot_controller, update_callback=None):
        self.plot_controller = plot_controller
        self._canvas = plot_controller.canvas
        self._window = self._canvas.get_window()
        self._update_callback = update_callback
        self.connect()
        self._artists = {}

    def register_artist(self, artist, callback, *args):
        self._artists[artist] = (callback, args)
        artist.set_picker(True)

    def edit_marker(self, marker):
        self.plot_controller.app_controller.show_marker(marker)
    
    def _on_pick(self, event):
        if event.artist is not None:
            callback, args = self._artists.get(event.artist, None)
            print(callback, args)
            callback(*args)
            
        """if isinstance(event.artist, Line2D):
            thisline = event.artist
            xdata = thisline.get_xdata()
            ydata = thisline.get_ydata()
            ind = event.ind
            print('onpick1 line:', zip(np.take(xdata, ind), np.take(ydata, ind)))
        elif isinstance(event.artist, Rectangle):
            patch = event.artist
            print('onpick1 patch:', patch.get_path())
        elif isinstance(event.artist, Text):
            text = event.artist
            print('onpick1 text:', text.get_text())"""
        return False

    def connect(self):
        delegator = MPLCanvasEventDelegator.wrap_canvas(self._canvas)
        delegator.connect('pick_event', self._on_pick, first=True)

    def disconnect(self):
        delegator = MPLCanvasEventDelegator.wrap_canvas(self._canvas)
        delegator.disconnect('pick_event', self._on_pick)

    pass #end of class