# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np

from pygene.gene import FloatGene, FloatGeneMax
from pygene.organism import Organism, MendelOrganism
from pygene.population import Population

def generate_gene(minimum, maximum):
    class PyXRDGene(FloatGeneMax):
        randMin = minimum
        randMax = maximum
        mutProb = 0.75
        mutAmt = 0.25
        
    return PyXRDGene

def generate_organism(props, ranges, fitness_func):
    str_props = [str(id(prop)) for prop in props]
    str_genome = { prop: generate_gene(*rng) for prop, rng in zip(str_props, ranges) }
    class Converger(Organism): #TODO make RefineableProperty to inherit from Organism
        genome = str_genome
        mutateOneOnly = True
        
        _last_fitness = None
        _last_solution = None
        def fitness(self):
            solution = self.get_solution()
            if self._last_fitness==None or np.any(self._last_solution!=solution):
                self._last_fitness = fitness_func(solution)
            self._last_solution = solution
            return self._last_fitness
            
            
        def get_solution(self):
            return np.array([self[prop] for prop in str_props])
    return Converger

def run_genetic_algorithm(ref_props, x0, ranges, fitness_func, gui_callback=None, stagnation=0.0001, max_generations=100):
    # create an empty population
    print "Creating the first generation..."
    pop = Population(species=generate_organism(ref_props, ranges, fitness_func), init=30)
    pop.childCount = 30
    pop.incest = 2
    pop.mutants = 0.8
    pop.mutateAfterMating = False
    

    ngens = 0
    last_fitness = None
    initial = None
    while True:
        b = pop.best()
        current = b.fitness()           
        
        if ngens == 0:
            initial = current
        
        #b.dump()
        print "Generation %s: best=%s average=%s" % (ngens, current, pop.fitness())
        #if callable(gui_callback):
        #    gui_callback(current)
            
        if last_fitness!=None and (last_fitness-current) / last_fitness <= stagnation:
            if current < initial:
                print "Stagnation after %d generations, result has improved, aborting and returning best solution" % ngens
                print "\t initial fitness = %s" % initial
                print "\t current fitness = %s" % current
                return b.get_solution(), current
            else:
                print "Stagnation after %d generations, result has not improved, aborting and returning initial solution" % ngens
                print "\t initial fitness = %s" % initial
                print "\t current fitness = %s" % current            
                return x0, initial
                
        
        if ngens < max_generations:
            pop.gen()
            ngens += 1
        else:
            print "Failed after %d generations, aborting and returning original result" % ngens
            return x0
            
        last_fitness = current
            

