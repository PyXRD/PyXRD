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

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import numpy as np
import scipy
import itertools
import random

from deap import base, creator, tools #@UnresolvedImport

from .deap_utils import pyxrd_array, evaluate
from .refine_run import RefineRun
from pyxrd.mixture.models.methods.deap_utils import AsyncEvaluatedAlgorithm, \
    PyXRDParetoFront, FitnessMin

# Default settings:
NGEN = 100
NSWARMS = 1
NEXCESS = 3
NPARTICLES = 15
CONV_FACTR = 0.3 # 5.*1e-2

class MultiPSOStrategy(object):

    def generate_particle(self, pclass, dim, pmin, pmax, smin, smax):
        """ Generate a particle """
        part = pclass(random.uniform(pmin[i], pmax[i]) for i in range(dim))
        part.speed = np.array([random.uniform(smin[i], smax[i]) for i in xrange(dim)])
        return part

    def update_particle(self, part, best, chi, c):
        """
            Update a particle's position & speed
            part: the particle
            best: the global best
            chi ~ recombination factor
            c ~ scale factor(s)
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

        # Adjust speed:
        speed = a + speed
        # Set position & speed:
        part[:] = part_pos + speed
        part.speed = speed
        # Clear fitness:
        del part.fitness.values

    def create_swarm(self, container, iterable):
        """ Returns a swarm container using the iterable """
        return container(iterable)

    def generate_particles(self, func, n):
        """ Returns a particle generator """
        for _ in xrange(n):
            yield func()

    def update_swarm(self, swarm, part):
        """ Update swarm's attractors personal best and global best """
        if not part.fitness.valid:
            raise RuntimeError, "Particles need to have a valid fitness before calling update_swarm!"
        if part.best == None or part.fitness > part.bestfit:
            part.best = creator.Particle(part)          # Get the position @UndefinedVariable
            part.bestfit.values = part.fitness.values   # Get the fitness
        if swarm.best == None or part.fitness > swarm.bestfit:
            swarm.best = creator.Particle(part)         # Get the position @UndefinedVariable
            swarm.bestfit.values = part.fitness.values  # Get the fitness

    def give_reinit_swarms(self, population):
        """ Gives a set of swarm indeces that need to be reinitialized (overlap)"""
        reinit_swarms = set()
        for s1, s2 in itertools.combinations(range(len(population)), 2):
            # Swarms must have a best and not already be set to reinitialize
            if population[s1].best is not None and population[s2].best is not None and not (s1 in reinit_swarms or s2 in reinit_swarms):
                # if t-test is True, then we reinit the worst of the two swarms
                t, _ = scipy.stats.ttest_ind(population[s1], population[s2]) #@UndefinedVariable
                if np.all(t < 0.1):
                    if population[s1].bestfit <= population[s2].bestfit:
                        reinit_swarms.add(s1)
                    else:
                        reinit_swarms.add(s2)
        return reinit_swarms

    def give_converged_swarms(self, population, conv_factr, converged_bests=[]):
        """ Returns the number of converged swarms and the worst swarm index """
        # Convergence check:
        not_converged = 0
        worst_swarm_idx = None
        worst_swarm = None
        for i, swarm in enumerate(population):
            # Compute the diameter of the swarm:
            std = np.std([ind.fitness.values for ind in swarm])
            # If it's larger then a given factor, we've not converged yet:
            if std > conv_factr:
                not_converged += 1
                if worst_swarm is None or swarm.bestfit < worst_swarm.bestfit:
                    worst_swarm_idx = i
                    worst_swarm = swarm
            else:
                converged_bests.append(swarm.best)

        converged_bests.sort(key=lambda i: i.fitness)

        return not_converged, worst_swarm_idx, converged_bests

    pass #end of class

