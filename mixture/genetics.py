# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import numpy as np

from pygene.gene import FloatGene, FloatGeneMax
from pygene.organism import Organism, MendelOrganism
from pygene.population import Population

def generate_gene(minimum, maximum):
    class PyXRDGene(FloatGeneMax):
        randMin = minimum
        randMax = maximum
        
    return PyXRDGene

def generate_organism(props, ranges, fitness_func):
    str_props = [str(id(prop)) for prop in props]
    str_genome = { prop: generate_gene(*rng) for prop, rng in zip(str_props, ranges) }
    class Converger(Organism):
        genome = str_genome
        
        def fitness(self):
            return fitness_func(self.get_solution())
            
        def get_solution(self):
            return np.array([self[prop] for prop in str_props])
    return Converger

def run_genetic_algorithm(ref_props, x0, ranges, fitness_func, gui_callback=None, stagnation=0.0001, max_generations=100):
    # create an empty population
    pop = Population(species=generate_organism(ref_props, ranges, fitness_func), init=200)
    pop.childCount = 30
    pop.incest=10

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
        if callable(gui_callback):
            gui_callback(current)
            
        if last_fitness!=None and (last_fitness-current) / last_fitness <= stagnation:
            print "Succesfull optimization after %d generations, aborting and returing found result" % ngens
            print "\t initial fitness = %s" % initial
            print "\t current fitness = %s" % current
            return b.get_solution()
        
        if ngens < max_generations:
            pop.gen()
            ngens += 1
        else:
            print "Failed after %d generations, aborting and returning original result" % ngens
            return x0
            
        last_fitness = current
            

