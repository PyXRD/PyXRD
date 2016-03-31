# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from itertools import product, combinations

import numpy as np

from ..refine_method import RefineMethod
from ..refine_method_option import RefineMethodOption

class RefineBruteForceRun(RefineMethod):
    name = "Brute force algorithm"
    description = "Refinement using a Brute Force algorithm"
    index = 3
    disabled = False

    num_samples = RefineMethodOption('Number of samples', 11, [3, 1000], int)

    def run(self, refiner, num_samples=11, stop=None, **kwargs):
        """
            Refinement using a Brute Force algorithm
        """

        self.refiner = refiner

        num_params = len(refiner.ranges)

        npbounds = np.array(refiner.ranges, dtype=float)
        npmins = npbounds[:, 0]
        npranges = npbounds[:, 1] - npbounds[:, 0]

        def generate():
            # Generates the solutions for async evaluation
            if num_params == 1:
                for index in range(num_samples):
                    npindex = np.array([index / float(num_samples - 1)], dtype=float)
                    solution = npmins + npranges * npindex
                    yield solution
            else:
                # Generate a grid for each possible combination of parameters:
                for par1, par2 in combinations(range(num_params), 2):
                    # produce the grid indices for those parameters
                    # keep the others half-way their range:
                    indeces = np.ones(shape=(num_params,), dtype=float) * 0.5
                    for par_indeces in product(range(num_samples), repeat=2):
                        indeces[par1] = par_indeces[0] / float(num_samples - 1)
                        indeces[par2] = par_indeces[1] / float(num_samples - 1)
                        # Make the solution:
                        solution = npmins + npranges * indeces
                        yield solution

        self.do_async_evaluation(generate)
        
        refiner.apply_initial_solution()

    pass #end of class
