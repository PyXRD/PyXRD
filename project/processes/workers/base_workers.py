# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import threading
import multiprocessing
from Queue import Empty

from generic.utils import get_new_uuid  

import settings

class PyXRDWorkerMethod(object):
    """
        A wrapper class that can be used to more quickly parallize methods using
        multi-processing. Used in conjunction with PyXRDWorker
    """
    
    def __init__(self, job_queue, result_queue, project):
        super(PyXRDWorkerMethod, self).__init__()
        self.project = project
        self.job_queue = job_queue
        self.result_queue = result_queue
        
    def __call__(self):
        """
            The actual work method
        """
        pass #does nothing by default
        
    def clean(self):
        del self.job_queue
        del self.result_queue
        del self.project
    
    pass #end of class

class PyXRDWorker(object):

    Method = PyXRDWorkerMethod

    def __init__(self, project):
        self.project = project
        
        # Setup the queue's:
        self.job_queue = multiprocessing.JoinableQueue()
        self.result_queue = multiprocessing.JoinableQueue()
               
        # Create a fetch thread:
        self.internal = {}
        self.doubles_check = {}
        self.fetch_thread = threading.Thread(target=self.fetch_results)
        self.stop_event = threading.Event()
        
    def get_setup_args(self):
        """
            Anything returned here nees to be serializable!
        """
        return self.job_queue, self.result_queue
               
    def join(self):
        self.job_queue.join()
        self.result_queue.join()
        self.stop_fetching()
        
    def start_fetching(self):
        self.stop_event.clear()    
        self.fetch_thread.start()
        
    def stop_fetching(self):
        self.stop_event.set()
        self.fetch_thread.join()
        
    def fetch_results(self):
        """
            Threaded function, fetches results from results queue and informs
            other threads waiting for this result. Remains within the
            scope of the main process.
        """
        #Fetch a process solution:
        while not self.stop_event.is_set():
            try:
                key, result = self.result_queue.get(True, 0.005)
            except Empty:
                continue #go for another run if we're still fetching...
            
            #Get the associated dict:
            result_dict = self.internal.pop(key, None)
            if result_dict!=None:
                #Lock the dict, set the result & inform whoever is waiting
                with result_dict["lock"]:
                    result_dict["result"] = result
                    result_dict["lock"].notify()
            
            #Decrement counters:
            self.result_queue.task_done()
        
    def put_on_queue(self, *args):
        """
            Puts a job on the queue and returns a dict containing a Condition 
            lock, which will be notified when the result of the job has been
            fetched. The return value can be found in the 'result' key of the
            dict.
        """
        # Add a unique key to the job so we can send it back where it is needed:
        key = get_new_uuid()
        job = (key, args)

        # Create a lock so the user can wait for the result:
        result_dict = { "lock": threading.Condition() }

        # Store the result dict in an internal dict:
        self.internal[key] = result_dict
        
        #Queue this:
        self.job_queue.put(job)
        
        #Return this so they can listen for the event...
        return result_dict
        
    pass #end of class
