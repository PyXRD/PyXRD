# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.



import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from math import sqrt

import numpy as np
import scipy

from deap import cma, base, creator, tools #@UnresolvedImport

from pyxrd.refinement.refine_method import RefineMethod
from pyxrd.refinement.refine_method_option import RefineMethodOption
from pyxrd.refinement.refine_async_helper import RefineAsyncHelper

from deap_utils import pyxrd_array, PyXRDParetoFront, FitnessMin, result_func

# Default settings:
NGEN = 100
STAGN_NGEN = 10
STAGN_TOL = 0.001

class Strategy(cma.Strategy):
    """
        This evolutionary strategy supports the hybrid PSO-CMA runs using the
        rotate_and_bias function (should be called after an update).
    """

    def __init__(self, centroid, sigma, ranges, **kwargs):
        self.ranges = ranges
        super(Strategy, self).__init__(centroid, sigma, **kwargs)

    def update(self, population):
        """Update the current covariance matrix strategy from the
        *population*.
        
        :param population: A list of individuals from which to update the
                           parameters.
        """
        population.sort(key=lambda ind: ind.fitness, reverse=True)
        selected_pop = self._translate_external(
            np.array([ind.to_ndarray() for ind in population[0:self.mu]]))

        old_centroid = self._translate_external(self.centroid)
        centroid = np.dot(self.weights, selected_pop)

        c_diff = centroid - old_centroid

        # Cumulation : update evolution path
        self.ps = (1 - self.cs) * self.ps \
             + sqrt(self.cs * (2 - self.cs) * self.mueff) / self.sigma \
             * np.dot(self.B, (1. / self.diagD) \
                          * np.dot(self.B.T, c_diff))

        hsig = float((np.linalg.norm(self.ps) /
                sqrt(1. - (1. - self.cs) ** (2. * (self.update_count + 1.))) / self.chiN
                < (1.4 + 2. / (self.dim + 1.))))

        self.update_count += 1

        self.pc = (1 - self.cc) * self.pc + hsig \
                  * sqrt(self.cc * (2 - self.cc) * self.mueff) / self.sigma \
                  * c_diff

        # Update covariance matrix
        artmp = selected_pop - old_centroid
        new_C = (1 - self.ccov1 - self.ccovmu + (1 - hsig) \
                   * self.ccov1 * self.cc * (2 - self.cc)) * self.C \
                + self.ccov1 * np.outer(self.pc, self.pc) \
                + self.ccovmu * np.dot((self.weights * artmp.T), artmp) \
                / self.sigma ** 2

        self.sigma *= np.exp((np.linalg.norm(self.ps) / self.chiN - 1.) \
                                * self.cs / self.damps)

        try:
            self.diagD, self.B = np.linalg.eigh(new_C)
        except np.linalg.LinAlgError:
            logger.warning(
                "LinAlgError occurred when calculating eigenvalues" \
                " and vectors for matrix C!\n%r" % new_C
            )
        else:
            self.C = new_C
            indx = np.argsort(self.diagD)

            self.cond = self.diagD[indx[-1]] / self.diagD[indx[0]]

            self.diagD = self.diagD ** 0.5

            self.B = self.B[:, indx]
            self.BD = self.B * self.diagD

        self.centroid = self._translate_internal(centroid)

    def rotate_and_bias(self, global_best, tc=0.1, b=0.5, cp=0.5):
        """
            Rotates the covariance matrix and biases the centroid of this
            CMA population towards a global mean. Can be used to implement a
            PSO-CMA hybrid algorithm. 
        """

        global_best = self._translate_external(global_best)
        centroid = self._translate_external(self.centroid)

        # Rotate towards global:
        pg = np.array(global_best) - np.array(centroid)
        Brot = self.__rotation_matrix(self.B[:, 0], pg) * self.B
        Crot = Brot * (self.diagD ** 2) * Brot.T
        self.C = cp * self.C + (1.0 - cp) * Crot

        # Bias our mean towards global best mean:
        npg = np.linalg.norm(pg)
        nsigma = np.amax(self.sigma)
        if nsigma < npg:
            if nsigma / npg <= tc * npg:
                bias = b * pg
            else:
                bias = nsigma / npg * pg
        else:
            bias = 0

        centroid = centroid + bias

        self.centroid = self._translate_internal(centroid)

        pass

    def _translate_internal(self, solutions):
        # rule is: anything given as an argument in a public function or
        # available as a public property should be within the external boundaries

        return self.ranges[:, 0] + (self.ranges[:, 1] - self.ranges[:, 0]) * (1.0 - np.cos(solutions * np.pi)) / 2.0

    def _translate_external(self, solutions):
        return np.arccos(1 - 2 * (solutions - self.ranges[:, 0]) / (self.ranges[:, 1] - self.ranges[:, 0])) / np.pi

    def generate(self, ind_init):
        """Generate a population from the current strategy using the 
        centroid individual as parent.
        
        :param ind_init: A function object that is able to initialize an
                         individual from a list.
        :returns: an iterator yielding the generated individuals.
        """

        centroid = self._translate_external(self.centroid)

        arz = np.random.standard_normal((self.lambda_, self.dim)) #@UndefinedVariable
        arz = np.array(centroid) + self.sigma * np.dot(arz, self.BD.T) #@UndefinedVariable

        arz = self._translate_internal(arz)

        for arr in arz:
            yield ind_init(arr)

    def __rotation_matrix(self, vector, target):
        """ Rotation matrix from one vector to another target vector.
     
        The solution is not unique as any additional rotation perpendicular to
        the target vector will also yield a solution)
         
        However, the output is deterministic.
        """

        R1 = self.__rotation_to_pole(target)
        R2 = self.__rotation_to_pole(vector)

        return np.dot(R1.T, R2)

    def __rotation_to_pole(self, target):
        """ Rotate to 1,0,0... """
        n = len(target)
        working = target
        rm = np.eye(n)
        for i in range(1, n):
            angle = np.arctan2(working[0], working[i])
            rm = np.dot(self.__rotation_matrix_inds(angle, n, 0, i), rm)
            working = np.dot(rm, target)

        return rm

    def __rotation_matrix_inds(self, angle, n, ax1, ax2):
        """ 'n'-dimensional rotation matrix 'angle' radians in coordinate plane with
            indices 'ax1' and 'ax2' """


        s = np.sin(angle)
        c = np.cos(angle)

        i = np.eye(n)

        i[ax1, ax1] = s
        i[ax1, ax2] = c
        i[ax2, ax1] = c
        i[ax2, ax2] = -s

        return i

    pass #end of class

