# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from importlib import import_module
from collections import deque
import functools
from itertools import product, izip

import numpy as np
import scipy

from pyxrd.calculations.mixture import get_optimized_mixture

from .refine_run import RefineRun
from pyxrd.generic.async import HasAsyncCalls

        
def evaluate(data_object):
    return get_optimized_mixture(data_object).residual

class RefineBruteForceRun(RefineRun, HasAsyncCalls):
    name="Brute force algorithm"
    description="Refinement using a Brute Force algorithm"
    options=[
        ( 'Number of samples', 'num_samples', int, 11, [3, 1000] ),
    ]


    def run(self, context, num_samples=11, stop=None, **kwargs):
        """
            Refinement using a Brute Force algorithm
        """

        #TODO interpolate best solution ?        
        num_params = len(context.ranges)
        
        npbounds = np.array(context.ranges, dtype=float)
        npmins = npbounds[:,0]
        npranges = npbounds[:,1] - npbounds[:,0]
    
        #Producer thread & queue: (with a maxsize for memory management)
        
        solutions = []
        
        self.context = context
        
        def generate():
            for indeces in product(range(num_samples), repeat=num_params):
                if self._user_cancelled(): break
                npindeces = np.array(indeces, dtype=float) / float(num_samples-1)
                solution = npmins + npranges * npindeces
                yield context.get_data_object_for_solution(solution), solution
        
        self.do_async_evaluation(solutions, generate, evaluate)        
        context.apply_solution(context.initial_solution)
        
        del self.context
              
    def do_async_evaluation(self, solutions, iter_func, eval_func):
        """ Utility that combines a submit and fetch cycle in a single
        function call"""
        results = []
        if solutions is None:
            solutions = []
        for data_object, solution in iter_func():
            result = HasAsyncCalls.submit_async_call(functools.partial(eval_func, data_object))
            solutions.append(solution)
            results.append(result)
            if self._user_cancelled(): # Stop submitting new individuals
                break
        for solution, result in izip(solutions, results):
            residual = HasAsyncCalls.fetch_async_result(result)
            self.context.update(solution, residual)
            self.context.record_state_data([
                ("param%d" % d, solution[d]) for d in range(solution.size)
            ] + [
                ("residual", residual)
            ])
        pass # end of method
        
    pass #end of class
