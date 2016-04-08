# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import random, copy

import numpy as np

from deap.tools import HallOfFame
from deap import creator, base, tools #@UnresolvedImport

from pyxrd.generic.async.cancellable import Cancellable
from pyxrd.refinement.refine_async_helper import RefineAsyncHelper

from ..refine_method import RefineMethod
from ..refine_method_option import RefineMethodOption

from .deap_utils import pyxrd_array, FitnessMin, result_func
from .deap_cma import Strategy

# Default settings:
NGEN = 100
NGEN_COMM = 5
NSWARMS = 4

class SwarmStrategy(Cancellable):

    def __create_strategy(self, parent, sigma, ranges, **kwargs):
        return Strategy(
            centroid=parent, sigma=sigma, ranges=ranges,
            stop=self._stop, **kwargs
        )

    def __init__(self, parents, sigma, ranges, stop, ** kwargs):
        self.nswarms = len(parents)
        self._stop = stop
        self.strategies = [self.__create_strategy(parents[i], sigma, ranges, **kwargs) for i in range(self.nswarms)]
        self.global_best = None

    def update(self, swarms, communicate=False):
        if self._user_cancelled():
            return

        for i, population in enumerate(swarms):
            self.strategies[i].update(population)
            # Keep track of the global best:
            best = population[0]
            if self.global_best == None or self.global_best.fitness < best.fitness:
                self.global_best = copy.deepcopy(best)

        if communicate:
            for i, population in enumerate(swarms):
                self.strategies[i].rotate_and_bias(self.global_best)

    def generate(self, ind_init):
        for strategy in self.strategies:
            yield strategy.generate(ind_init)

    pass #end of class


class SwarmAlgorithm(RefineAsyncHelper):

    @property
    def ngen(self):
        return self._ngen
    @ngen.setter
    def ngen(self, value):
        self._ngen = value
        logger.info("Setting ngen to %d" % value)
    _ngen = 100

    gen = -1
    halloffame = None

    refiner = None

    toolbox = None
    stats = None
    verbose = False

    #--------------------------------------------------------------------------
    #    Initialization
    #--------------------------------------------------------------------------
    def __init__(self, toolbox, halloffame, stats, ngen=NGEN, ngen_comm=NGEN_COMM,
                 verbose=__debug__, refiner=None, stop=None):
        """
        :param toolbox: A :class:`~deap.base.Toolbox` that contains the evolution
                        operators.
        :param ngen: The number of generations.
        :param ngen_comm: At each multiple generation of this number swarms will
                         communicate
        :param halloffame: A :class:`~deap.tools.ParetoFront` object that will
                           contain the best individuals.
        :param stats: A :class:`~deap.tools.Statistics` object that is updated
                      inplace.
        :param verbose: Whether or not to log the statistics.
                    
        :param refiner: PyXRD refiner object
    
        :returns: The best individual and the final population.
        
        The toolbox should contain a reference to the generate and the update method 
        of the chosen strategy.
        
        Call the run() method when the algorithm should be run.
    
        .. [Colette2010] Collette, Y., N. Hansen, G. Pujol, D. Salazar Aponte and
           R. Le Riche (2010). On Object-Oriented Programming of Optimizers -
           Examples in Scilab. In P. Breitkopf and R. F. Coelho, eds.:
           Multidisciplinary Design Optimization in Computational Mechanics,
           Wiley, pp. 527-565;
    
        """
        self.stats = stats
        self.toolbox = toolbox
        self.ngen = ngen
        self.ngen_comm = ngen_comm
        self.halloffame = halloffame
        self.verbose = verbose
        self.refiner = refiner

        self.gen = 0

        self._stop = stop

    #--------------------------------------------------------------------------
    #    Run method:
    #--------------------------------------------------------------------------
    def run(self):
        """Will run this algorithm"""
        if self.verbose:
            column_names = ["gen", "evals", "best"]
            if self.stats is not None:
                column_names += self.stats.functions.keys()
            self.logbook = tools.Logbook()
            self.logbook.header = column_names

        for _ in range(self.ngen):
            # Check if the user has cancelled:
            if self._user_cancelled():
                self.refiner.status.message = "Stopping..."
                logger.info("User cancelled execution, stopping ...")
                break

            #ASK: Generate a new population:
            swarms = self._ask()
            #TELL: Update the strategy with the evaluated individuals
            self._tell(swarms)
            #RECORD: For logging:
            self._record(swarms)

        return self.refiner.history.best_solution, [ind for population in swarms for ind in population]

    #--------------------------------------------------------------------------
    #    Ask, tell & record:
    #--------------------------------------------------------------------------
    def _ask(self):
        self.gen += 1
        self.refiner.status.message = "Creating generation #%d" % self.gen

        swarms = []
        def iter_func():
            for generator in self.toolbox.generate():
                swarm = []
                for solution in generator:
                    swarm.append(solution)
                    yield solution
                swarms.append(swarm)

        def result_f(*args):
            self.refiner.update(*args)
            result_func(*args)

        population = self.do_async_evaluation(iter_func=iter_func, result_func=result_f)

        if self.halloffame is not None:
            self.halloffame.update(population)

        del population

        return swarms

    def _tell(self, swarms):
        self.refiner.status.message = "Updating strategy"
        communicate = bool(self.gen > 0 and self.gen % self.ngen_comm == 0)
        self.toolbox.update(swarms, communicate=communicate)

    def _record(self, swarms):
        self.refiner.status.message = "Processing ..."

        # Get the best solution so far:
        if hasattr(self.halloffame, "get_best"):
            best = self.halloffame.get_best()
        else:
            best = self.halloffame[0]
        best_f = best.fitness.values[0]

        flat_pop = [ind for population in swarms for ind in population]
        pop_size = len(flat_pop)

        # Calculate stats & print something if needed:
        record = self.stats.compile(flat_pop)
        if self.verbose:
            self.logbook.record(gen=self.gen, evals=pop_size, best=best_f, **record)
            print self.logbook.stream


        self.refiner.status.message = "Refiner update ..."
        # Update the refiner history:
        self.refiner.update(best, iteration=self.gen, residual=best_f)

    pass #end of class

