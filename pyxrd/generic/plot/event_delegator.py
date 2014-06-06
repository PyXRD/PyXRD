# coding=UTF-8
# ex:ts=4:sw=4:et

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

class MPLCanvasEventDelegator(object):
    """
        An event delegator object that supports stopping event propagation by
        returning 'True' and setting event handlers as the first.
    """

    canvas = None
    _handler_dict = None

    @classmethod
    def wrap_canvas(cls, canvas):
        delegator = getattr(canvas, "__mpl_canvas_delegator", None)
        if delegator is None:
            delegator = MPLCanvasEventDelegator(canvas)
            setattr(canvas, "__mpl_canvas_delegator", delegator)
        else:
            assert (delegator.canvas == canvas)
        return delegator

    def __init__(self, canvas):
        self.canvas = canvas
        self._handler_dict = {
            "button_press_event": [],
            "button_release_event": [],
            "draw_event": [],
            "key_press_event": [],
            "key_release_event": [],
            "motion_notify_event": [],
            "pick_event": [],
            "resize_event": [],
            "scroll_event": [],
            "figure_enter_event": [],
            "figure_leave_event": [],
            "axes_enter_event": [],
            "axes_leave_event": [],
            "close_event": [],
        }

    def _get_handlers(self, event_name):
        try:
            handlers = self._handler_dict[event_name]
        except KeyError:
            raise ValueError, "Unknown event name!"
        return handlers

    def _handle_event(self, event_name):
        handlers = self._get_handlers(event_name)
        def _event_handler(event):
            for handler in handlers:
                if handler(event): # Returning true stops propagation
                    break
                else:
                    continue
        return _event_handler

    def connect(self, event_name, handler, first=False):
        """
            Connects the given handler with the given event_name.
            If first is set to True the handler will be the first in the list
            of event handlers. There is no absolute guarantee the handler will
            remain the first (e.g. later handlers can also call this with 
            first=True).
        """
        handlers = self._get_handlers(event_name)

        if len(handlers) == 0:
            setattr(self, "_event_id_%s" % event_name, self.canvas.mpl_connect(
                event_name, self._handle_event(event_name)
            ))

        if not first:
            handlers.append(handler)
        else:
            handlers.insert(0, handler)

    def disconnect(self, event_name, handler):
        """
            Disconnects the given handler for the given event_name. 
        """

        handlers = self._get_handlers(event_name)

        try:
            handlers.remove(handler)
        except ValueError:
            logger.warning(
                "Tried to disconnect an unregistered handler `%r` on `%r`" % (
                    handler, self))

        if len(handlers) == 0:
            event_id = getattr(self, "_event_id_%s" % event_name, None)
            if event_id is not None:
                self.canvas.mpl_disconnect(event_id)
            setattr(self, "_event_id_%s" % event_name, None)

    pass # end of class
