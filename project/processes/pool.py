# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.
from __future__ import print_function

import threading
import multiprocessing
from Queue import Empty

from generic.utils import get_new_uuid

from .process import project_run

import settings

class PyXRDPool(object):

    def __init__(self, project, workers=[], process_count=settings.MULTI_CORES):
        print("Preparing multi processing environment...")     
        
        projectf = project.dump_object(zipped=True)

        self.workers = workers

        self.stop_processing = multiprocessing.Event()

        self.processes = []
        self.process_count = process_count
        for i in range(self.process_count):        
            print("Setting up process %d..." % i)
            process = multiprocessing.Process(
                target=project_run,
                args=(
                    projectf.getvalue(),
                    self.stop_processing,
                    [ (worker.Method, worker.get_setup_args()) for worker in workers ],
                )
            )
            process.daemon = True
            self.processes.append(process)

        projectf.close() # free resources

        print("Multi processing setup finished.")

    def start(self):
        print("Starting processes.")

        for i in range(self.process_count):
            self.processes[i].start()
            
        for worker in self.workers:
            worker.start_fetching()
                            
    def stop(self):
        #Finish consumers:

        print("Joining fetchers.")
        for worker in self.workers:
            worker.join()
        
        self.stop_processing.set()
        for i in range(self.process_count):
            print("Stopping process %d." % i)
            try:
                self.processes[i].join(0.5)
            except:
                self.processes[i].terminate()



    pass #end of class
