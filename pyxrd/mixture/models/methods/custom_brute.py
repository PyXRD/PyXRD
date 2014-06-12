# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import functools
from itertools import product, izip, combinations

import numpy as np

from pyxrd.calculations.mixture import get_optimized_mixture

from .refine_run import RefineRun
from pyxrd.generic.async import HasAsyncCalls


def evaluate(data_object):
    return get_optimized_mixture(data_object).residual

class RefineBruteForceRun(RefineRun, HasAsyncCalls):
    name = "Brute force algorithm"
    description = "Refinement using a Brute Force algorithm"
    options = [
        ('Number of samples', 'num_samples', int, 11, [3, 1000]),
    ]


    def run(self, context, num_samples=11, stop=None, **kwargs):
        """
            Refinement using a Brute Force algorithm
        """

        #TODO interpolate best solution ?
        num_params = len(context.ranges)

        npbounds = np.array(context.ranges, dtype=float)
        npmins = npbounds[:, 0]
        npranges = npbounds[:, 1] - npbounds[:, 0]

        solutions = []

        self.context = context

        #TODO: single parameter refinement!!

        def generate():

            for par1, par2 in combinations(range(num_params), 2):
                indeces = np.zeros(shape=(num_params,))
                print "COMBO:", par1, par2
                for par_indeces in product(range(num_samples), repeat=2):
                    print par_indeces
                    indeces[par1] = par_indeces[0]
                    indeces[par2] = par_indeces[1]
                    npindeces = np.array(indeces, dtype=float) / float(num_samples - 1)
                    solution = npmins + npranges * npindeces
                    yield context.get_data_object_for_solution(solution), solution


            """for indeces in product(range(num_samples), repeat=num_params):
                if self._user_cancelled(): break
                npindeces = np.array(indeces, dtype=float) / float(num_samples - 1)
                solution = npmins + npranges * npindeces
                yield context.get_data_object_for_solution(solution), solution"""

        self.do_async_evaluation(solutions, generate, evaluate)
        context.apply_solution(context.initial_solution)

        del self.context

    def do_async_evaluation(self, solutions, iter_func, eval_func, max_stacked=100):
        """ Utility that combines a submit and fetch cycle in a single
        function call"""
        results = []
        if solutions is None:
            solutions = []

        def process_results(solutions, results):
            for solution, result in izip(solutions, results):
                residual = HasAsyncCalls.fetch_async_result(result)
                self.context.update(solution, residual)
                self.context.record_state_data([
                    ("param%d" % d, solution[d]) for d in range(solution.size)
                ] + [
                    ("residual", residual)
                ])

        num_stacked = 0
        for data_object, solution in iter_func():
            result = HasAsyncCalls.submit_async_call(functools.partial(eval_func, data_object))
            solutions.append(solution)
            results.append(result)
            num_stacked += 1
            if num_stacked >= max_stacked:
                process_results(solutions, results)
                num_stacked = 0
                solutions = []
                results = []
            if self._user_cancelled(): # Stop submitting new individuals
                break

        if num_stacked > 0:
            process_results(solutions, results)

        pass # end of method

    pass #end of class