class MPSOAlgorithm(AsyncEvaluatedAlgorithm):
    """
        Multi-particle-swarm optimization method adapted from the examples found
        in the DEAP project. Employs a T-test (two independent sample lists) to
        differentiate between swarms instead of the diameter and average of the
        swarms. Seemed to work better for scaled parameters (YMMV).
        
        Implementation of the Multiswarm Particle Swarm Optimization algorithm as
        presented in *Blackwell, Branke, and Li, 2008, Particle Swarms for Dynamic
        Optimization Problems.*
    """

    gen = -1
    converged_bests = None

    #--------------------------------------------------------------------------
    #    Initialization
    #--------------------------------------------------------------------------
    def __init__(self, toolbox, bounds, norms,
        ngen=NGEN, nswarms=NSWARMS, nexcess=NEXCESS,
        nparticles=NPARTICLES, conv_factr=CONV_FACTR,
        stats=None, halloffame=None, verbose=True, context=None, stop=None):
        """
            TODO
        """
        self.converged_bests = []
        self.toolbox = toolbox
        self.bounds = bounds
        self.norms = norms
        self.ngen = ngen
        self.nswarms = nswarms
        self.nexcess = nexcess
        self.nparticles = nparticles
        self.conv_factr = conv_factr
        self.stats = stats
        self.halloffame = halloffame
        self.verbose = verbose
        self.context = context

        self._stop = stop

    #--------------------------------------------------------------------------
    #    Convenience functions:
    #--------------------------------------------------------------------------

    def _evaluate_swarms(self, population):
        # Only evaluate invalid particles:
        def give_unevaluated_particles():
            for p in itertools.chain(*population):
                if p.fitness.valid: continue
                else: yield p
        self.do_async_evaluation(None, give_unevaluated_particles, self.toolbox.evaluate)
        for swarm in population:
            for part in swarm:
                self.toolbox.update_swarm(swarm, part)
        return population

    def _create_and_evaluate_swarm(self):
        """ Helper function that creates, evaluates and returns a new swarm """
        particles = []
        self.do_async_evaluation(particles,
            self.toolbox.generate_particles, self.toolbox.evaluate)
        return self.toolbox.swarm(particles)

    def _create_and_evaluate_population(self):
        """ Helper function that creates, evaluates and returns a population of swarms """
        population = [self._create_and_evaluate_swarm() for _ in range(self.nswarms)]
        if self.halloffame is not None:
            self.halloffame.update(itertools.chain(*population))
        return population

    #--------------------------------------------------------------------------
    #    Run method:
    #-------------------------------------------------------------------------
    def run(self):
        """Will run this algorithm"""
        self._setup_logging()
        population = []
        for _ in xrange(self.ngen):

            # Check if the user has cancelled:
            if self._user_cancelled():
                logger.info("User cancelled execution of PCMA-ES, stopping ...")
                break

            #ASK: Generate a new population:
            population = self._ask(population)
            #RECORD: For stagnation checking & logging:
            self._record(population)
            #CHECK: whether we are stagnating:
            if self._is_stagnating():
                break
            #TELL: Update the strategy with the evaluated individuals
            self._tell(population)

        return (
            self.context.best_solution,
            list(itertools.chain(*population)),
            self.converged_bests
        )

    #--------------------------------------------------------------------------
    #    Ask, tell & record:
    #--------------------------------------------------------------------------
    def _ask(self, population):
        """
            Calculates how many swarms have converged, and keeps track of the
            worst swarm. If all swarms have converged, it will add a new swarm.
            If too many swarms are roaming, it will remove the worst.
        """

        self.gen += 1
        self.context.status_message = "Creating generation #%d" % (self.gen + 1)

        if not population:
            # First iteration: create a new population of swarms
            population = self._create_and_evaluate_population()
        else:
            # Second and later iterations: check for overlapping swarms
            reinit_swarms = self.toolbox.give_reinit_swarms(population)
            # Reinitialize and evaluate swarms
            for sindex in reinit_swarms:
                population[sindex] = self._create_and_evaluate_swarm()

        # Get unconverged swarm count and worst swarm id:
        not_converged, worst_swarm_idx, self.converged_bests = self.toolbox.give_converged_swarms(population, self.conv_factr, self.converged_bests)

        # If all swarms have converged, add a swarm:
        if not_converged == 0:
            population.append(self._create_and_evaluate_swarm())

        # If too many swarms are roaming, remove the worst swarm:
        elif not_converged > self.nexcess:
            population.pop(worst_swarm_idx)

        return population

    def _tell(self, population):
        # Update and evaluate the swarm
        for swarm in population:
            # Update particles and swarm:
            for part in swarm:
                if swarm.best is not None and part.best is not None:
                    self.toolbox.update_particle(part, swarm.best)
        self._evaluate_swarms(population)
        self.halloffame.update(itertools.chain(*population))

    def _is_stagnating(self):
        return False # TODO FIXME

    def _setup_logging(self):
        if self.verbose:
            column_names = ["gen", "nswarm", "indiv"]
            if self.stats is not None:
                column_names += self.stats.functions.keys()
            self.logbook = tools.Logbook()
            self.logbook.header = column_names

    def _record(self, population):
        # Get pop size:
        pop_size = len(population)

        # Get the best solution so far:
        best = self.halloffame.get_best()
        best_f = best.fitness.values[0]

        # Calculate stats & print something if needed:
        pop = list(itertools.chain(*population))
        record = self.stats.compile(pop)
        if self.verbose:
            self.logbook.record(gen=self.gen, nswarm=pop_size, indiv=len(pop), **record)
            print self.logbook.stream

        # Update the context:
        self.context.update(best, best_f)
        self.context.record_state_data([
            ("best", best_f)
        ] + [
            (key, record[key][0]) for key in self.stats.functions.keys()
        ] + [
            ("par%d" % i, float(val)) for i, val in enumerate(best)
        ])

    pass #end of class


