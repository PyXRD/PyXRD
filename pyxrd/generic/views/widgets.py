# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# ThreadedTaskBox based on code from Rick Spencer
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gobject
import gtk

from threading import Lock

from pyxrd.generic.custom_math import round_sig
from pyxrd.generic.threads import CancellableThread
from pyxrd.generic import pool
pool.get_pool()

class ScaleEntry(gtk.HBox):
    """
        The ScaleEntry combines the generic GtkEntry and GtkScale widgets in
        one widget, with synchronized values and one changed signal.
    """

    __gsignals__ = {
        'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []), #@UndefinedVariable
    }

    @property
    def lower(self):
        return self.adjustment.get_lower()
    @lower.setter
    def lower(self, value):
        return self.adjustment.set_lower(value)

    @property
    def upper(self):
        return self.adjustment.get_upper()
    @upper.setter
    def upper(self, value):
        return self.adjustment.set_upper(value)

    def __init__(self, lower=0, upper=10, enforce_range=False):
        gtk.HBox.__init__(self, spacing=5)

        self.enforce_range = enforce_range

        if lower == None: lower = 0
        if upper == None: upper = 10
        lower = min(upper, lower)
        upper = max(upper, lower)

        step = max((upper - lower) / 200.0, 0.01)
        self.adjustment = gtk.Adjustment(
            0.0, lower, upper, step, step, 0.0)

        self.adjustment.connect('value-changed', self.on_adj_value_changed)

        self.scale = gtk.HScale(self.adjustment)
        self.scale.set_draw_value(False)
        self.scale.set_size_request(50, -1)
        self.scale.set_update_policy(gtk.UPDATE_DELAYED)

        self.entry = gtk.SpinButton(self.adjustment)
        self.entry.set_digits(5)
        self.entry.set_numeric(True)
        self.entry.set_size_request(150, -1)

        self.set_value(self.scale.get_value())

        gtk.HBox.pack_start(self, self.scale, expand=False)
        gtk.HBox.pack_start(self, self.entry, expand=False)
        self.set_focus_chain((self.entry,))


    _idle_changed_id = None
    def _idle_emit_changed(self):
        if self._idle_changed_id is not None:
            gobject.source_remove(self._idle_changed_id)
        self._idle_changed_id = gobject.idle_add(self._emit_changed)

    def _emit_changed(self):
        self.emit('changed')

    def on_adj_value_changed(self, adj, *args):
        self._idle_emit_changed()

    def _update_adjustment(self, lower, upper):
        step = round_sig(max((upper - lower) / 200.0, 0.0005))
        self.adjustment.configure(lower, upper,
            step, step, 0.0)

    def _update_range(self, value):
        lower, upper = self.lower, self.upper
        if not self.enforce_range:
            if value < (lower + abs(lower) * 0.05):
                lower = value - abs(value) * 0.2
            if value > (upper - abs(lower) * 0.05):
                upper = value + abs(value) * 0.2
            self._update_adjustment(lower, upper)

    def set_value(self, value):
        self._update_range(value)
        self.adjustment.set_value(value)

    def get_value(self):
        return self.adjustment.get_value()

    def get_children(self, *args, **kwargs):
        return []
    def add(self, *args, **kwargs):
        raise NotImplementedError
    def add_with_properties(self, *args, **kwargs):
        raise NotImplementedError
    def child_set(self, *args, **kwargs):
        raise NotImplementedError
    def child_get(self, *args, **kwargs):
        raise NotImplementedError
    def child_set_property(self, *args, **kwargs):
        raise NotImplementedError
    def child_get_property(self, *args, **kwargs):
        raise NotImplementedError
    def remove(self, *args, **kwargs):
        raise NotImplementedError
    def set_child_packing(self, *args, **kwargs):
        raise NotImplementedError
    def query_child_packing(self, *args, **kwargs):
        raise NotImplementedError
    def reorder_child(self, *args, **kwargs):
        raise NotImplementedError
    def pack_start(self, *args, **kwargs):
        raise NotImplementedError
    def pack_end(self, *args, **kwargs):
        raise NotImplementedError

    pass # end of class

gobject.type_register(ScaleEntry) #@UndefinedVariable

