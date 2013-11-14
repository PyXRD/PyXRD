#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import scipy
import itertools
import random
from copy import deepcopy

from deap import base, creator, tools

from pyxrd.data.settings import POOL as pool

from .deap_utils import pyxrd_array, evaluate
from .refine_run import RefineRun


# Default settings:
NGENS = 100
NSWARMS = 1
NEXCESS = 3
NPARTICLES = 15
CONV_FACTR = 0.3 # 5.*1e-2

# Needs to be shared for multiprocessing to work properly
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

class MultiPSOStrategy(object):

    def generate(self, pclass, dim, pmin, pmax, smin, smax):
        part = pclass(random.uniform(pmin[i], pmax[i]) for i in range(dim))
        part.speed = np.array([random.uniform(smin[i], smax[i]) for i in xrange(dim)])
        return part

    def update(self, part, best, chi, c):
        """
            C ~ scale factor(s)
            Chi ~ recombination factor
        """
        part_pos = np.asarray(part)
        best_pos = np.asarray(best)
        pers_pos = np.asarray(part.best)
        speed = np.asarray(part.speed)

        ce1 = c * np.random.uniform(0, 1, size=len(part))
        ce2 = c * np.random.uniform(0, 1, size=len(part))
        ce1_p = ce1 * np.array(best_pos - part_pos)
        ce1_g = ce2 * np.array(pers_pos - part_pos)

        f = (ce1_p + ce1_g)

        # Calculate velocity:
        a = chi * (f + speed) - speed

        speed = a + speed
        part[:] = part_pos + speed
        part.speed = speed
        del part.fitness.values

    def create_swarm(self, container, func, halloffame, n):
        swarm = container(func() for _ in xrange(n))
        try:
            champion = halloffame[0]
            swarm.best = deepcopy(champion)        # Get the position
            swarm.bestfit.values = champion.fitness.values # Get the fitness
        except IndexError:
            pass # HOF is empty, ignore
        return swarm

    def evaluate_swarm(self, evaluate, swarm, part):
        """ Update swarm's attractors personal best and global best """
        if not part.fitness.valid:
            part.fitness.values = evaluate(part)
        if part.best == None or part.fitness > part.bestfit:
            part.best = creator.Particle(part)          # Get the position
            part.bestfit.values = part.fitness.values   # Get the fitness
        if swarm.best == None or part.fitness > swarm.bestfit:
            swarm.best = creator.Particle(part)         # Get the position
            swarm.bestfit.values = part.fitness.values  # Get the fitness

    def evaluate_fitnesses(self, toolbox, evaluate, swarm, context=None):
        fitnesses = toolbox.map(evaluate, swarm)
        for part, fit in zip(swarm, fitnesses):
            part.fitness.values = fit
            self.evaluate_swarm(evaluate, swarm, part)
            if context: context.update(part, *fit)

