# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from itertools import izip, imap

import numpy as np
from deap import creator, base, cma, tools

from pyxrd.data.settings import POOL as pool

from .refine_run import RefineRun
from .deap_utils import pyxrd_array, evaluate

# Default settings:
FACTR_LAMBDA = 10
FACTR_INIT_LAMBDA = 20
MAX_INIT_LAMBDA = 300
MIN_INIT_LAMBDA = 100
MAX_LAMBDA = MAX_INIT_LAMBDA
NGEN = 100
STAGN_NGEN = 10
STAGN_TOL = 0.5

# Needs to be shared for multiprocessing to work properly
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

def eaGenerateUpdateStagn(toolbox, ngen, halloffame=None, stats=None,
                     verbose=__debug__, stagn_ngen=10, stagn_tol=0.001, context=None):
    """This is algorithm implements the ask-tell model proposed in 
    [Colette2010]_, where ask is called `generate` and tell is called `update`.
    
    Modified (Mathijs Dumon) so it checks for stagnation.
    
    :param toolbox: A :class:`~deap.base.Toolbox` that contains the evolution
                    operators.
    :param ngen: The number of generation.
    :param stats: A :class:`~deap.tools.Statistics` object that is updated
                  inplace, optional.
    :param halloffame: A :class:`~deap.tools.HallOfFame` object that will
                       contain the best individuals, optional.
    :param verbose: Whether or not to log the statistics.
    :param stagn_gens: The number of generations to check for stagnation
    :param stagn_tol: The maximum tolerance for the last `stagn_gens` best fitnesses.

    :returns: The final population.
    
    The toolbox should contain a reference to the generate and the update method 
    of the chosen strategy.

    .. [Colette2010] Collette, Y., N. Hansen, G. Pujol, D. Salazar Aponte and
       R. Le Riche (2010). On Object-Oriented Programming of Optimizers -
       Examples in Scilab. In P. Breitkopf and R. F. Coelho, eds.:
       Multidisciplinary Design Optimization in Computational Mechanics,
       Wiley, pp. 527-565;

    """

    column_names = ["gen", "evals"]
    if stats is not None:
        column_names += stats.functions.keys()
    if verbose:
        logger = tools.EvolutionLogger(column_names)
        logger.logHeader()

    best_fitnesses = []

    for gen in xrange(ngen):

        # Generate a new population
        population = []
        results = []
        for ind in toolbox.generate():
            result = pool.apply_async(toolbox.evaluate, (ind,))
            population.append(ind)
            results.append(result)

        # Get the fitness results:
        for ind, result in izip(population, results):
            ind.fitness.values = result.get()

        del results # clear some memory

        if halloffame is not None:
            halloffame.update(population)
        # Update the strategy with the evaluated individuals
        toolbox.update(population)
        if stats is not None:
            stats.update(population)
        best = population[0]
        context.update(best, best.fitness.values[0])

        best_fitnesses.append(best.fitness.values)
        if len(best_fitnesses) > (stagn_ngen + 1):
            del best_fitnesses[0]

        if context is not None:
            context.record_state_data([
                ("gen", gen),
                ("pop", len(population)),
                ("min", float(stats.min[-1][-1][-1])),
                ("avg", float(stats.avg[-1][-1][-1])),
                ("max", float(stats.max[-1][-1][-1])),
                ("std", float(stats.std[-1][-1][-1])),
            ] + [ ("par%d" % i, float(val)) for i, val in enumerate(best)])

        if verbose:
            logger.logGeneration(evals=len(population), gen=gen, stats=stats)
        # Check for stagnation
        if gen >= stagn_ngen: # 10
            stagnation = True
            last_fitn = np.array(best_fitnesses[-1])
            for fitn in best_fitnesses[-(stagn_ngen - 1):]:
                fitn = np.array(fitn)
                if np.any(np.abs(fitn - last_fitn) > stagn_tol): # 0.01
                    stagnation = False
                    break
            if stagnation:
                break

    return population

class CustomStrategy(cma.Strategy):

    def generate(self, ind_init):
        """Generate a population from the current strategy using the 
        centroid individual as parent.
        
        :param ind_init: A function object that is able to initialize an
                         individual from a list.
        :returns: an iterator yielding the generated individuals.
        """
        arz = np.random.standard_normal((self.lambda_, self.dim))
        arz = self.centroid + self.sigma * np.dot(arz, self.BD.T)
        for arr in arz:
            yield ind_init(arr)

