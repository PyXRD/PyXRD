# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from math import log

import numpy as np
import scipy

from deap import creator, base, cma, tools #@UnresolvedImport

from .refine_run import RefineRun
from .deap_utils import pyxrd_array, evaluate, AsyncEvaluatedAlgorithm, PyXRDParetoFront, FitnessMin

# Default settings:
NGEN = 100
STAGN_NGEN = 10
STAGN_TOL = 0.001

class Strategy(cma.StrategyOnePlusLambda):
    """
        This evolutionary strategy is nothing more then a 
        One+Lambda with a modified generate() function that will
        return a generator instead of an evaluated list.
        This allows for more efficient parallel computing (only generate the
        next individual when needed) on larger population sizes.
    """

    def __init__(self, centroid, sigma, **kwargs):
        if not "lambda_" in kwargs:
            kwargs["lambda_"] = int(25 + min(3 * log(len(centroid)), 75)) #@UndefinedVariable
        super(Strategy, self).__init__(centroid, sigma, ** kwargs)

    def generate(self, ind_init):
        """Generate a population from the current strategy using the 
        centroid individual as parent.
        
        :param ind_init: A function object that is able to initialize an
                         individual from a list.
        :returns: an iterator yielding the generated individuals.
        """
        arz = np.random.standard_normal((self.lambda_, self.dim)) #@UndefinedVariable
        arz = np.array(self.parent) + self.sigma * np.dot(arz, self.A.T) #@UndefinedVariable
        for arr in arz:
            yield ind_init(arr)

