# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
import scipy
from random import uniform

from pygene.gene import FloatGene, FloatGene
from pygene.organism import Organism, MendelOrganism
from pygene.population import Population

from generic.utils import print_timing

from project.processes.workers import ImproveWorker, RefineWorker
from project.processes.pool import PyXRDPool

from .refine_run import RefineRun

import settings

def generate_gene(minimum, maximum):
    class PyXRDGene(FloatGene):
        randMin = minimum
        randMax = maximum
        mutProb = 0.65
        mutAmt = 0.20
        
        def mutate(self):
            """
            Mutate this gene's value by a random amount
            within the range determined by multiplying self.mutAmt by the
            gene's current value. Takes legal endpoints into account.
            
            perform mutation IN-PLACE, ie don't return mutated copy
            """
            local_min = max(self.value * (1.+self.mutAmt), self.randMin)
            local_max = min(self.value * (1.-self.mutAmt), self.randMax)
            self.value = uniform(local_min, local_max)
        
        pass #end of class
    return PyXRDGene

class PyXRDOrganism(Organism):
    """
        An Organism adapted to PyXRD's needs. Has some additional methods:
            - get_solution
            - set_from_solution
        to translate from and to PyXRD solution arrays and pygene gene dicts
        Makes use of multithreading or processing if enabled...
    """
    genome = None
    refine_worker = None
    context = None
    mutateOneOnly = True
    
    _last_fitness = None
    _last_solution = None
    result_dict = None
    def prepare_fitness(self):
         #Get and reset some stuff;
        solution = self.get_solution()
        self.result_dict = None
        # Do we need an update?
        if self._last_fitness==None or np.any(self._last_solution!=solution):
            self._last_solution = solution
            # Yes, we need an update, do we have a queue?
            if settings.MULTI_USE_PROCESSES and self.refine_worker!=None:
                # Yes, put it on the queue:
                self.result_dict = self.refine_worker.put_on_queue(self.get_solution())
            else:
                # No, calculate it immediately:
                self._last_fitness = self.context.objective_function(solution)

    def fitness(self):
        # Did we put it on the queue?
        if settings.MULTI_USE_PROCESSES and self.result_dict!=None and 'lock' in self.result_dict:
            #Yes, then wait for a result to come out:
            with self.result_dict['lock']:
                while not 'result' in self.result_dict:
                    self.result_dict['lock'].wait()
                self._last_fitness = self.result_dict['result']
            self.result_dict = None #clear reference
            self.context.dry_update(self._last_solution, self._last_fitness)
        return self._last_fitness
        
    def get_solution(self):
        return np.array([self[str(id(prop))] for prop in self.context.ref_props])
        
    def set_from_solution(self, solution, fitness=None):
        for i, prop in enumerate(self.context.ref_props):
            self.genes[str(id(prop))].value = solution[i]
            self._last_solution = solution
            self._last_fitness = fitness
             
    pass #end of class

class EngineeredPopulation(Population):
    """
        A population of organisms that is in every aspect behaving as the 
        normal PyGene population will, but for a number of 
    """
    improve_worker = None
    nengineered = max(settings.MULTI_CORES, 2)
    threshold_fitness = 7.0
    
    def gen(self, nfittest=None, nchildren=None, nengineered=None, threshold_fitness=None):
        super(EngineeredPopulation, self).gen(nfittest=nfittest, nchildren=nchildren)   
        
        nengineered = nengineered if nengineered!=None else self.nengineered
        print "Improving %d best organisms ..." % nengineered
        
        if settings.MULTI_USE_PROCESSES and self.improve_worker != None:
            #Parallel version:
            results = []
            for org in self.organisms[:nengineered]:
                if org.fitness > threshold_fitness:
                    # Improve it:
                    result_dict = self.improve_worker.put_on_queue(org.get_solution())
                    results.append(result_dict)

            for result_dict in results[::-1]:
                with result_dict['lock']:
                    while not 'result' in result_dict:
                        result_dict['lock'].wait()
                    new_solution, residual = result_dict['result']
                    new_org = self.species()
                    new_org.set_from_solution(new_solution, residual)
                    self.organisms.append(new_org)
                    result_dict.clear()
                    
            del results
        else:
            #Serial version:
            for org in self.organisms[:nengineered]:
                if org.fitness > threshold_fitness:
                    vals = scipy.optimize.fmin_l_bfgs_b(
                        self.context.apply_solution,
                        solution,
                        approx_grad=True,
                        bounds=self.context.ranges,
                        factr=1e18,
                        pgtol=1e-02,
                        epsilon=1e-05,
                        maxiter=1
                    )
                    new_solution, residual = vals[0:2]
                    new_org = self.species()
                    new_org.set_from_solution(new_solution, residual)
                    self.organisms.append(new_org)                    
        
        self.organisms.sort()
        self.organisms[:] = self.organisms[:nfittest]
        
    pass #end of class

