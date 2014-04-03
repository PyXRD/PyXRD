# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
import functools
logger = logging.getLogger(__name__)

import numpy as np
import random

from pyxrd.generic.async import HasAsyncCalls

from .deap_cma import RefineCMAESRun
from .refine_run import RefineRun

# IDEALLY, THIS SHOULD BE EQUAL OR LOWER TO NUMBER OF PROCESSES IN THE POOL:
NUM_RUNS = 4
NUM_RESTARTS = 5
STAGN_TOL = 0.01
STAGN_NGEN = 10
NGEN = 100

class RefinePCMAESRun(RefineRun, HasAsyncCalls):
    """
        Algorithm that will run CMA-ES strategies in parallel for a shorter # of
        generations, check them and reset unsuccessful runs.
    """
    name = "Parallel multi-CMA-ES refinement"
    description = "Multiple CMA-ES refinement are run in parallel"

    options = [
        ('Instances', 'num_runs', int, NUM_RUNS, [1, 20]),
        ('Restarts', 'num_restarts', int, NUM_RESTARTS, [1, 10]),
        ('Total # of generations', 'total_ngen', int, NGEN, [1, 10000]),
        ('Minimum # of generations', 'stagn_ngen', int, STAGN_NGEN, [1, 10000]),
        ('Fitness stagnation tolerance', 'stagn_tol', float, STAGN_TOL, [0., 100.]),
    ]

    def _get_args(self, context, start, **kwargs):
        # Fetch a project dump:
        with context.mixture.project.hold_child_signals():
            # Set the current refine method to RefineCMAESRun:
            old_refine_method = context.mixture.refine_method
            old_initial_solution = context.initial_solution
            for i, m in context.mixture.Meta.all_refine_methods.iteritems():
                if isinstance(m, RefineCMAESRun):
                    context.mixture.refine_method = i
                    context.apply_solution(start)
                    break
            # Dump project in its entirety:
            projectf = context.mixture.project.dump_object()
            mixture_index = context.mixture.project.mixtures.index(context.mixture)
            # Reset the old refine method & options:
            context.mixture.refine_method = old_refine_method
            context.apply_solution(old_initial_solution)

            return projectf, mixture_index, kwargs

    def run(self, context, num_runs=NUM_RUNS, num_restarts=NUM_RESTARTS, **kwargs):
        bounds = np.array(context.ranges)
        dim = len(context.ref_props)
        pmin = bounds[:, 0].copy()
        pmax = bounds[:, 1].copy()

        def add_random(coll):
            rnd = np.array([random.uniform(pmin[i], pmax[i]) for i in range(dim)], dtype=float)
            coll.append(rnd)

        # Number of generations per 'reset':
        kwargs["ngen"] = int(kwargs.pop("total_ngen") / num_restarts)

        # Scripts can pass the "bsol" kwarg containing a list
        # of numpy arrays (begin point solutions).
        # If not passed, random staring points are used instead
        bsol = kwargs.pop("bsol", [])
        while len(bsol) < num_runs:
            add_random(bsol)

        from pyxrd.calculations.improve import run_refinement

        context.status_message = "Running Parallel CMA-ES ..."
        context.status = "running"

        for restart in xrange(num_restarts):
            HasAsyncCalls.restart_pool()
            if self._user_cancelled():
                logger.info("User cancelled execution of PCMA-ES, stopping ...")
                break

            # Submit & fetch refinements to/from the multiprocessing system:
            results = [
                    self.submit_async_call(
                        functools.partial(run_refinement,
                        *self._get_args(context, start=bsol[i], **kwargs))
                    )
                    for i in xrange(num_runs)
            ]
            solutions = [self.fetch_async_result(result) for result in results]

            # Reset starting solutions:
            bsol = []
            if not hasattr(context, "pcma_records"):
                setattr(context, "pcma_records", [])
            solutions.sort(key=lambda v: v[1])
            for solution, residual, records in solutions:
                context.pcma_records.append(records)
                context.update(solution, residual)
                bsol.append((residual, solution))

            if restart < num_restarts:
                # Delete the worst three and remove the residuals again
                del bsol[2:]
                bsol = [ solution for residual, solution in bsol ]
                # Add 3 new random points:
                for i in xrange(num_runs - 2):
                    add_random(bsol)

        context.status_message = "PCMA-ES finished ..."
        context.status = "finished"

    pass #end of class
