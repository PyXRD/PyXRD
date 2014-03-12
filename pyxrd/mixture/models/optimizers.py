# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.generic.models import ChildModel

from pyxrd.calculations.mixture import (
    get_optimized_mixture,
    calculate_mixture,
    get_residual,
    get_optimized_residual
)


class Optimizer(ChildModel):
    """
        A simple model that plugs onto the Mixture model. It provides
        the functionality related to optimizing the weight fractions, scales
        and background shifts and residual calculation for the phases.
    """
    parent_alias = "mixture"

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_current_residual(self):
        """
            Gets the residual for the current mixture solution.
            Convenience function.
        """
        return self.get_residual()

    def get_optimized_residual(self, data_object=None):
        """
            Gets an optimized residual for the current mixture setup. If no
            data_object is passed it is retrieved from the mixture.
        """
        return get_optimized_residual(*self.get_data_object(data_object))[0]

    def get_residual(self, data_object=None):
        """
            Calculates the residual for the given solution in combination with
            the given optimization arguments. If no data_object is passed it is 
            retrieved from the mixture.
        """
        return get_residual(*self.get_data_object(data_object))[0]

    def calculate(self, data_object=None):
        """
            Calculates the total and phase intensities. If no data_object is
            passed it is retrieved from the mixture.
        """
        return calculate_mixture(*self.get_data_object(data_object))

    def optimize(self, data_object=None):
        """
            Optimizes the mixture fractions, scales and bg shifts and returns the
            optimized result. If no data_object is passed it is retrieved from
            the mixture.
        """
        try:
            return get_optimized_mixture(*self.get_data_object(data_object))
        except AssertionError:
            return None

    def get_data_object(self, data_object=None):
        return (data_object if data_object is not None else self.parent.data_object,)

    pass # end of class