class RefineGeneticsRun(RefineRun):
    """
        A genetic algorithm refiner, as implemented by PyGene
    """
    name="Genetic algorithm"
    description="A genetic algorithm, as implemented by PyGene"
    options=[
        # The minimum difference between the previous and current solution 
        # fitness needed to continue refining:
        ( 'Stagnation difference', 'stagnation', float, 0.3, [1E-12, 10] ),     
        # Target fitness to achieve, if fitness is not yet lower then this value,
        # do not stop (even if stagnation occurs, will continue up to max generations):
        ( 'Target fitness', 'target', int, 16.0, [0.0, 100.0] ),                
        # Maximum number of generations after which the refinement stops:
        ( 'Maximum generations', 'max_generations', int, 40, [5, 10000] ),
        
        ( '# start organisms', 'init', int, 100, [2, 100] ),
        ( '# new organisms', 'new_organisms', int, 10, [0, 100] ),
        ( '# children', 'childcount', int, 50, [1, 100] ),
        ( 'Decimate to', 'childcull', int, 30, [1, 100] ),
        ( 'Incest parents', 'incest', int, 10, [0, 100] ),
        ( 'Mutant fraction', 'mutants', float, 0.3, [0.0, 1.0] ),
    ]

    def _get_pool(self, context):
        if settings.MULTI_USE_PROCESSES:
            project = context.mixture.project
            
            improve_worker = ImproveWorker(context.mixture, project)
            refine_worker = RefineWorker(context.mixture, project)
            
            pool = PyXRDPool(project, workers=[
                improve_worker,
                refine_worker
            ])
            return improve_worker, refine_worker, pool
        else:
            return None, None, None
    
    def _setup_species(self, context, refine_worker=None):
        """
            Helper function
        """
        PyXRDOrganism.context = context
        PyXRDOrganism.refine_worker = refine_worker
        PyXRDOrganism.genome = { str(id(prop)): generate_gene(*rng) for prop, rng in zip(context.ref_props, context.ranges) }
        
        return PyXRDOrganism
    
    def run(self, context, init=100, **kwargs):
        # create an empty population
        print "Creating the first generation..."
        
        improve_worker, refine_worker, pool = self._get_pool(context)
        species = self._setup_species(context, refine_worker)
        
        if pool: pool.start()
        
        pop = Population(species=species, init=init)
        pop.improve_worker = improve_worker        
        self.run_population(context, pop, **kwargs)
        
        if pool: pool.stop()
        del pop, improve_worker, refine_worker, pool

    def run_population(self, context, pop,
            stagnation=0.3,
            target=16.0,
            max_generations=40,
            new_organisms=10,
            childcount=50,
            childcull=30,
            incest=10,
            mutants=0.3):
        pop.childCount = childcount
        pop.childCull = childcull
        pop.numNewOrganisms = new_organisms
        pop.incest = incest
        pop.mutants = mutants
        pop.mutateAfterMating = False

        ngens = 0
        previous_residual = None
        running = True
        while running and not (context.run_params.get("kill", False) or context.run_params.get("stop", False)):
            b = pop.best()
            context.update(b.get_solution())
            best = context.last_residual
            average = pop.fitness()
            
            context.record_state_data([
                ("generation", ngens),
                ("best_residual", best),
                ("average_residual", average)
            ])
                    
            print "Generation %s: best=%s average=%s" % (ngens, best, average)
            print previous_residual, best, stagnation, (previous_residual or 100)-best
            if best < target and previous_residual!=None and (previous_residual-best) <= stagnation:
                running = False
                if best < context.initial_residual:
                    print "Stagnation after %d generations, end result is an improvement" % ngens
                else:
                    print "Stagnation after %d generations, end result is not an improvement" % ngens
                print "\t initial fitness = %s" % context.initial_residual
                print "\t current fitness = %s" % best
                return context                    
            
            previous_residual = best
            
            if ngens < max_generations:
                pop.gen()
                ngens += 1
            else:
                print "Maximum number of generations reached (%d)" % ngens
                running = False
                return context
            
        del pop
    pass #end of class
    
class RefineHybridRun(RefineGeneticsRun):
    """
        A hybrid genetic and symplex algorithm refiner.
        Top x-organisms are further engineerd using L_BFGS_B
    """
    name = "Hybrig Gen/L BFGS algorithm"
    description = "A hybrid genetic and L BFGS algorithm."

    options= [
        ( '# of engineered organisms', 'nengineered', int, max(settings.MULTI_CORES, 2), [0, 20] ),
        ( 'Engineering fitness threshold', 'threshold_fitness', int, 4.0, [0.0, 50.0] ),
    ] + RefineGeneticsRun.options
       
    def run(self, context, init=100, nengineered=max(settings.MULTI_CORES, 2), threshold_fitness=7.0, **kwargs):
        # create an empty population
        print "Creating the first generation..."
        
        
        improve_worker, refine_worker, pool = self._get_pool(context)
        
        species = self._setup_species(context, refine_worker)
        if pool: pool.start()
        
        pop = EngineeredPopulation(species=species, init=init)
        pop.improve_worker = improve_worker
        pop.context = context
        pop.nengineered = nengineered
        pop.threshold_fitness = threshold_fitness
        
        self.run_population(context, pop, **kwargs)
        
        if pool: pool.stop()
        del pop, improve_worker, refine_worker, pool

    def run_population(self, *args, **kwargs):
        context = super(RefineHybridRun, self).run_population(*args, **kwargs)
        
        #Improve the final solution once more:
        print "Improving Über-solution..."
        vals = scipy.optimize.fmin_l_bfgs_b(
            context.apply_solution,
            context.best_solution,
            approx_grad=True,
            bounds=context.ranges,
            epsilon=1e-2 #use a rather large epsilon as for noisy data, the grad will be rather small...
        )
        new_solution, residual = vals[0:2]
        context.dry_update(new_solution, residual)

        context.record_state_data([
            ("generation", -1),
            ("best_residual", residual),
            ("average_residual", 0.0)
        ])

    pass #end of class
