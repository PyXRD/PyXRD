# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from pygene.gene import FloatGene, FloatGeneMax
from pygene.organism import Organism, MendelOrganism
from pygene.population import Population

def generate_gene(minimum, maximum):
    class PyXRDGene(FloatGeneMax):
        randMin = minimum
        randMax = maximum
        
    return PyXRDGene

def generate_organism(props, ranges, fitness_func):
    class Converger(Organism):
        genome = { prop: generate_gene(*rng) for prop, rng in zip(props, ranges) }
        
        def fitness(self):
            return fitness_func(self.get_solution())
            
        def get_solution(self):
            values = np.array([self[prop] for prop in props])

def run_genetic_algorithm(ref_props, x0, ranges, fitness_func, gui_callback=None, stagnation=0.1, max_generations=100):
    # create an empty population
    pop = Population(species=generate_organism(ref_props, ranges, fitness_func), init=2, childCount=50, childCull=20)

    ngens = 0
    last_fitness = None
    while True:
        b = pop.best()
        current = b.fitness()           
        
        #b.dump()
        print "Generation %s: best=%s average=%s" % (i, current, pop.fitness())
            
        if last_fitness!=None and (current - last_fitness) / last_fitness <= stagnation:
            print "Succesfull optimization after %d generations, aborting and returing found result" % ngens
            return b.get_solution()
        
        if ngens < max_generations:
            pop.gen()
            ngens += 1
        else:
            print "Failed after %d generations, aborting and returning original result" % ngens
            return x0
            
        last_fitness = current
            