class Algorithm(RefineAsyncHelper):
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

    refiner = None

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
                         stagn_tol=STAGN_TOL, refiner=None, stop=None):
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
        self.halloffame = halloffame
        self.verbose = verbose
        self.stagn_ngen = stagn_ngen
        self.stagn_tol = stagn_tol
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
            population = self._ask()
            #TELL: Update the strategy with the evaluated individuals
            self._tell(population)
            #RECORD: For stagnation checking & logging:
            self._record(population)
            #CHECK: whether we are stagnating:
            if self._is_stagnating():
                logging.info("CMA: stagnation detected!")
                break

        return self.refiner.history.best_solution, population

    #--------------------------------------------------------------------------
    #    Stagnation calls:
    #--------------------------------------------------------------------------
    def _is_flat(self, yvals, xvals, slope_tolerance=0.001):
        slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(xvals, yvals) #@UndefinedVariable @UnusedVariable
        val = bool(abs(slope) <= slope_tolerance)
        return val

    def _is_stagnating(self):
        self.refiner.status.message = "Checking for stagnation"
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
        self.refiner.status.message = "Creating generation #%d" % self.gen

        def result_f(*args):
            self.refiner.update(*args)
            result_func(*args)

        population = self.do_async_evaluation(
            self.toolbox.generate, result_func=result_f
        )
        
        if self.halloffame is not None:
            self.halloffame.update(population)

        return population

    def _tell(self, population):
        self.refiner.status.message = "Updating strategy"
        self.toolbox.update(population)

    def _record(self, population):
        self.refiner.status.message = "Processing ..."
        
        # Get the best solution so far:
        best = self.halloffame.get_best()
        best_f = best.fitness.values[0]
        pop_size = len(population)

        # Calculate stats & print something if needed:
        record = self.stats.compile(population)
        if self.verbose:
            self.logbook.record(gen=self.gen, evals=pop_size, best=best_f, **record)
            print self.logbook.stream

        self.refiner.status.message = "Refiner update ..."
        # Update the refiner:
        self.refiner.update(best, iteration=self.gen, residual=best_f)

    pass #end of class

class RefineCMAESRun(RefineMethod):
    """
        The DEAP CMA-ES algorithm implementation with added stagnation thresholds
    """
    name = "CMA-ES refinement"
    description = "This algorithm uses the CMA-ES refinement strategy as implemented by DEAP"
    index = 1
    disabled = False

    ngen = RefineMethodOption('Maximum # of generations', NGEN, [1, 10000], int)
    stagn_ngen = RefineMethodOption('Minimum # of generations', STAGN_NGEN, [1, 10000], int)
    stagn_tol = RefineMethodOption('Fitness slope tolerance', STAGN_TOL, [0., 100.], float)

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
    def _setup(self, refiner, ngen=NGEN, stagn_ngen=STAGN_NGEN, stagn_tol=STAGN_TOL, **kwargs):
        if not self._has_been_setup:
            logger.info("Setting up the DEAP CMA-ES refinement algorithm (ngen=%d)" % ngen)
            refiner.status.message = "Setting up algorithm..."

            # Process some general stuff:
            bounds = np.array(refiner.ranges) #@UndefinedVariable
            create_individual = self._individual_creator(refiner, bounds)

            # Setup strategy:
            centroid = create_individual(refiner.history.initial_solution)
            strat_kwargs = {}
            if "lambda_" in kwargs:
                strat_kwargs["lambda_"] = kwargs.pop("lambda_")
            strategy = Strategy(
                centroid=centroid, sigma=1.0 / 10.0, ranges=bounds,
                stop=self._stop, **strat_kwargs
            )

            # Toolbox setup:
            toolbox = base.Toolbox()
            toolbox.register("generate", strategy.generate, create_individual)
            toolbox.register("update", strategy.update)

            # Hall of fame & stats:
            logger.info("Creating hall-off-fame and statistics")
            halloffame = PyXRDParetoFront(similar=lambda a1, a2: np.all(a1 == a2)) #@UndefinedVariable
            stats = self._create_stats()

            # Create algorithm
            self.algorithm = Algorithm(
                toolbox, halloffame, stats, ngen=ngen,
                stagn_ngen=stagn_ngen, stagn_tol=stagn_tol, refiner=refiner, stop=self._stop)

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
