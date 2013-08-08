# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

try:
    import cPickle as pickle
except ImportError:
    import pickle

import numpy as np
from deap import creator

from generic.calculations.mixture import get_optimized_residual

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
        if hasattr(self, "context") and self.context!=None:
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
        
    def __array_finalize__(self,obj):
        self.__init__()
        if not hasattr(self, "context"):
            # The object does not yet have a `.context` attribute
            self.context = getattr(obj,'context',self.__def_context)
            self._update()

    def __reduce__(self):
        __dict__ = self.__dict__
        if "context" in __dict__:
            __dict__ = __dict__.copy()
            del __dict__["context"]
        return (pyxrd_array, (list(self),), __dict__)

    pass #end of class

def evaluate(individual):
    """
        individual should be an pyxrd_array subclass 
        (or have a data_object attribute)
    """
    if individual.data_object!=None:
        return get_optimized_residual(individual.data_object),
    else:
        return 100., 
