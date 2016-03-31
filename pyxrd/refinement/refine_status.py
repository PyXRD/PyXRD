# coding=UTF-8
# ex:ts=4:sw=4:et=on
import time

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

class RefineStatus(object):
    """
    A status object for a refinement. This should provide some hints
    for the UI to keep track of the status of the refinement.
    
    The error, running and finished flags are mutually exclusive but can be
    False together. When the cancelled flag is set, the user cancelled the
    refinement (the stop signal was set). When the error flag is true, an error
    was encountered during the refinement. When the finished flag is true the 
    refinement has finished successfully. When the running flag is true the 
    refinement is still running. When all three flags are False, the refinement 
    has not started yet.
    
    The status message should be a textual description of these three flags,
    but can be set to any value.
    
    The current error is retrieved from the RefinementHistory instance passed
    in the constructor (it is the residual of the last solution registered).
    
    The best way to use the status object is with a context, like this:
    
     with RefineHistory() as history:
         with RefineStatus(history) as status:
             run_refinement()
             
    """
    
    _error = False
    @property
    def error(self):
        return self._error
    @error.setter
    def error(self, value):
        self._error = bool(value)
        if self._error: 
            self.running = False
            self.cancelled = False
            self.finished = False
    
    _cancelled = False
    @property
    def cancelled(self):
        return self._cancelled
    @cancelled.setter
    def cancelled(self, value):
        self._cancelled = bool(value)
        if self._cancelled: 
            self.running = False
            self.error = False
            self.finished = False
    
    _running = False
    @property
    def running(self):
        return self._running
    @running.setter
    def running(self, value):
        self._running = bool(value)
        if self._running: 
            self.error = False
            self.cancelled = False
            self.finished = False
        
    _finished = False
    @property
    def finished(self):
        return self._finished
    @finished.setter
    def finished(self, value):
        self._finished = bool(value)
        if self._finished:
            self.error = False
            self.cancelled = False
            self.running = False
     
    message = "Not initialized."
    
    @property
    def current_error(self):
        return self.history.last_solution[self.history.RESIDUAL_INDEX]
    
    def __init__(self, history, stop_signal=None):
        assert history is not None, "The RefinementStatus needs a RefinementHistory instance!"
        self.history = history
        self.stop_signal = stop_signal
        self.message = "Initialized."
        
        self.start_time = -1
        self.end_time = -1
    
    def __enter__(self):
        # Set flag
        self.running = True
        # Set message
        self.message = "Running..."
        # Record start time
        self.start_time = time.time()
        # Return us
        return self
        
    def __exit__(self, tp, value, traceback):
        # Record end time
        self.start_time = -1

        if tp is not None:
            self.message = "Refinement error!"
            self.error = True
        else:
            if self.stop_signal is not None and self.stop_signal.is_set():            
                self.message = "Refinement cancelled!"
                self.cancelled = True
            else:
                self.message = "Refinement finished!"
                self.finished = True
    
    def get_total_time(self):
        """ Gets the total time the refinement has run in ms """
        if self.start_time == -1:
            return 0
        else:
            return (self.end_time - self.start_time) * 1000.0
    
    pass #end of class