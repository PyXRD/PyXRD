# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
import scipy

from ..refine_method import RefineMethod
from ..refine_method_option import RefineMethodOption

import logging
logger = logging.getLogger(__name__)

MAXFUN = 15000
MAXITER = 15000
IPRINT = 0

class RefineLBFGSBRun(RefineMethod):
    """
        An implementation of the L BFGS B refinement algorithm.
    """

    name = "L BFGS B algorithm"
    description = "Refinement using the L BFGS B algorithm"
    index = 0
    disabled = False

    maxfun = RefineMethodOption('Maximum # of function calls', MAXFUN, [1, 1000000], int)
    maxiter = RefineMethodOption('Maximum # of iterations', MAXITER, [1, 1000000], int)
    iprint = RefineMethodOption('Output level [-1,0,1]', IPRINT, [-1, 1], int)

    def run(self, context, maxfun=MAXFUN, maxiter=MAXITER, iprint=IPRINT, **kwargs):
        """
            Refinement using the L BFGS B algorithm
        """
        context.last_solution, context.last_residual, d = scipy.optimize.fmin_l_bfgs_b(# @UnusedVariable
            context.get_residual_for_solution,
            context.initial_solution,
            approx_grad=True,
            bounds=context.ranges,
            iprint=iprint,
            epsilon=1e-4,
            callback=context.update,
            maxfun=maxfun, maxiter=maxiter
        )
        logger.debug("fmin_l_bfgs_b returned: %s" % d)

    pass # end of class

class RefineBruteForceRun(RefineMethod):
    """
        An implementation of the Brute Force refinement algorithm.
    """

    name = "Brute force algorithm"
    description = "Refinement using a Brute Force algorithm"
    index = 3
    disabled = False

    num_samples = RefineMethodOption('Number of samples', 10, [3, 1000], int)

    def run(self, context, num_samples=10, **kwargs):
        """
            Refinement using a Brute Force algorithm
        """
        vals = scipy.optimize.brute(
            context.get_residual_for_solution,
            context.ranges,
            Ns=num_samples,
            full_output=True,
            finish=None
        )
        try:
            context.last_solution = np.ndarray(list(vals[0]))
        except TypeError:
            context.last_solution = np.ndarray([vals[0]])
        context.last_residual = vals[1]

    pass # end of class

class RefineBasinHoppingRun(RefineMethod):
    """
        An implementation of the Basin Hopping refinement algorithm.
    """

    name = "Basin Hopping Algorithm"
    description = "Refinement using a basin hopping algorithm"
    index = 4
    disabled = False

    niter = RefineMethodOption('Number of iterations', 100, [10, 10000], int)
    T = RefineMethodOption('Temperature criterion', 3.0, [0.0, None], int)
    stepsize = RefineMethodOption('Displacement step size', 1.0, [0.0, None], float)

    def run(self, context, niter=100, T=3.0, stepsize=1.0, **kwargs):
        """
            Refinement using a Basin Hopping Algorithm
        """
        vals = scipy.optimize.basinhopping(
            context.get_residual_for_solution,
            context.initial_solution,
            niter=niter,
            T=T, # this can be quite large
            stepsize=stepsize,
            minimizer_kwargs={
                'method': 'L-BFGS-B',
                'bounds': context.ranges,
            }
        )
        context.last_solution = np.asanyarray(vals.x)
        context.last_residual = vals.fun

    pass # end of class