def eaMultiPSO(toolbox,
        bounds,
        norms,
        ngens=NGENS,
        nswarms=NSWARMS,
        nexcess=NEXCESS,
        nparticles=NPARTICLES,
        conv_factr=CONV_FACTR,
        stats=None,
        halloffame=None,
        verbose=True):
    """
        Multi-particle-swarm optimization method adapted from the examples found
        in the DEAP project. Employs a T-test (two independent sample lists) to
        differentiate between swarms instead of the diameter and average of the
        swarms. Seemed to work better for scaled parameters (YMMV).
        
        Implementation of the Multiswarm Particle Swarm Optimization algorithm as
        presented in *Blackwell, Branke, and Li, 2008, Particle Swarms for Dynamic
        Optimization Problems.*
        
    """

    # Generate the initial population
    population = [toolbox.swarm(n=nparticles) for _ in range(nswarms)]

    # Evaluate each particle
    for swarm in population:
        toolbox.evaluate_fitnesses(swarm)

    # Stats, hall of fame logging setup:
    if stats:
        stats.update(itertools.chain(*population))
    if halloffame:
        halloffame.update(itertools.chain(*population))

    def get_log_kwargs():
        kwargs = {}
        if stats:
            kwargs['stats'] = stats
        if halloffame is not None:
            try:
                kwargs['champ'] = round(halloffame[0].fitness.values[0], 2)
            except IndexError:
                kwargs['champ'] = None
        return kwargs

    if verbose:
        column_names = ["gen", "nswarm", "uncnvrg"]
        if halloffame is not None:
            column_names.append("champ")
        if stats is not None:
            column_names.extend(stats.functions.keys())
        logger = tools.EvolutionLogger(column_names)
        logger.logHeader()
        logger.logGeneration(gen=0, nswarm=len(population), uncnvrg=0, **get_log_kwargs())

    # The loop
    generation = 1
    while generation < ngens:
        # Convergence check
        not_converged = 0
        worst_swarm_idx = None
        worst_swarm = None
        for i, swarm in enumerate(population):
            # Compute the diameter of the swarm
            std = np.std([ind.fitness.values for ind in swarm])
            if std > conv_factr:
                not_converged += 1
                if not worst_swarm or swarm.bestfit < worst_swarm.bestfit:
                    worst_swarm_idx = i
                    worst_swarm = swarm

        # If all swarms have converged, add a swarm
        if not_converged == 0:
            population.append(toolbox.swarm(n=nparticles))
        # If too many swarms are roaming, remove the worst swarm
        elif not_converged > nexcess:
            population.pop(worst_swarm_idx)

        # Update and evaluate the swarm
        for swarm in population:
            for part in swarm:
                # Not necessary to update if it is a new swarm
                if swarm.best is not None and part.best is not None:
                    toolbox.update(part, swarm.best)
            toolbox.evaluate_fitnesses(swarm)

        stats.update(itertools.chain(*population))
        halloffame.update(itertools.chain(*population))

        # Tell the user something has happened
        if verbose:
            logger.logGeneration(gen=generation, nswarm=len(population), uncnvrg=0, **get_log_kwargs())

        # Apply exclusion
        reinit_swarms = set()
        for s1, s2 in itertools.combinations(range(len(population)), 2):
            # Swarms must have a best and not already be set to reinitialize
            if population[s1].best is not None and population[s2].best is not None and not (s1 in reinit_swarms or s2 in reinit_swarms):

                t, prob = scipy.stats.ttest_ind(population[s1], population[s2])
                if np.all(t < 0.1):
                    if population[s1].bestfit <= population[s2].bestfit:
                        reinit_swarms.add(s1)
                    else:
                        reinit_swarms.add(s2)

        # Reinitialize and evaluate swarms
        for s in reinit_swarms:
            swarm = toolbox.swarm(n=NPARTICLES)
            toolbox.evaluate_fitnesses(swarm)
            population[s] = swarm

        generation += 1

    return [itertools.chain(population)]

class RefineMPSORun(RefineRun):
    """
        The DEAP MPSO algorithm implementation
    """
    name = "MPSO refinement"
    description = "This algorithm uses the MPSO refinement strategy"

    options = [
        ('Maximum # of generations', 'ngens', int, NGENS, [1, 1000]),
        ('Start # of swarms', 'nswarms', int, NSWARMS, [1, 50]),
        ('Max # of unconverged swarms', 'nexcess', int, NEXCESS, [1, 50]),
        ('Swarm size', 'nparticles', int, NPARTICLES, [1, 50]),
        ('Stagnation tolerance', 'stagn_tol', float, CONV_FACTR, [0., 10.]),
    ]

    def run(self, context, **kwargs):

        # Parameters:
        verbose = True
        ndim = len(context.ref_props)
        bounds = np.array(context.ranges)
        norms = np.abs(bounds[:, 1] - bounds[:, 0])

        # Strategy setup
        strategy = MultiPSOStrategy()

        # Particle setup:
        creator.create(
            "Particle", pyxrd_array,
            fitness=creator.FitnessMin,
            speed=list,
            best=None,
            bestfit=creator.FitnessMin,
            context=context,
            min_bounds=bounds[:, 0],
            max_bounds=bounds[:, 1],
        )
        creator.create("Swarm", list, best=None, bestfit=creator.FitnessMin)

        # Hall of fame:
        halloffame = tools.HallOfFame(1)

        # Stats:
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", tools.mean)
        stats.register("std", tools.std)
        stats.register("min", min)
        stats.register("max", max)

        # Our toolbox:
        toolbox = base.Toolbox()
        toolbox.register(
            "particle", strategy.generate, creator.Particle,
            dim=ndim,
            pmin=bounds[:, 0], pmax=bounds[:, 1],
            smin=-norms / 2.0, smax=norms / 2.0
        )
        toolbox.register("swarm", strategy.create_swarm, creator.Swarm, toolbox.particle, halloffame)
        toolbox.register("evaluate", evaluate)
        toolbox.register("update", strategy.update, chi=0.729843788, c=norms / np.amax(norms))
        toolbox.register("evaluate_swarm", strategy.evaluate_swarm, evaluate)
        toolbox.register(
            "evaluate_fitnesses",
            strategy.evaluate_fitnesses, toolbox, evaluate,
            context=context
        )

        if pool is not None:
            toolbox.register("map", pool.map)

        final = eaMultiPSO(
            toolbox, bounds, norms,
            ngens=NGENS,
            nswarms=NSWARMS,
            conv_factr=CONV_FACTR,
            stats=stats,
            halloffame=halloffame,
            verbose=True
        )

    pass # end of class
