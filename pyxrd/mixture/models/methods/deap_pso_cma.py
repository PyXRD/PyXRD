# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
from deap.tools import HallOfFame
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import functools, random, copy
from itertools import izip

import numpy as np

from deap import creator, base, tools #@UnresolvedImport

from pyxrd.generic.async import HasAsyncCalls, Cancellable

from .refine_run import RefineRun
from .deap_utils import pyxrd_array, evaluate, FitnessMin
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


class SwarmAlgorithm(HasAsyncCalls):

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

    context = None

    toolbox = None
    stats = None
    verbose = False

    #--------------------------------------------------------------------------
    #    Initialization
    #--------------------------------------------------------------------------
    def __init__(self, toolbox, halloffame, stats, ngen=NGEN, ngen_comm=NGEN_COMM,
                 verbose=__debug__, context=None, stop=None):
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
                    
        :param context: PyXRD refinement context object
    
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
        self.context = context

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
                logger.info("User cancelled execution, stopping ...")
                break

            #ASK: Generate a new population:
            swarms = self._ask()
            #TELL: Update the strategy with the evaluated individuals
            self._tell(swarms)
            #RECORD: For logging:
            self._record(swarms)

        return self.context.best_solution, [ind for population in swarms for ind in population]

    #--------------------------------------------------------------------------
    #    Ask, tell & record:
    #--------------------------------------------------------------------------
    def _ask(self):
        self.gen += 1
        self.context.status_message = "Creating generation #%d" % self.gen
        swarms = []
        self.do_async_evaluation(swarms)
        if self.halloffame is not None:
            self.halloffame.update([ind for population in swarms for ind in population])

        return swarms

    def _tell(self, swarms):
        self.context.status_message = "Updating strategy"
        communicate = bool(self.gen > 0 and self.gen % self.ngen_comm == 0)
        self.toolbox.update(swarms, communicate=communicate)

    def _record(self, swarms):
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

        # Update the context:
        self.context.update(best, best_f)
        self.context.record_state_data([
            ("gen", self.gen),
            ("pop", pop_size),
            ("best", best_f)
        ] + [
            (key, record[key][0]) for key in self.stats.functions.keys()
        ] + [
            ("par%d" % i, float(val)) for i, val in enumerate(best)
        ])

    #--------------------------------------------------------------------------
    #    Async calls:
    #--------------------------------------------------------------------------
    def do_async_evaluation(self, swarms):
        """ Utility that combines a submit and fetch cycle in a single
        function call"""
        if swarms is None:
            swarms = []
        all_results = []
        for generator in self.toolbox.generate():
            results = []
            population = []
            for ind in generator:
                result = self.submit_async_call(functools.partial(
                    self.toolbox.evaluate,
                    self.context.get_pickled_data_object_for_solution(ind)
                ))
                population.append(ind)
                results.append(result)
                if self._user_cancelled(): # Stop submitting new individuals
                    break
            all_results.append(results)
            swarms.append(population)
        for population, results in izip(swarms, all_results):
            for ind, result in izip(population, results):
                ind.fitness.values = self.fetch_async_result(result)
        del all_results

    pass #end of class

class RefinePSOCMAESRun(RefineRun):
    """
        The PS-CMA-ES hybrid algorithm implementation
    """
    name = "PS-CMA-ES refinement"
    description = "This algorithm uses the PS-CMA-ES hybrid refinement strategy"

    options = [
        ('Maximum # of generations', 'ngen', int, NGEN, [1, 10000]),
        ('# of CMA swarms', 'nswarms', int, NSWARMS, [1, 100]),
        ('Communicate each x gens', 'ngen_comm', int, NGEN_COMM, [1, 10000]),
    ]

    def _individual_creator(self, context, num_weights, bounds):
        creator.create(
            "Individual", pyxrd_array,
            fitness=FitnessMin, # @UndefinedVariable
            context=context,
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
    def _setup(self, context, ngen=NGEN, ngen_comm=NGEN_COMM, nswarms=NSWARMS, **kwargs):
        if not self._has_been_setup:
            logger.info("Setting up the DEAP CMA-ES refinement algorithm (ngen=%d)" % ngen)

            # Process some general stuff:
            bounds = np.array(context.ranges) #@UndefinedVariable
            num_weights = len(context.mixture.specimens) + 1
            create_individual = self._individual_creator(context, num_weights, bounds)

            # Setup strategy:

            #TODO make the others random
            parents = [None] * nswarms
            parents[0] = create_individual(context.initial_solution)

            for i in range(1, nswarms):
                parents[i] = create_individual([
                   random.uniform(bounds[j, 0], bounds[j, 1]) for j in range(len(context.initial_solution))
                ])

            strategy = SwarmStrategy(
                parents=parents, sigma=1.0 / 10.0, ranges=bounds,
                stop=self._stop,
            )

            # Toolbox setup:
            toolbox = base.Toolbox()
            toolbox.register("evaluate", evaluate)
            toolbox.register("generate", strategy.generate, create_individual)
            toolbox.register("update", strategy.update)

            # Hall of fame & stats:
            logger.info("Creating hall-off-fame and statistics")
            halloffame = HallOfFame(1, similar=lambda a1, a2: np.all(a1 == a2)) #PyXRDParetoFront(similar=lambda a1, a2: np.all(a1 == a2))
            stats = self._create_stats()

            # Create algorithm
            self.algorithm = SwarmAlgorithm(
                toolbox, halloffame, stats, ngen=ngen, ngen_comm=ngen_comm,
                context=context, stop=self._stop)

            self._has_been_setup = True
        return self.algorithm

    def run(self, context, **kwargs):
        logger.info("CMA-ES run invoked with %s" % kwargs)
        self._has_been_setup = False #clear this for a new refinement
        algorithm = self._setup(context, **kwargs)
        # Get this show on the road:
        logger.info("Running the CMA-ES algorithm...")
        context.status = "running"
        context.status_message = "Running CMA-ES algorithm ..."
        algorithm.run()
        context.status_message = "CMA-ES finished ..."
        context.status = "finished"

    pass # end of class
