# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from math import sqrt, log

from generic.custom_math import lognormal
from generic.caching import cache

@cache(64)
def calculate_distribution(Tmean, Tmax, Tmin, alpha_scale, alpha_offset, beta_scale, beta_offset):
    a = alpha_scale * log(Tmean) + alpha_offset
    b = sqrt(beta_scale * log(Tmean) + beta_offset)
        
    steps = int(Tmax - Tmin) + 1
    
    maxT = 0
    
    smq = 0
    q_log_distr = []
    TQDistr = dict()
    for i in range(steps):
        T = max(Tmin + i, 1e-50)
        q = lognormal(T, a, b)
        smq += q
        
        TQDistr[int(T)] = q
        maxT = T
        
    TQarr = np.zeros(shape=(maxT+1,), dtype=float)
    Rmean = 0
    for T,q in TQDistr.iteritems():
        TQarr[T] = q / smq
        Rmean += T*q
    Rmean /= smq
        
    return (TQDistr.items(), TQarr, Rmean)
