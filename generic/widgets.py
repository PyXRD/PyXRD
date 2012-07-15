# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# ThreadedTaskBox based on code from Rick Spencer
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import types
import gobject
import gtk
from gtk import Entry, HScale, HBox

from gtkmvc.adapters.default import add_adapter

from generic.validators import FloatEntryValidator
from generic.custom_math import round_sig
from generic.utils import delayed
from generic.threads import KillableThread, GUIThread

class ScaleEntry(HBox):
  
    __gsignals__ = { 
        'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
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
        HBox.__init__(self, spacing=5)
        
        self.enforce_range = enforce_range

        if lower==None: lower = 0
        if upper==None: upper = 10
        lower = min(upper, lower)
        upper = max(upper, lower)
        
        step = max((upper-lower)/200.0, 0.01)
        self.adjustment = gtk.Adjustment(
            0.0, lower, upper, step, step, 1.0)
        
        self.scale = gtk.HScale(self.adjustment)
        self.scale.set_draw_value(False)
        self.scale.set_size_request(50, -1)
        self.scale.set_update_policy(gtk.UPDATE_DELAYED)
        self.scale.connect('value-changed', self.on_scale_value_changed)
        
        self.entry = Entry()
        FloatEntryValidator(self.entry)
        self.entry.set_size_request(200,-1)
        self.entry.connect('changed', self.on_entry_changed)
        
        self.set_value(self.scale.get_value())
        
        HBox.pack_start(self, self.scale, expand=False)
        HBox.pack_start(self, self.entry, expand=False)

    def on_scale_value_changed(self, *args, **kwargs):
        self._update_value_and_range(self.scale.get_value())
        return False

    def on_entry_changed(self, *args, **kwargs):
        self._update_value_and_range(self.get_text())
        return False

    def _update_adjustment(self, value, lower, upper):
        step = round_sig(max((upper-lower)/200.0, 0.01))
        self.adjustment.configure(value, lower, upper, 
            step, step, 1.0)

    inhibit_updates = False
    def _update_value_and_range(self, value):
        if not self.inhibit_updates:
            self.inhibit_updates = True   
            #set scale value:
            try: value = float(value)
            except ValueError:
               self.inhibit_updates = False
               return
            lower, upper = self.lower, self.upper
            if not self.enforce_range:
                if value < (lower + abs(lower)*0.05):
                    lower = value - abs(value)*0.2
                if value > (upper - abs(lower)*0.05):
                    upper = value + abs(value)*0.2
            else:
                value = max(min(value, upper), lower)
            self._update_adjustment(value, lower, upper)
            #set entry text:     
            self.entry.set_text(str(self.scale.get_value()))
            #emit 'toplevel' changed signal:
            self._delay_emit_changed()
            self.inhibit_updates = False
        
    @delayed(delay=100)
    def _delay_emit_changed(self):
        self.emit('changed')
        
    def set_value(self, value):
        self.set_text(value)

    def get_value(self):
        return float(self.get_text())

    def set_text(self, text):
        self._update_value_and_range(text)
        
    def get_text(self):
        return float(self.entry.get_text())

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
        
gobject.type_register(ScaleEntry)
add_adapter(ScaleEntry, "changed", ScaleEntry.get_value, ScaleEntry.set_value, types.FloatType)

class ThreadedTaskBox(gtk.Table):
    """
        ThreadedTaskBox: encapsulates a spinner, label, cancel button and a long
        running task. Use an ThreadedTaskBox when you want a window to perform a 
        long running task in the background without freezing the UI for the user.
    """
  
    __gsignals__ = {
        'complete' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'cancelrequested' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
    }
    
    def __init__(self, run_function, gui_callback, complete_callback, params=None, cancelable=True):
        """
            Create an ThreadedTaskBox

            Keyword arguments:
            run_function -- the function to run in threaded mode
            params -- optional dictionary of parameters to be pass into run_function
            cancelable -- optional value to determine whether to show cancel button. Defaults to True.
            Do not use a value with the key of 'kill' in the params dictionary
        """
        self.setup_ui(cancelable=cancelable)

        self.run_function = run_function
        self.gui_callback = gui_callback
        self.complete_callback = complete_callback
        self.pulse_thread = None
        self.work_thread = None
        self.params = params

        self.connect("destroy", self.__destroy)

 
    def setup_ui(self, cancelable=True):
        gtk.Table.__init__(self, 2, 3)
        self.set_row_spacings(10)
        self.set_col_spacings(10)

        self.descrlbl = gtk.Label("Status:")
        self.descrlbl.show()
        self.attach(self.descrlbl, 0, 3, 0, 1, xoptions=gtk.FILL, yoptions=0)

        self.spinner = gtk.Spinner()
        self.spinner.show()
        self.attach(self.spinner, 0, 1, 1, 2, xoptions=0, yoptions=0)

        self.label = gtk.Label()
        self.label.show()
        self.attach(self.label, 1, 2, 1, 2, xoptions=gtk.FILL, yoptions=0)

        self.cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        if cancelable:
            self.cancel_button.show()
        self.cancel_button.set_sensitive(False)
        self.cancel_button.connect("clicked",self.__stop_clicked)
        self.attach(self.cancel_button, 2, 3, 1, 2, xoptions=0, yoptions=0)
 
    def start(self, caption="Working"):
        """
            executes run_function asynchronously and starts the spinner
            Keyword arguments:
            caption -- optional text to display in the label
        """
        #Throw an exception if the user tries to start an operating thread
        if self.pulse_thread != None:
            raise RuntimeError("ThreadedTaskBox already started.")

        self.label.set_text(caption)
        self.spinner.start()

        #Create and start a thread to run the users task
        #pass in a callback and the user's params
        self.work_thread = KillableThread(self.run_function, self.__on_complete, self.params)
        self.work_thread.start()
  
        #create a thread to display the user feedback
        self.pulse_thread = GUIThread(self.gui_function)
        self.pulse_thread.start()

        #enable the button so the user can try to kill the task
        self.cancel_button.set_sensitive( True )
  
    #call back function for after run_function returns
    def __on_complete( self, data ):
        gtk.gdk.threads_enter()
        if callable(self.complete_callback): self.complete_callback(data)
        gtk.gdk.threads_leave()
        self.emit("complete", data)        
        self.kill()

    #call back function for cancel button
    def __stop_clicked( self, widget, data = None ):
        self.cancel()

    def cancel(self):
        self.kill()
        self.emit("cancelrequested", self)

    def gui_function(self):
        if callable(self.gui_callback): self.gui_callback()

    def kill(self, caption="Done"):
        """
            Stops spinning the spinner and sets the value of 'kill' to True in
            the run_function.
        """

        #stop the pulse_thread and remove a reference to it if there is one
        if self.pulse_thread != None:
            self.pulse_thread.kill()
            self.pulse_thread = None

        #disable the cancel button since the task is about to be told to stop
        self.cancel_button.set_sensitive( False )
        #tell the users function tostop if it's thread exists
        if self.work_thread != None:
            self.work_thread.kill()
            
        self.spinner.stop()
        self.label.set_text(caption)

    def __destroy(self, widget, data = None):
        #called when the widget is destroyed, attempts to clean up
        #the work thread and the pulse thread
        if self.work_thread != None:
            self.work_thread.kill()
        if self.pulse_thread != None:
            self.pulse_thread.kill()
            
gobject.type_register(ThreadedTaskBox)

