# coding=UTF-8
# ex:ts=4:sw=4:et

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

# from matplotlib.backends.backend_gtk import FigureCanvasGTK

import gtk

class DraggableMixin(object):

    _prev_event_data = None
    _draggable_artist = None
    _draggable_figure = None
    _draggable_canvas = None
    _draggable_axes = None
    _on_dragged_delta_x = None
    _on_dragged_delta_y = None

    def __init__(self, artist=None, on_dragged_delta_x=None, on_dragged_delta_y=None, *args, **kwargs):
        super(DraggableMixin, self).__init__()
        self.update(artist, on_dragged_delta_x, on_dragged_delta_y)

    def update(self, artist=None, on_dragged_delta_x=None, on_dragged_delta_y=None):
        self._on_dragged_delta_x = on_dragged_delta_x
        self._on_dragged_delta_y = on_dragged_delta_y
        self.set_draggable_artist(artist)

    def set_draggable_artist(self, artist):
        if self._draggable_figure is not None:
            self._draggable_disconnect()

        self._draggable_artist = artist
        self._draggable_figure = artist.figure if artist is not None else None
        self._draggable_canvas = artist.figure.canvas if artist is not None else None
        self._draggable_axes = artist.axes if artist is not None else None

        if self._draggable_artist is not None:
            self._draggable_connect()

    def _draggable_on_press(self, event):
        if self._draggable_figure is None: return

        contains, attrd = self._draggable_artist.contains(event) # @UnusedVariable
        if not contains: return
        self._prev_event_data = self._draggable_convert_display_xy(event.x, event.y)

    def _draggable_convert_display_xy(self, x, y):
        tAxes = self._draggable_axes.transAxes
        tAxesInv = tAxes.inverted()

        tx, ty = tAxesInv.transform((x, y))
        return tx, ty

    def _draggable_on_motion(self, event):
        if self._draggable_figure is None: return
        if self._prev_event_data is None: return

        xpress, ypress = self._prev_event_data
        tx, ty = self._draggable_convert_display_xy(event.x, event.y)

        if callable(self._on_dragged_delta_x):
            self._on_dragged_delta_x(tx - xpress, button=event.button)
        if callable(self._on_dragged_delta_y):
            self._on_dragged_delta_y(ty - ypress, button=event.button)

        self._prev_event_data = tx, ty

    def _draggable_on_release(self, event):
        self._prev_event_data = None

    def _draggable_connect(self):
        self.cidpress = self._draggable_canvas.mpl_connect(
            'button_press_event', self._draggable_on_press)
        self.cidrelease = self._draggable_canvas.mpl_connect(
            'button_release_event', self._draggable_on_release)
        self.cidmotion = self._draggable_canvas.mpl_connect(
            'motion_notify_event', self._draggable_on_motion)

    def _draggable_disconnect(self):
        self._draggable_canvas.mpl_disconnect(self.cidpress)
        self._draggable_canvas.mpl_disconnect(self.cidrelease)
        self._draggable_canvas.mpl_disconnect(self.cidmotion)
