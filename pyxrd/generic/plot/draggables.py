# coding=UTF-8
# ex:ts=4:sw=4:et

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk
from .event_delegator import MPLCanvasEventDelegator

class DraggableMixin(object):
    """
        A mixin that can be used to make any matplotlib artist draggable.
        The constructor takes two callbacks, `on_dragged` and `on_released`
        which are called when the artist is dragged and released respectively.
        
        These callbacks are passed 3 coordinate tuples: the starting point of
        the drag operation, the previous cursor position and the current cursor
        position. All of these are in display coordinates. If these need to be 
        converted you can use the `convert_display_to_*` methods where * should
        be one of figure, axes or data. Aside from these coordinates, the callbacks
        are also passed the last event object.
        
        For more advanced usage the user can also override the 
        `_draggable_on_press`, `_draggable_on_motion` and `_draggable_on_release`
        event handlers, be sure to call the base implementation if so.
    """

    lock = None  # only one can be animated at a time
    _prev_event_data = None
    _draggable_artist = None
    _draggable_figure = None
    _draggable_canvas = None
    _draggable_axes = None
    _on_dragged = None
    _on_released = None

    _first_event_data = None
    _prev_event_data = None

    @property
    def _is_dragging(self):
        return not bool(
            self._draggable_artist is None or \
            self._first_event_data is None or \
            self._prev_event_data is None
        )

    def __init__(self,
            artist=None,
            on_dragged=None, on_released=None,
            *args, **kwargs):
        super(DraggableMixin, self).__init__(*args, **kwargs)
        self.update(artist, on_dragged, on_released)

    def update(self, artist=None, on_dragged=None, on_released=None):
        self._on_dragged = on_dragged
        self._on_released = on_released
        self.set_draggable_artist(artist)

    def disconnect(self):
        self.set_draggable_artist(None)

    def set_draggable_artist(self, artist):
        if self._draggable_artist is not None:
            self._draggable_disconnect()

        self._draggable_artist = artist
        self._draggable_figure = artist.figure if artist is not None else None
        self._draggable_canvas = artist.figure.canvas if artist is not None else None
        self._draggable_axes = artist.axes if artist is not None else None

        if self._draggable_artist is not None:
            self._draggable_connect()

    def _convert_to_inverse_transform(self, x, y, transf):
        inverse = transf.inverted()
        return inverse.transform((x, y))

    def convert_display_to_figure(self, x, y):
        return self._convert_to_inverse_transform(
            x, y, self._draggable_figure.transFigure)

    def convert_display_to_axes(self, x, y):
        return self._convert_to_inverse_transform(
            x, y, self._draggable_axes.transAxes)

    def convert_display_to_data(self, x, y):
        return self._convert_to_inverse_transform(
            x, y, self._draggable_axes.transData)

    # -- EVENT HANDLERS:

    def _draggable_on_press(self, event):
        if self._draggable_figure is None: return False

        contains, attrd = self._draggable_artist.contains(event) # @UnusedVariable
        if not contains: return False

        self._prev_event_data = event.x, event.y
        self._first_event_data = self._prev_event_data

        return True

    def _draggable_on_motion(self, event):
        if not self._is_dragging: return

        x0, y0 = self._first_event_data
        x1, y1 = self._prev_event_data
        x2, y2 = event.x, event.y

        if callable(self._on_dragged):
            self._on_dragged(
                (x0, y0), (x1, y1), (x2, y2),
                event=event
            )

        self._prev_event_data = x2, y2

    def _draggable_on_release(self, event):
        if not self._is_dragging: return

        x0, y0 = self._first_event_data
        x1, y1 = self._prev_event_data
        x2, y2 = event.x, event.y

        if callable(self._on_released):
            self._on_released(
                (x0, y0), (x1, y1), (x2, y2),
                event=event
            )

        self._prev_event_data = None
        self._first_event_data = None

    # -- CONECTION & DISCONNECTION:

    __connected = False
    def _draggable_connect(self):
        if not self.__connected:
            delegator = MPLCanvasEventDelegator.wrap_canvas(self._draggable_canvas)

            delegator.connect('button_press_event', self._draggable_on_press)
            delegator.connect('button_release_event', self._draggable_on_release)
            delegator.connect('motion_notify_event', self._draggable_on_motion)

            self.__connected = True

    def _draggable_disconnect(self):
        if self.__connected:
            delegator = MPLCanvasEventDelegator.wrap_canvas(self._draggable_canvas)

            delegator.disconnect('button_press_event', self._draggable_on_press)
            delegator.disconnect('button_release_event', self._draggable_on_release)
            delegator.disconnect('motion_notify_event', self._draggable_on_motion)

            self.__connected = False

    pass #end of class


class DraggableVLine(DraggableMixin):
    """
        A draggable vertical line with a callback called with the new x position
        of the line after the user released it.
    """
    def __init__(self, line, callback=None, window=None):
        super(DraggableVLine, self).__init__(
            artist=line,
            on_dragged=self._on_dragged,
            on_released=self._on_released)
        self.line = line
        self.line_x0 = None
        self.callback = callback
        self.window = window

    def _check_cursor(self, event):
        if self.window is not None:
            change_cursor, _ = self.line.contains(event)
            if not change_cursor:
                self.window.set_cursor(None)
            else:
                arrows = gtk.gdk.Cursor(gtk.gdk.SB_H_DOUBLE_ARROW) #@UndefinedVariable
                self.window.set_cursor(arrows)

    def _draggable_on_motion(self, event):
        super(DraggableVLine, self)._draggable_on_motion(event)
        self._check_cursor(event)

    def _on_dragged(self, (x0, y0), (x1, y1), (x2, y2), event):
        self._check_cursor(event)
        if self.line_x0 == None:
            self.line_x0 = self.line.get_xdata()[0]

        diff = self.convert_display_to_data(x2, 0)[0] - self.convert_display_to_data(x0, 0)[0]
        x = max(self.line_x0 + diff, 0)
        self.line.set_xdata((x, x))

        self.line.figure.canvas.draw()

    def _on_released(self, (x0, y0), (x1, y1), (x2, y2), event):
        self._check_cursor(event)
        if callable(self.callback):
            self.callback(self.line.get_xdata()[0])
        self.line_x0 = None

        # redraw the full figure
        self.line.figure.canvas.draw()

    pass #end of class