class RefineCMAESRun(RefineRun):
    """
        The DEAP CMA-ES algorithm implementation with added stagnation thresholds
    """
    name = "CMA-ES refinement"
    description = "This algorithm uses the CMA-ES refinement strategy as implemented by DEAP"

    options = [
        ('Maximum # of generations', 'ngen', int, NGEN, [1, 10000]),
        ('Minimum # of generations', 'stagn_ngen', int, STAGN_NGEN, [1, 10000]),
        ('Fitness stagnation tolerance', 'stagn_tol', float, STAGN_TOL, [0., 100.]),

        ('Lambda factor', 'factr_lambda', int, FACTR_LAMBDA, [1, 10000]),
        ('Init lambda factor', 'factr_init_lambda', int, FACTR_INIT_LAMBDA, [1, 10000]),
        ('Maximum init lambda', 'max_init_lambda', int, MAX_INIT_LAMBDA, [1, 10000]),
        ('Minimum init lambda', 'min_init_lambda', int, MIN_INIT_LAMBDA, [1, 10000]),
    ]

    def run(self, context, ngen=NGEN, stagn_ngen=STAGN_NGEN, stagn_tol=STAGN_TOL,
            factr_lambda=FACTR_LAMBDA, factr_init_lambda=FACTR_INIT_LAMBDA,
            max_init_lambda=MAX_INIT_LAMBDA, min_init_lambda=MIN_INIT_LAMBDA, **kwargs):

        logger.info("Setting up the DEAP CMA-ES refinement algorithm")

        N = len(context.ref_props)
        init_lambda = max(min(N * factr_init_lambda, max_init_lambda), min_init_lambda)
        lambda_ = min(N * factr_lambda, MAX_LAMBDA)

        # Individual generation:
        bounds = np.array(context.ranges)
        creator.create(
            "Individual", pyxrd_array,
            fitness=creator.FitnessMin, # @UndefinedVariable
            context=context,
            min_bounds=bounds[:, 0].copy(),
            max_bounds=bounds[:, 1].copy(),
        )

        # Makes sure individuals stay in-bound:
        def create_individual(lst):
            arr = np.array(lst).clip(bounds[:, 0], bounds[:, 1])
            return creator.Individual(arr) # @UndefinedVariable

        # Toolbox setup:
        toolbox = base.Toolbox()
        toolbox.register("evaluate", evaluate)

        # Setup strategy:
        strategy = CustomStrategy(centroid=context.initial_solution, sigma=2, lambda_=lambda_)

        logger.info("Pre-feeding with a normal distributed population ...")
        # Pre-feed the strategy with a normal distributed population over the entire domain (large population):
        solutions = np.random.normal(size=(init_lambda, N))
        solutions = (solutions - solutions.min()) / (solutions.max() - solutions.min()) # stretch to [0-1] interval
        solutions = bounds[:, 0] + solutions * (bounds[:, 1] - bounds[:, 0])
        logger.info("\t generated solution")
        population = []
        results = []
        for ind in imap(create_individual, solutions):
            result = pool.apply_async(toolbox.evaluate, (ind,))
            population.append(ind)
            results.append(result)
        logger.info("\t queued solutions for evaluation")
        for ind, result in izip(population, results):
            ind.fitness.values = result.get()
        logger.info("\t retrieved all solution evaluations")
        del results # clear some memory
        logger.info("\t updating population")
        strategy.update(population)

        toolbox.register("update", strategy.update)
        toolbox.register("generate", strategy.generate, create_individual)

        logger.info("Creating hall-off-fame and statistics")
        # Hall of fame:
        halloffame = tools.HallOfFame(1)

        # Stats:
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", tools.mean)
        stats.register("std", tools.std)
        stats.register("min", min)
        stats.register("max", max)

        # Get this show on the road:
        if pool is not None:
            toolbox.register("map", lambda f, i: pool.map(f, i, 10))

        logger.info("Running the CMA-ES algorithm...")
        final = eaGenerateUpdateStagn(
            toolbox,
            ngen=ngen,
            stats=stats,
            halloffame=halloffame,
            context=context,
            stagn_ngen=STAGN_NGEN,
            stagn_tol=STAGN_TOL
        )

        fitnesses = toolbox.map(evaluate, final)

        bestf = None
        besti = None
        for ind, fitness in izip(final, fitnesses):
            fitness, = fitness
            if bestf == None or bestf > fitness:
                bestf = float(fitness)
                besti = ind
            context.update(ind, fitness)

        context.last_residual = bestf
        context.last_solution = np.array(besti, dtype=float)

    pass # end of class