class RefinePSOCMAESRun(RefineMethod):
    """
        The PS-CMA-ES hybrid algorithm implementation
    """
    name = "PS-CMA-ES refinement"
    description = "This algorithm uses the PS-CMA-ES hybrid refinement strategy"
    index = 6
    disabled = False

    ngen = RefineMethodOption('Maximum # of generations', NGEN, [1, 10000], int)
    nswarms = RefineMethodOption('# of CMA swarms', NSWARMS, [1, 100], int)
    ngen_comm = RefineMethodOption('Communicate each x gens', NGEN_COMM, [1, 10000], int)

    def _individual_creator(self, refiner, bounds):
        creator.create(
            "Individual", pyxrd_array,
            fitness=FitnessMin, # @UndefinedVariable
            refiner=refiner,
            min_bounds=bounds[:, 0].copy(),
            max_bounds=bounds[:, 1].copy(),
        )

        def create_individual(lst):
            arr = np.array(lst).clip(bounds[:, 0], bounds[:, 1]) #@UndefinedVariable
            return creator.Individual(arr) # @UndefinedVariable

        return create_individual

    def _create_stats(self):
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0) #@UndefinedVariable
        stats.register("std", np.std, axis=0) #@UndefinedVariable
        stats.register("min", np.min, axis=0) #@UndefinedVariable
        stats.register("max", np.max, axis=0) #@UndefinedVariable
        return stats

    _has_been_setup = False
    def _setup(self, refiner, ngen=NGEN, ngen_comm=NGEN_COMM, nswarms=NSWARMS, **kwargs):
        if not self._has_been_setup:
            logger.info("Setting up the DEAP CMA-ES refinement algorithm (ngen=%d)" % ngen)
            refiner.status.message = "Setting up algorithm..."

            # Process some general stuff:
            bounds = np.array(refiner.ranges) #@UndefinedVariable
            create_individual = self._individual_creator(refiner, bounds)

            # Setup strategy:

            #TODO make the others random
            parents = [None] * nswarms
            parents[0] = create_individual(refiner.history.initial_solution)

            for i in range(1, nswarms):
                parents[i] = create_individual([
                   random.uniform(bounds[j, 0], bounds[j, 1]) for j in range(len(refiner.history.initial_solution))
                ])

            strategy = SwarmStrategy(
                parents=parents, sigma=1.0 / 10.0, ranges=bounds,
                stop=self._stop,
            )

            # Toolbox setup:
            toolbox = base.Toolbox()
            toolbox.register("generate", strategy.generate, create_individual)
            toolbox.register("update", strategy.update)

            # Hall of fame & stats:
            logger.info("Creating hall-off-fame and statistics")
            halloffame = HallOfFame(1, similar=lambda a1, a2: np.all(a1 == a2)) #PyXRDParetoFront(similar=lambda a1, a2: np.all(a1 == a2))
            stats = self._create_stats()

            # Create algorithm
            self.algorithm = SwarmAlgorithm(
                toolbox, halloffame, stats, ngen=ngen, ngen_comm=ngen_comm,
                refiner=refiner, stop=self._stop)

            self._has_been_setup = True
        return self.algorithm

    def run(self, refiner, **kwargs):
        logger.info("CMA-ES run invoked with %s" % kwargs)
        self._has_been_setup = False #clear this for a new refinement
        algorithm = self._setup(refiner, **kwargs)
        # Get this show on the road:
        logger.info("Running the CMA-ES algorithm...")
        algorithm.run()

    pass # end of class
