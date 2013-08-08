# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import multiprocessing
from time import sleep
from importlib import import_module
from collections import deque
from itertools import product

from threading import Thread, Event
from Queue import Queue, Empty

import numpy as np
import scipy

from .refine_run import RefineRun

class RefineBruteForceRun(RefineRun):
    name="Brute force algorithm"
    description="Refinement using a Brute Force algorithm"
    options=[
        ( 'Number of samples', 'num_samples', int, 11, [3, 1000] ),
    ]


    def run(self, context, num_samples=11, stop=None, **kwargs):
        """
            Refinement using a Brute Force algorithm
        """
        
        pool = multiprocessing.Pool()

        #TODO interpolate best solution ?        
        num_params = len(context.ranges)
        
        npbounds = np.array(context.ranges, dtype=float)
        npmins = npbounds[:,0]
        npranges = npbounds[:,1] - npbounds[:,0]
    
        #Producer thread & queue: (with a maxsize for memory management)
        results = Queue(maxsize=1000)
        producer_stopped = Event()
        def producer(pool, res_queue, mins, ranges):
            for indeces in product(range(num_samples), repeat=num_params):
                if stop.is_set(): break
                npindeces = np.array(indeces, dtype=float) / float(num_samples-1)
                solution = mins + ranges * npindeces
                
                context.apply_solution(solution)
                result = context.mixture.optimizer.get_optimized_residual_async(pool)
                res_queue.put((solution, result))
            producer_stopped.set()

        produce_thread = Thread(target=producer, args=(pool, results, npmins, npranges))
        produce_thread.start() #start producing

        #Fetch loop:
        keep_fetching = True
        while keep_fetching:
            try:
                solution, result = results.get(True, 0.005)
            except Empty:
                if not producer_stopped.is_set():
                    continue #go for another run
                else:
                    keep_fetching = False                        
            else:
                if not stop.is_set():
                    residual = result.get()
                    context.update(solution, residual)
        produce_thread.join()
        context.apply_solution(context.initial_solution)
        
        pool.close()        
        if not stop.is_set():
            pool.join()
        else:
            pool.terminate()
        
    pass #end of class
