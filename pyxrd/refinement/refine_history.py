# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np 

class RefineHistory(object):
    """
    A history tracking class for refinements
    """
    
    INITIAL_ITERATION_INDEX = -1
    LAST_ITERATION_INDEX = -1
    
    ITERATION_INDEX = 0
    RESIDUAL_INDEX = -1
    SOLUTION_SELECTOR = np.s_[ITERATION_INDEX+1:RESIDUAL_INDEX]
    PLOT_SAMPLE_SELECTOR = np.s_[ITERATION_INDEX+1:]
    
    samples = None
    
    _closed = False
    
    @property
    def best_entry(self):
        if self._closed:
            samples = self.samples
        else:
            samples = np.asanyarray(self.samples)
        residuals = samples[:,self.RESIDUAL_INDEX]
        return samples[np.where(residuals == residuals.min()),:][-1].flatten()
    
    @property
    def initial_entry(self):
        if self._closed:
            samples = self.samples
        else:
            samples = np.asanyarray(self.samples)
        iterations = samples[:,self.ITERATION_INDEX]       
        return samples[np.where(iterations == self.INITIAL_ITERATION_INDEX),:][-1].flatten()
    
    @property
    def last_entry(self):
        if self._closed:
            samples = self.samples
        else:
            samples = np.asanyarray(self.samples)
        iterations = samples[:,self.ITERATION_INDEX]
        return samples[np.where(iterations == self.LAST_ITERATION_INDEX),:][-1].flatten()
    
    @property
    def best_solution(self):
        return self.best_entry[self.SOLUTION_SELECTOR].flatten()
    
    @property
    def initial_solution(self):
        return self.initial_entry[self.SOLUTION_SELECTOR]
    
    @property
    def last_solution(self):
        return self.last_entry[self.SOLUTION_SELECTOR]

    @property
    def initial_residual(self):
        return float(self.initial_entry[self.RESIDUAL_INDEX])

    @property
    def best_residual(self):
        return float(self.best_entry[self.RESIDUAL_INDEX])
    
    @property
    def last_residual(self):
        return float(self.last_entry[self.RESIDUAL_INDEX])

    def __init__(self):
        self.samples = []

    def _sort_solutions_by_iteration(self):
        self.samples.sort(key=lambda s: s[0])
    
    def close(self):
        self._closed = True
        self._sort_solutions_by_iteration()
        self.samples = np.asanyarray(self.samples)
    
    def __enter__(self):
        assert self._closed is False, "Cannot use a closed refinement history!"
        return self
    
    def __exit__(self, tp, value, traceback):
        self.close()
    
    def set_initial_solution(self, solution, residual):
        if self._closed:
            raise RuntimeError, "Cannot change a closed refinement history!"
        self.register_solution(self.INITIAL_ITERATION_INDEX, solution, residual)
        
    def register_solution(self, iteration, solution, residual):
        if self._closed:
            raise RuntimeError, "Cannot change a closed refinement history!"
        sample = [iteration,]+list(solution)+[residual,]
        self.samples.append(sample)
        if iteration > self.LAST_ITERATION_INDEX:
            self.LAST_ITERATION_INDEX = iteration
            
    def get_residual_per_iteration(self):
        if not self._closed:
            raise RuntimeError, "Cannot perform analysis on an open refinement history"
        return self.samples[:,[self.ITERATION_INDEX,self.RESIDUAL_INDEX]].tolist()
        
    """ MOVE  THIS ELSEWHERE, history doesn't know or care about names! 
    def get_parameter_value_per_iteration(self, *parameter_names):
        if not self._closed:
            raise RuntimeError, "Cannot perform analysis on an open refinement history"
        indexes = [
            self.parameter_names.index(parameter_name) 
            for parameter_name in parameter_names
        ]
        return self.samples[:,indexes].tolist()"""
        
    pass #end of class
        