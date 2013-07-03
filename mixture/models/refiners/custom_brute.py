# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from collections import deque
from itertools import product

from threading import Thread, Event
from Queue import Queue, Empty

import numpy as np
import scipy

from .refine_run import RefineRun

from project.processes.workers import RefineWorker
from project.processes.pool import PyXRDPool

class RefineBruteForceRun(RefineRun):
    name="Brute force algorithm"
    description="Refinement using a Brute Force algorithm"
    options=[
        ( 'Number of samples', 'num_samples', int, 11, [3, 1000] ),
    ]
    
    def _get_pool(self, context):
        project = context.mixture.project
        
        refine_worker = RefineWorker(context.mixture, project)
        
        pool = PyXRDPool(project, workers=[
            refine_worker,
        ])
        return refine_worker, pool
    
    def run(self, context, num_samples=11, **kwargs):
        """
            Refinement using a Brute Force algorithm
        """
               
        #TODO interpolate best solution ?
        
        refine_worker, pool = self._get_pool(context)        
        pool.start()

        num_params = len(context.ranges)
        
        npbounds = np.array(context.ranges, dtype=float)
        npmins = npbounds[:,0]
        npranges = npbounds[:,1] - npbounds[:,0]

        #Producer thread & queue: (with a maxsize for memory management)
        results = Queue(maxsize=1000)
        producer_stopped = Event()
        def producer(refine_worker, res_queue, mins, ranges):
            for indeces in product(range(num_samples), repeat=num_params):
                npindeces = np.array(indeces, dtype=float) / float(num_samples-1)
                solution = mins + ranges * npindeces
                result_dict = refine_worker.put_on_queue(solution)
                res_queue.put((solution, result_dict))
            producer_stopped.set()
            
        produce_thread = Thread(target=producer, args=(refine_worker, results, npmins, npranges))
        produce_thread.start() #start producing
        
        #Fetch loop:
        keep_fetching = True
        while keep_fetching:
            try:
                solution, result_dict = results.get(True, 0.005)
            except Empty:
                if not producer_stopped.is_set():
                    continue #go for another run
                else:
                    keep_fetching = False
            with result_dict['lock']:
                while not 'result' in result_dict:  #TODO add a timeout so this doesn't lock that easily...
                    result_dict['lock'].wait()
                residual = result_dict['result']
            context.dry_update(solution, residual)

        pool.stop()
        del refine_worker, pool
        del results
        del npmins, npranges, npbounds
        
    pass #end of class