class RefineMPSORun(RefineRun):
    """
        The DEAP MPSO algorithm implementation
    """
    name = "MPSO refinement"
    description = "This algorithm uses the MPSO refinement strategy"

    options = [
        ('Maximum # of generations', 'ngen', int, NGEN, [1, 1000]),
        ('Start # of swarms', 'nswarms', int, NSWARMS, [1, 50]),
        ('Max # of unconverged swarms', 'nexcess', int, NEXCESS, [1, 50]),
        ('Swarm size', 'nparticles', int, NPARTICLES, [1, 50]),
        ('Convergence tolerance', 'conv_factr', float, CONV_FACTR, [0., 10.]),
    ]

    def _individual_creator(self, context, num_weights, bounds):
        creator.create(
            "Particle", pyxrd_array,
            fitness=FitnessMin, #@UndefinedVariable
            speed=list,
            best=None,
            bestfit=FitnessMin, #@UndefinedVariable
            context=context,
            min_bounds=bounds[:, 0],
            max_bounds=bounds[:, 1],
        )
        creator.create("Swarm", list, best=None, bestfit=FitnessMin) #@UndefinedVariable

    def _create_stats(self):
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)
        return stats

    def run(self, context, ngen=NGEN, nswarms=NSWARMS, nexcess=NEXCESS,
            conv_factr=CONV_FACTR, nparticles=NPARTICLES, **kwargs):

        logger.info("Setting up the DEAP MPSO refinement algorithm")

        # Process some general stuff:
        ndim = len(context.ref_props)
        bounds = np.array(context.ranges)
        norms = np.abs(bounds[:, 1] - bounds[:, 0])
        num_weights = len(context.mixture.specimens) + 1
        self._individual_creator(context, num_weights, bounds)

        # Strategy setup
        strategy = MultiPSOStrategy()

        # Hall of fame & stats:
        logger.info("Creating hall-off-fame and statistics")
        halloffame = PyXRDParetoFront(similar=lambda a1, a2: np.all(a1 == a2))
        stats = self._create_stats()

        # Our toolbox:
        toolbox = base.Toolbox()
        toolbox.register(
            "particle", strategy.generate_particle, creator.Particle, #@UndefinedVariable
            dim=ndim,
            pmin=bounds[:, 0], pmax=bounds[:, 1],
            smin=-norms / 2.0, smax=norms / 2.0
        )
        toolbox.register("evaluate", evaluate)
        toolbox.register("update_particle", strategy.update_particle, chi=0.729843788, c=norms / np.amax(norms))
        toolbox.register("generate_particles", strategy.generate_particles, toolbox.particle, n=NPARTICLES)

        toolbox.register("swarm", strategy.create_swarm, creator.Swarm) #@UndefinedVariable
        toolbox.register("update_swarm", strategy.update_swarm)
        toolbox.register("give_reinit_swarms", strategy.give_reinit_swarms)
        toolbox.register("give_converged_swarms", strategy.give_converged_swarms)

        # Create algorithm
        algorithm = MPSOAlgorithm(
            toolbox, bounds, norms,
            ngen, nswarms, nexcess, nparticles, conv_factr,
            stats=stats, halloffame=halloffame,
            context=context, stop=self._stop, **kwargs
        )

        # Get this show on the road:
        logger.info("Running the MPSO algorithm...")
        context.status = "running"
        context.status_message = "Running MPSO algorithm ..."
        best, population, converged_bests = algorithm.run() # returns (best, population) tuple
        context.status_message = "MPSO finished ..."
        context.status = "finished"

        return best, population, converged_bests

    pass # end of class
