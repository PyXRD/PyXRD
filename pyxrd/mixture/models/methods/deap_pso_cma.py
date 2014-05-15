# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from pyxrd.generic.async import HasAsyncCalls
import numpy as np

from .refine_run import RefineRun

from .deap_swarm import RefineMPSORun
from .deap_pcma import RefinePCMAESRun

# IDEALLY, THIS SHOULD BE EQUAL OR LOWER TO NUMBER OF PROCESSES IN THE POOL:
PCMA_NUM_RUNS = 4
CMA_STAGN_TOL = 0.001
CMA_STAGN_NGEN = 10
CMA_NGEN = 80
CMA_NUM_RESTARTS = 1

PSO_NGEN = 20
PSO_NSWARMS = 4
PSO_NEXCESS = 4
PSO_NPARTICLES = 10
PSO_CONV_FACTR = 0.3

class RefineMPSOCMAESRun(RefineRun, HasAsyncCalls):
    """
        Algorithm that will first run a MPSO strategy to get a number of different
        starting points which are then used in a parallel CMA-ES run.
    """
    name = "MPSO CMA-ES refinement"
    description = "Multiple PSO chained to a parallel CMA-ES refinement"

    options = [
        ('PSO Maximum # of generations', 'pso_ngen', int, PSO_NGEN, [1, 10000]),
        ('PSO Start # of swarms', 'nswarms', int, PSO_NSWARMS, [1, 50]),
        ('PSO Max # of unconverged swarms', 'nexcess', int, PSO_NEXCESS, [1, 50]),
        ('PSO Swarm size', 'nparticles', int, PSO_NPARTICLES, [1, 50]),
        ('PSO Convergence tolerance', 'conv_factr', float, PSO_CONV_FACTR, [0., 10.]),

        ('PCMA Instances', 'num_runs', int, PCMA_NUM_RUNS, [1, 10000]),
        ('PCMA Restarts', 'num_restarts', int, CMA_NUM_RESTARTS, [0, 10]),
        ('PCMA Total # of generations', 'cma_ngen', int, CMA_NGEN, [1, 10000]),
        ('PCMA Minimum # of generations', 'stagn_ngen', int, CMA_STAGN_NGEN, [1, 10000]),
        ('PCMA Fitness stagnation tolerance', 'stagn_tol', float, CMA_STAGN_TOL, [0., 100.]),

    ]

    def run(self, context, **kwargs):
        pso_kwargs = {}
        for kw in ["pso_ngen", "nswarms", "nexcess", "nparticles", "conv_factr"]:
            pso_kwargs[kw] = kwargs.pop(kw)
        pso_kwargs["ngen"] = pso_kwargs.pop("pso_ngen")
        cma_kwargs = kwargs
        cma_kwargs["total_ngen"] = cma_kwargs.pop("cma_ngen")

        mpso = RefineMPSORun()
        best, population, converged_bests = mpso(context, self._stop, **pso_kwargs) #@UnusedVariable

        bsol = []
        logger.setLevel(logging.INFO)
        logger.info("Multiple PSO converged on these points:")

        for b in converged_bests:
            bsol.append(np.array(b))
            logger.info(" - %r" % list(b))

        cmaes = RefinePCMAESRun()
        cmaes(context, self._stop, bsol=bsol, **cma_kwargs)

        context.status_message = "MPSO/CMA-ES finished ..."
        context.status = "finished"

    pass #end of class
