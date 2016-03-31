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

    def run(self, refiner, maxfun=MAXFUN, maxiter=MAXITER, iprint=IPRINT, **kwargs):
        """
            Refinement using the L BFGS B algorithm
        """
        solution, residual, d = scipy.optimize.fmin_l_bfgs_b(# @UnusedVariable @UndefinedVariable
            refiner.get_residual,
            refiner.history.initial_solution,
            approx_grad=True,
            bounds=refiner.ranges,
            iprint=iprint,
            epsilon=1e-4,
            callback=refiner.update,
            maxfun=maxfun, maxiter=maxiter
        )
        
        refiner.update(solution, residual=residual)
        
        logger.debug("fmin_l_bfgs_b returned: %s" % d)

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
    T = RefineMethodOption('Temperature criterion', 1.0, [0.0, None], int)
    stepsize = RefineMethodOption('Displacement step size', 0.5, [0.0, None], float)

    def run(self, refiner, niter=100, T=1.0, stepsize=0.5, **kwargs):
        """
            Refinement using a Basin Hopping Algorithm
        """
        vals = scipy.optimize.basinhopping(  # @UndefinedVariable
            refiner.get_residual,
            refiner.history.initial_solution,
            niter=niter,
            T=T, # this can be quite large
            stepsize=stepsize,
            minimizer_kwargs={
                'method': 'L-BFGS-B',
                'bounds': refiner.ranges,
            },
            callback=lambda s,r, a: refiner.update(s,r),
        )
        solution = np.asanyarray(vals.x)
        residual = vals.fun
        refiner.update(solution, residual=residual)

    pass # end of class

