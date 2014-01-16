# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
import scipy

from .refine_run import RefineRun

import logging
logger = logging.getLogger(__name__)

class RefineLBFGSBRun(RefineRun):
    name = "L BFGS B algorithm"
    description = "Refinement using the L BFGS B algorithm"
    options = []

    def run(self, context, **kwargs):
        """
            Refinement using the L BFGS B algorithm
        """
        context.last_solution, context.last_residual, d = scipy.optimize.fmin_l_bfgs_b(# @UnusedVariable
            context.get_residual_for_solution,
            context.initial_solution,
            approx_grad=True,
            bounds=context.ranges,
            iprint=-1,
            epsilon=1e-4,
            callback=context.update
        )
        logger.debug("fmin_l_bfgs_b returned: %s" % d)

    pass # end of class

class RefineBruteForceRun(RefineRun):
    name = "Brute force algorithm"
    description = "Refinement using a Brute Force algorithm"
    options = [
        ('Number of samples', 'num_samples', int, 10, [3, 1000]),
    ]

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

class RefineBasinHoppingRun(RefineRun):

    name = "Basin Hopping Algorithm"
    description = "Refinement using a basin hopping algorithm"
    options = [
         ('Number of iterations', 'niter', int, 100, [10, 10000]),
         ('Temperature criterion', 'T', float, 3.0, [0.0, None]),
         ('Displacement stepsize', 'stepsize', float, 1.0, [0.0, None]),
    ]

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