class ThreadedTaskBox(gtk.Table):
    """
        ThreadedTaskBox: encapsulates a spinner, label, cancel button and a long
        running task. Use an ThreadedTaskBox when you want a window to perform a 
        long running task in the background without freezing the UI for the user.
    """

    __gsignals__ = {
        'complete' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)), #@UndefinedVariable
        'cancelrequested' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)), #@UndefinedVariable
        'stoprequested' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)) #@UndefinedVariable
    }

    def __init__(self, run_function, gui_callback, cancelable=True):
        """
            Create a ThreadedTaskBox

            Keyword arguments:
            run_function -- the function to run in threaded mode
            gui_callback -- a callback that handles the GUI updating
            params -- optional dictionary of parameters to be pass into run_function
            cancelable -- optional value to determine whether to show cancel button. Defaults to True.
            Do not use a value with the key of 'stop' in the params dictionary
        """
        self.setup_ui(cancelable=cancelable)

        self.run_function = run_function
        self.gui_callback = gui_callback
        self.gui_timeout_id = None
        self.work_thread = None

        self.stop_lock = Lock()
        self.stopped = False

        self.connect("destroy", self.__destroy)

    def setup_ui(self, cancelable=True, stoppable=False):
        gtk.Table.__init__(self, 3, 3)
        self.set_row_spacings(10)
        self.set_col_spacings(10)

        self.descrlbl = gtk.Label("Status:")
        self.descrlbl.show()
        self.attach(self.descrlbl, 0, 3, 0, 1, xoptions=gtk.FILL, yoptions=0)

        self.spinner = gtk.Spinner()
        self.spinner.show()
        self.attach(self.spinner, 0, 1, 1, 3, xoptions=0, yoptions=0)

        self.label = gtk.Label()
        self.label.show()
        self.attach(self.label, 1, 2, 1, 3, xoptions=gtk.FILL, yoptions=0)

        self.cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        if cancelable:
            self.cancel_button.show()
        self.cancel_button.set_sensitive(False)
        self.cancel_button.connect("clicked", self.__cancel_clicked)
        self.attach(self.cancel_button, 2, 3, 1, 2, xoptions=0, yoptions=0)

        self.stop_button = gtk.Button(stock=gtk.STOCK_STOP)
        if stoppable:
            self.stop_button.show()
        self.stop_button.set_sensitive(False)
        self.stop_button.connect("clicked", self.__stop_clicked)
        self.attach(self.stop_button, 2, 3, 2, 3, xoptions=0, yoptions=0)


    def start(self, caption="Working"):
        """
            executes run_function asynchronously and starts the spinner
            Keyword arguments:
            caption -- optional text to display in the label
        """
        # Throw an exception if the user tries to start an operating thread
        if self.gui_timeout_id is not None:
            raise RuntimeError("ThreadedTaskBox already started.")

        self.label.set_text(caption)
        self.spinner.start()

        # Create and start a thread to run the users task
        # pass in a callback and the user's args
        self.work_thread = CancellableThread(
            self.run_function, self.__on_complete, stop=pool.pool_stop)
        self.work_thread.start()

        # create a thread to display the user feedback
        self.gui_timeout_id = gobject.timeout_add(250, self.__gui_function)

        # enable the button so the user can try to cancel the task
        self.cancel_button.set_sensitive(True)
        self.stop_button.set_sensitive(True)

    def set_status(self, caption):
        self.label.set_text(caption)

    def stop(self, join=False, cancel=False):
        """
            Stops spinning the spinner and sets the value of 'stop' to True in
            the run_function.
        """
        if self.stop_lock.acquire(False):
            # disable the cancel button since the task is about to be told to stop
            self.cancel_button.set_sensitive(False)
            self.stop_button.set_sensitive(False)
            # tell the users function tostop if it's thread exists
            if self.work_thread is not None:
                self.work_thread.stop()
                if join: self.work_thread.join()
                self.work_thread = None

            if cancel:
                self.emit("cancelrequested", self)
            else:
                self.emit("stoprequested", self)

            self.spinner.stop()
            self.label.set_text("Done")

            self.stopped = True
            self.stop_lock.release()

    def cancel(self):
        self.stop(cancel=True)

    def emit(self, *args):
        # Override the default emit implementation, so this will *always* emit
        # events on the main loop instead of the threaded loop
        gobject.idle_add(gobject.GObject.emit, self, *args) #@UndefinedVariable

    def __gui_function(self):
        if callable(self.gui_callback): self.gui_callback()
        return not self.stopped

    def __on_complete(self, data):
        self.stop()
        self.emit("complete", data)

    def __cancel_clicked(self, widget):
        self.cancel()

    def __stop_clicked(self, widget):
        self.stop(join=True)

    def __destroy(self, widget, data=None):
        # called when the widget is destroyed, attempts to clean up
        # the work thread and the pulse thread
        if self.work_thread is not None:
            self.work_thread.kill()

    pass # end of class

gobject.type_register(ThreadedTaskBox) #@UndefinedVariable
