# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# ThreadedTaskBox based on code from Rick Spencer
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gi   
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from mvc.support.cancellable_thread import CancellableThread
from mvc.support.gui_loop import add_timeout_call, remove_timeout_call,\
    run_when_idle


class ThreadedTaskBox(Gtk.Table):
    """
        ThreadedTaskBox: encapsulates a spinner, label and a cancel button for
        threaded tasks.
    """

    __gsignals__ = {
        'cancelrequested' : (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,)), #@UndefinedVariable
        'stoprequested' : (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,)) #@UndefinedVariable
    }

    def __init__(self, cancelable=True, stoppable=False):
        """
            Create a ThreadedTaskBox

            Keyword arguments:
            cancelable -- optional value to determine whether to show cancel button. Defaults to True.
            stoppable -- optional value to determine whether to show the stop button. Default to False.
        """
        super(ThreadedTaskBox, self).__init__()
        self.setup_ui(cancelable=cancelable, stoppable=stoppable)

    def setup_ui(self, cancelable=True, stoppable=False):
        GObject.GObject.__init__(self, 3, 3)
        self.set_row_spacings(10)
        self.set_col_spacings(10)

        self.descrlbl = Gtk.Label(label="Status:")
        self.descrlbl.show()
        self.attach(self.descrlbl, 0, 3, 0, 1, xoptions=Gtk.AttachOptions.FILL, yoptions=0)

        self.spinner = Gtk.Spinner()
        self.spinner.show()
        self.attach(self.spinner, 0, 1, 1, 3, xoptions=0, yoptions=0)

        self.label = Gtk.Label()
        self.label.show()
        self.attach(self.label, 1, 2, 1, 3, xoptions=Gtk.AttachOptions.FILL, yoptions=0)

        self.cancel_button = Gtk.Button(stock=Gtk.STOCK_CANCEL)
        self.cancel_button.set_sensitive(False)
        self.cancel_button.connect("clicked", self.__cancel_clicked)
        if cancelable:
            self.attach(self.cancel_button, 2, 3, 1, 2, xoptions=0, yoptions=0)

        self.stop_button = Gtk.Button(stock=Gtk.STOCK_STOP)
        self.stop_button.set_sensitive(False)
        self.stop_button.connect("clicked", self.__stop_clicked)
        if stoppable:
            self.attach(self.stop_button, 2, 3, 2, 3, xoptions=0, yoptions=0)

        self.set_no_show_all(False)
        self.set_visible(True)
        self.show_all()

    def start(self):
        # Start the spinner
        self.spinner.start()

        # Enable the buttons so the user can try to cancel the task
        self.cancel_button.set_sensitive(True)
        self.stop_button.set_sensitive(True)

    def set_status(self, caption):
        self.label.set_text(caption)

    def stop(self, join=False, cancel=False):
        """
            Stops spinning the spinner and emits the correct event.
        """
        # disable the cancel button since the task is about to be told to stop
        self.cancel_button.set_sensitive(False)
        self.stop_button.set_sensitive(False)

        if cancel:
            self.emit("cancelrequested", self)
        else:
            self.emit("stoprequested", self)

        self.spinner.stop()
        self.label.set_text("Done")

    def cancel(self):
        self.stop(cancel=True)

    def __cancel_clicked(self, widget):
        self.cancel()

    def __stop_clicked(self, widget):
        self.stop()

    pass # end of class

GObject.type_register(ThreadedTaskBox) #@UndefinedVariable
