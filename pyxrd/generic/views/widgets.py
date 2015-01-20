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

from pyxrd.generic.threads import CancellableThread
from pyxrd.generic import pool
pool.get_pool()

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
            cancelable -- optional value to determine whether to show cancel button. Defaults to True.
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
        self.cancel_button.set_sensitive(False)
        self.cancel_button.connect("clicked", self.__cancel_clicked)
        if cancelable:
            self.attach(self.cancel_button, 2, 3, 1, 2, xoptions=0, yoptions=0)

        self.stop_button = gtk.Button(stock=gtk.STOCK_STOP)
        self.stop_button.set_sensitive(False)
        self.stop_button.connect("clicked", self.__stop_clicked)
        if stoppable:
            self.attach(self.stop_button, 2, 3, 2, 3, xoptions=0, yoptions=0)

    def start(self, caption="Working", stop=None):
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
            self.run_function, self.__on_complete, stop=stop)
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
        if not self.stopped and callable(self.gui_callback):
            self.gui_callback()
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
            self.work_thread.cancel()

    pass # end of class

gobject.type_register(ThreadedTaskBox) #@UndefinedVariable
