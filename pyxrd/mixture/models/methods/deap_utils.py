# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
import functools
logger = logging.getLogger(__name__)

from math import sqrt
from itertools import izip

import numpy as np

from deap import creator, base
from deap.tools import ParetoFront

from pyxrd.calculations.mixture import get_optimized_mixture
from pyxrd.generic.async import HasAsyncCalls

class pyxrd_array(creator._numpy_array):
    """
        Helper DEAP.creator._numpy_array subclass that tracks changes to its
        underlying numerical data object, and if changed gets the corresponding
        data object from the context (if set). Allows for async evaluation of
        fitnesses for PyXRD parameter solutions.
    """
    context = None
    data_object = None
    min_bounds = None
    max_bounds = None

    __in_update = False

    def __init__(self, *args, **kwargs):
        creator._numpy_array.__init__(self, *args, **kwargs)
        self._update()

    def _update(self):
        if hasattr(self, "context") and self.context is not None:
            self.data_object = self.context.get_data_object_for_solution(self)

    def __setitem__(self, i, y):
        y = min(y, self.max_bounds[i])
        y = max(y, self.min_bounds[i])
        creator._numpy_array.__setitem__(self, i, y)
        self._update()

    def __setslice__(self, i, j, y):
        y = np.array(y)
        np.clip(y, self.min_bounds[i:j], self.max_bounds[i:j], y)
        creator._numpy_array.__setslice__(self, i, j, y)
        self._update()

    def __array_finalize__(self, obj):
        self.__init__()
        if not hasattr(self, "context"):
            # The object does not yet have a `.context` attribute
            self.context = getattr(obj, 'context', self.__def_context)
            self._update()

    def __reduce__(self):
        __dict__ = self.__dict__ # @ReservedAssignment
        if "context" in __dict__:
            __dict__ = __dict__.copy() # @ReservedAssignment
            del __dict__["context"]
        return (pyxrd_array, (list(self),), __dict__)

    pass # end of class

import sys
from operator import mul, truediv

class FitnessMin(base.Fitness):
    weights = []

    def getValues(self):
        return tuple(map(truediv, self.wvalues, (-1,) * len(self.wvalues)))

    def setValues(self, values):
        try:
            self.wvalues = tuple(map(mul, values, (-1,) * len(values)))
        except TypeError:
            _, _, traceback = sys.exc_info()
            raise TypeError, ("Both weights and assigned values must be a "
            "sequence of numbers when assigning to values of "
            "%r. Currently assigning value(s) %r of %r to a fitness with "
            "weights %s."
            % (self.__class__, values, type(values), (-1,) * len(values))), traceback

    values = property(getValues, setValues, base.Fitness.delValues,
    ("Fitness values. Use directly ``individual.fitness.values = values`` "
     "in order to set the fitness and ``del individual.fitness.values`` "
     "in order to clear (invalidate) the fitness. The (unweighted) fitness "
     "can be directly accessed via ``individual.fitness.values``."))

    def __eq__(self, other):
        return tuple(self.wvalues) == tuple(other.wvalues)

    pass #end of class

def evaluate(individual):
    """
        individual should be an pyxrd_array subclass 
        (or have a data_object attribute)
    """
    if individual.data_object is not None:
        return get_optimized_mixture(individual.data_object).residuals
    else:
        return 100.,

class PyXRDParetoFront(ParetoFront):

    def get_best_n(self, n):
        inds = []
        for ind in self:
            d = 0.0
            for f in ind.fitness.wvalues:
                d += f ** 2
            d = sqrt(d)
            inds.append((d, ind))

        inds.sort(key=lambda ind:-ind[0])
        return inds[:n]

    def get_best(self):
        _, ind = self.get_best_n(1)[0]
        return ind

    def update(self, population):
        """Update the Pareto front hall of fame with the *population* by adding 
        the individuals from the population that are not dominated by the hall
        of fame. If any individual in the hall of fame is dominated it is
        removed.
        
        :param population: A list of individual with a fitness attribute to
                           update the hall of fame with.
        """
        for ind in population:
            is_dominated = False
            has_twin = False
            to_remove = []
            for i, hofer in enumerate(self):    # hofer = hall of famer
                try:
                    if hofer.fitness.dominates(ind.fitness):
                        is_dominated = True
                        break
                    elif ind.fitness.dominates(hofer.fitness):
                        to_remove.append(i)
                    elif ind.fitness == hofer.fitness and self.similar(ind, hofer):
                        has_twin = True
                        break
                except ValueError:
                    print ind, ind.fitness
                    print hofer, hofer.fitness
                    raise

            for i in reversed(to_remove):       # Remove the dominated hofer
                self.remove(i)
            if not is_dominated and not has_twin:
                self.insert(ind)

class AsyncEvaluatedAlgorithm(HasAsyncCalls):

    def do_async_evaluation(self, population, iter_func, eval_func):
        """ Utility that combines a submit and fetch cycle in a single
        function call"""
        results = []
        if population is None:
            population = []
        for ind in iter_func():
            result = HasAsyncCalls.submit_async_call(functools.partial(eval_func, ind))
            population.append(ind)
            results.append(result)
            if self._user_cancelled(): # Stop submitting new individuals
                break
        for ind, result in izip(population, results):
            ind.fitness.values = HasAsyncCalls.fetch_async_result(result)
        del results

    pass #end of class