class Algorithm(AsyncEvaluatedAlgorithm):
    """
        This algorithm implements the ask-tell model proposed in 
        [Colette2010]_, where ask is called `generate` and tell is called `update`.
        
        Modified (Mathijs Dumon) so it checks for stagnation.
    """

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
    stagn_ngen = None
    stagn_tol = None
    verbose = False

    #--------------------------------------------------------------------------
    #    Initialization
    #--------------------------------------------------------------------------
    def __init__(self, toolbox, halloffame, stats, ngen=NGEN,
                         verbose=__debug__, stagn_ngen=STAGN_NGEN,
                         stagn_tol=STAGN_TOL, context=None, stop=None):
        """
        :param toolbox: A :class:`~deap.base.Toolbox` that contains the evolution
                        operators.
        :param ngen: The number of generations.
        :param halloffame: A :class:`~deap.tools.ParetoFront` object that will
                           contain the best individuals.
        :param stats: A :class:`~deap.tools.Statistics` object that is updated
                      inplace.
        :param verbose: Whether or not to log the statistics.
        :param stagn_gens: The minimum number of generations to wait before
                            checking for stagnation
        :param stagn_tol: The stagnation tolerance. Higher values means a 
                            harsher tolerance, values should fall between 0 and 1
                    
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
        self.halloffame = halloffame
        self.verbose = verbose
        self.stagn_ngen = stagn_ngen
        self.stagn_tol = stagn_tol
        self.context = context

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
            population = self._ask()
            #TELL: Update the strategy with the evaluated individuals
            self._tell(population)
            #RECORD: For stagnation checking & logging:
            self._record(population)
            #CHECK: whether we are stagnating:
            if self._is_stagnating():
                logging.info("CMA: stagnation detected!")
                break

        return self.context.best_solution, population

    #--------------------------------------------------------------------------
    #    Stagnation calls:
    #--------------------------------------------------------------------------
    def _is_flat(self, yvals, xvals, slope_tolerance=0.001):
        slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(xvals, yvals) #@UndefinedVariable @UnusedVariable
        val = bool(abs(slope) <= slope_tolerance)
        return val

    def _is_stagnating(self):
        self.context.status_message = "Checking for stagnation"
        if self.gen >= self.stagn_ngen: # 10
            std, best = self.logbook.select("std", "best")
            std = np.array(std)[:, 0]
            yvals1 = std[-(self.stagn_ngen - 1):]
            xvals1 = range(len(yvals1))
            yvals2 = best[-(self.stagn_ngen - 1):]
            xvals2 = range(len(yvals2))
            return self._is_flat(yvals1, xvals1, self.stagn_tol) and \
                self._is_flat(yvals2, xvals2, self.stagn_tol)
        else:
            return False

    #--------------------------------------------------------------------------
    #    Ask, tell & record:
    #--------------------------------------------------------------------------
    def _ask(self):
        self.gen += 1
        self.context.status_message = "Creating generation #%d" % (self.gen + 1)
        population = []
        self.do_async_evaluation(population)
        if self.halloffame is not None:
            self.halloffame.update(population)

        return population

    def _tell(self, population):
        self.context.status_message = "Updating strategy"
        self.toolbox.update(population)

    def _record(self, population):
        # Get the best solution so far:
        best = self.halloffame.get_best()
        best_f = best.fitness.values[0]
        pop_size = len(population)

        # Calculate stats & print something if needed:
        record = self.stats.compile(population)
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
    def do_async_evaluation(self, population):
        super(Algorithm, self).do_async_evaluation(
            population, self.toolbox.generate, self.toolbox.evaluate)

    pass #end of class

class RefineCMAESRun(RefineRun):
    """
        The DEAP CMA-ES algorithm implementation with added stagnation thresholds
    """
    name = "CMA-ES refinement"
    description = "This algorithm uses the CMA-ES refinement strategy as implemented by DEAP"

    options = [
        ('Maximum # of generations', 'ngen', int, NGEN, [1, 10000]),
        ('Minimum # of generations', 'stagn_ngen', int, STAGN_NGEN, [1, 10000]),
        ('Fitness slope tolerance', 'stagn_tol', float, STAGN_TOL, [0., 100.]),
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
    def _setup(self, context, ngen=NGEN, stagn_ngen=STAGN_NGEN, stagn_tol=STAGN_TOL, **kwargs):
        if not self._has_been_setup:
            logger.info("Setting up the DEAP CMA-ES refinement algorithm (ngen=%d)" % ngen)

            # Process some general stuff:
            bounds = np.array(context.ranges) #@UndefinedVariable
            num_weights = len(context.mixture.specimens) + 1
            create_individual = self._individual_creator(context, num_weights, bounds)

            # Setup strategy:
            centroid = create_individual(context.initial_solution)
            sigma = np.array(abs(bounds[:, 0] - bounds[:, 1]) / 20.0) #@UndefinedVariable
            strat_kwargs = {}
            if "lambda_" in kwargs:
                strat_kwargs["lambda_"] = kwargs.pop("lambda_")
            strategy = Strategy(
                centroid=centroid, sigma=sigma,
                stop=self._stop, **strat_kwargs
            )

            # Toolbox setup:
            toolbox = base.Toolbox()
            toolbox.register("evaluate", evaluate)
            toolbox.register("generate", strategy.generate, create_individual)
            toolbox.register("update", strategy.update)

            # Hall of fame & stats:
            logger.info("Creating hall-off-fame and statistics")
            halloffame = PyXRDParetoFront(similar=lambda a1, a2: np.all(a1 == a2)) #@UndefinedVariable
            stats = self._create_stats()

            # Create algorithm
            self.algorithm = Algorithm(
                toolbox, halloffame, stats, ngen=ngen,
                stagn_ngen=stagn_ngen, stagn_tol=stagn_tol, context=context, stop=self._stop)

            self._has_been_setup = True
        return self.algorithm

    def run(self, context, **kwargs):
        logger.info("CMA-ES run invoked with %s" % kwargs)
        algorithm = self._setup(context, **kwargs)
        # Get this show on the road:
        logger.info("Running the CMA-ES algorithm...")
        context.status = "running"
        context.status_message = "Running CMA-ES algorithm ..."
        algorithm.run()
        context.status_message = "CMA-ES finished ..."
        context.status = "finished"

    pass # end of class
