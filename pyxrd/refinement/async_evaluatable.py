

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import functools
from itertools import imap, izip

from pyxrd.generic.async.cancellable import Cancellable
from pyxrd.generic.async.has_async_calls import HasAsyncCalls

class AsyncEvaluatable(HasAsyncCalls, Cancellable):
    
    # self.refiner.get_pickled_data_object_for_solution

    def do_async_evaluation(self, iter_func, eval_func, data_func, result_func):
        """ 
            Utility that combines a submit and fetch cycle in a single function
            call.
            iter_func is a generation callback (generates solutions)
            data_func transforms the given solutions to something eval_func can 
              work with (this can be a pass-through operation)
            eval_func evaluates a single (generated) solution (this must be
              picklable)
            result_func receives each solution and its residual as arguments
            
        """
        assert callable(iter_func)
        assert callable(eval_func)
        assert callable(data_func)
        assert callable(result_func)
        
        results = []
        solutions = []
        for solution in iter_func():
            result = self.submit_async_call(functools.partial(
                eval_func, data_func(solution)
            ))
            solutions.append(solution)
            results.append(result)
            if self._user_cancelled(): # Stop submitting new individuals
                break
            
        for solution, result in izip(solutions, imap(self.fetch_async_result, results)): 
            result_func(solution, result)
        
        del results
        
        # Run the garbage collector once for good measure
        import gc
        gc.collect()
        
        return solutions