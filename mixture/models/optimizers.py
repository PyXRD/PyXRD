# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from math import pi

from gtkmvc.model import Model, Signal
import numpy as np
import scipy

import settings

from generic.utils import print_timing
from generic.models import ChildModel

from specimen.models import Statistics


class Optimizer(ChildModel):
    """
        A simple model that plugs onto the Mixture model. It provides
        the functionality related to optimizing the weight fractions, scales
        and background shifts and residual calculation for the phases.
    """
    __parent_alias__ = "mixture"
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    def get_residual_parts(self):
        """
            Returns a tuple containing:
             - current number of phases `n`
             - current number of specimens `m`
             - a list of `m` numpy arrays containing `n` calculated phase patterns
             - a list of `m`experimental patterns
             - a list of `m` selectors (based on exclusion ranges)
            Using this information, it is possible to calculate the residual for
            any bg_shift or scales value.
        """
        #1 get the different intensities for each phase for each specimen 
        #  -> each specimen gets a 2D np-array of size m,t with:
        #         m the number of phases        
        #         t the number of data points for that specimen
        n, m = self.mixture.phase_matrix.shape
        calculated = [None]*n
        experimental = [None]*n
        selectors = [None]*n
        todeg = 360.0 / pi
        for i in range(n):
            phases = self.mixture.phase_matrix[i]
            specimen = self.mixture.specimens[i]
            if specimen!=None:
                theta_range, calc = specimen.get_phase_intensities(phases)
                calculated[i] = calc.copy()
                experimental[i] = specimen.experimental_pattern.xy_store.get_raw_model_data()[1].copy()
                selectors[i] = specimen.get_exclusion_selector(theta_range*todeg)
        return n, m, calculated, experimental, selectors
        
    def get_current_residual(self):
        """
            Gets the residual for the current mixture solution.
        """
        return self.get_residual(
            self.mixture.get_current_solution(), 
            self.get_residual_parts()
        )       
    
    def get_residual(self, solution, residual_parts=None):
        """
            Calculates the residual for the given solution in combination with
            the given residual parts. If residual_parts is None,
            the method calls get_residual_parts.
        """
        tot_rp = 0.0
        n, m, calculated, experimental, selectors = residual_parts if residual_parts else self.get_residual_parts()
        fractions, scales, bgshifts = self.mixture.parse_solution(solution, n, m)
        for i in range(n):
            if calculated[i]!=None and experimental[i].size > 0:
                calc = (scales[i] * np.sum(calculated[i]*fractions, axis=0)) 
                if settings.BGSHIFT:
                    calc += bgshifts[i]
                exp = experimental[i][selectors[i]]
                cal = calc[selectors[i]]
                tot_rp += Statistics._calc_Rp(exp, cal)
        del n, m, calculated, experimental, selectors
        del fractions, scales, bgshifts
        return tot_rp

    def get_optimize_start(self):
        residual_parts = self.get_residual_parts()
        n, m, calculated, experimental, selectors = residual_parts

        bounds = [(0,None) for i in range(m)] + [(0, None) for i in range(n*2)]
        
        return n, m, bounds, residual_parts

    def __optimize(self, silent):
        """
            Optimizes the mixture fractions, scales and bg shifts.
        """
        
        
        """ TODO check if this will really improve, for now speed is okay
        pi_args_list = []
        observed_ranges = []
        observed_intensities = []
        selected_ranges = []
        for i, specimen in enumerate(self.mixture.specimen):
            pi_args = specimen.get_pi_args(self.mixture.phase_matrix[i,...])
            pi_args_list.append(pi_args)
            
            
            
            observed_ranges.append(specimen.experimental_pattern.xy_store._model_data_x)
            observed_intensities.append(specimen.experimental_pattern.xy_store._model_data_y)
            observed_intensities.append(specimen.experimental_pattern.xy_store._model_data_y)
            
        get_optimized_mixture(
            pi_args_list, observed_ranges, observed_intensities, selected_ranges
            
        )
        """

        # 1. get stuff that doesn't change:
        n, m, bounds, residual_parts = self.get_optimize_start()
            
        # 2. optimize the fractions:         
        x0 = np.ones(shape=(m+n+n,))
        x0[-n:] = 0.0
        
        # Do a quick optimization to get an idea of the scales:
        lastx, lastR2, info = scipy.optimize.fmin_l_bfgs_b(
            self.get_residual,
            x0,
            factr=1e-12,
            pgtol=1e-3,
            args=(residual_parts,),
            approx_grad=True,
            bounds=bounds,
            iprint=-1
        )
        
        # 3. rescale scales and fractions so they fit into [0-1] range, 
        #    and round them to have 6 digits max:
        fractions, scales, bgshifts = self.mixture.parse_solution(lastx, n, m)
        fractions = fractions.flatten()
        if settings.BGSHIFT:
            bgshifts = bgshifts.round(6)
        
        sum_frac = np.sum(fractions)
        if sum_frac == 0.0 and len(fractions) > 0: #prevent NaN errors
            fractions[0] = 1.0
            sum_frac = 1.0
        fractions = np.around((fractions / sum_frac), 6)
        scales *= sum_frac
        scales = scales.round(6)
        
        # 4. set model properties:
        self.mixture.set_solution(fractions, scales, bgshifts, silent=silent)
                        
        return lastR2

    def optimize(self, silent=False):
        return self.__optimize(silent=silent)

    pass #end of class
