# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from math import sqrt

import sys
from operator import mul, truediv

import numpy as np

from deap import creator, base
from deap.tools import ParetoFront

class pyxrd_array(creator._numpy_array):
    """
        Helper DEAP.creator._numpy_array subclass that tracks changes to its
        underlying numerical data object, and if changed gets the corresponding
        data object from the context (if set). Allows for async evaluation of
        fitnesses for PyXRD parameter solutions.
    """
    min_bounds = None
    max_bounds = None

    def to_ndarray(self):
        return np.ndarray.copy(self)

    def __setitem__(self, i, y):
        y = min(y, self.max_bounds[i])
        y = max(y, self.min_bounds[i])
        creator._numpy_array.__setitem__(self, i, y)

    def __setslice__(self, i, j, y):
        y = np.array(y)
        np.clip(y, self.min_bounds[i:j], self.max_bounds[i:j], y)
        creator._numpy_array.__setslice__(self, i, j, y)

    pass # end of class

def result_func(individual, fitness):
    individual.fitness.values = fitness

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
        # Run the garbage collector once for good measure
        import gc
        gc.collect()
