# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from math import sqrt
import numpy as np
from pyxrd.generic.custom_math import smooth

def R_squared(exp, calc, *args):
    """
        Calculate the 'coefficient of determination' (aka R²) for the given
        experimental and calculated patterns (1D numpy arrays, y-values only) 
    """
    avg = sum(exp) / exp.size
    sserr = np.sum((exp - calc) ** 2)
    sstot = np.sum((exp - avg) ** 2)
    return 1 - (sserr / sstot)

def Rp(exp, calc, *args):
    """
        Calculate the 'pattern R factor' (aka Rp) for the given experimental and
        calculated patterns (1D numpy arrays, y-values only)
    """
    return np.sum(np.abs(exp - calc)) / np.sum(np.abs(exp)) * 100

def smooth_pattern(pattern):
    """
        Smooth the given pattern.
    """
    return smooth(pattern, 15)

def derive(pattern):
    """
        Calculate the first derivative pattern pattern. 
        Smoothes the input first, so noisy patterns shouldn't
        be much of a problem.
    """
    return np.gradient(smooth_pattern(pattern))

def Rpder(exp, calc):
    """
        Calculated the 'derived pattern R factor' (aka Rp') for the given 
        experimental and calculated patterns.
    """
    return Rp(derive(exp), derive(calc))

def Rpw(exp, calc):
    """
        Calculated the 'weighted pattern R factor' (aka Rwp) for the given experimental and
        calculated patterns (1D numpy arrays, y-values only)
        The weights are set equal to the inverse of the observed intensities.  
    """
    # weighted Rp:
    # Rwp = Sqrt ( Sum[w * (obs - calc)²] / Sum[w * obs²] )  w = 1 / Iobs
    sm1 = 0
    sm2 = 0
    for i in range(exp.size):
        t = (exp[i] - calc[i]) ** 2 / exp[i]
        if not (np.isnan(t) or np.isinf(t)):
            sm1 += t
            sm2 += abs(exp[i])
    try:
        return sqrt(sm1 / sm2) * 100
    except:
        return 0

def Rpe(exp, calc, num_params):
    """
        Calculate the 'expected pattern R factor' (Rpe) for the given experimental and
        calculated pattern and the number of refined parameters.
         
    """
    # R expected:
    # Re = Sqrt( (Points - Params) / Sum[ w * obs² ] )
    num_points = exp.size
    return np.sqrt((num_points - num_params) / np.sum(exp ** 2)) * 100
