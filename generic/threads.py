# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# Based on code from Rick Spencer
# Copyright (c) 2013, Mathijs Dumon, Rick Spencer
# All rights reserved.
# Complete license can be found in the LICENSE file.

import time
import gtk
from threading import Thread

class GUIThread(Thread):
    """
        Class for use by ThreadedTaskBox. Not for general use.
    """
    def __init__(self, gui_callback):
        Thread.__init__(self)
        self.setDaemon(True)
        self.gui_callback = gui_callback
        self.__kill = False

    def kill(self):
        self.__kill = True

    #As a subclass of Thread, this function runs when start() is called
    #It will cause the spinner to pulse, showing that a task is running
    def run(self):
        while not self.__kill:
            time.sleep(.1)
            gtk.gdk.threads_enter()
            self.gui_callback()
            while gtk.events_pending():
                gtk.main_iteration(False)
            gtk.gdk.threads_leave()
        
    pass #end of class

class KillableThread(Thread):
    """
        Class for use by ThreadedTaskBox. Not for general use.
    """
    def __init__(self, run_function, on_complete, params=None):
        Thread.__init__(self)
        self.setDaemon(True)
        self.run_function = run_function
        self.params = params
        self.on_complete = on_complete

    #As a subclass of Thread, this function runs when start() is called
    #It will run the user's function on this thread
    def run(self):
        #set up params and include the kill flag
        if self.params == None:
            self.params = {}
        self.params["kill"] = False
        self.params["stop"] = False
        #tell the function to run
        data = self.run_function(self.params)
        #return any data from the function so it can be sent in the complete signal
        self.on_complete(data)

    #Tell the user's function that it should stop
    #Note the user's function may not check this
    def kill(self):
        self.params["kill"] = True
        
    def stop(self):
        self.params["stop"] = True

    pass #end of class
