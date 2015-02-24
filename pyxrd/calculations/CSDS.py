# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from math import sqrt, log

from pyxrd.generic.custom_math import lognormal

def calculate_distribution(CSDS):
    r"""
    Returns a tuple containing a numpy array with the (log normal) CSDS
    distribution and a float containing the arithmetic mean of that
    distribution.
    
    Takes a single :class:`~CSDSData` object as argument.
    """
    a = CSDS.alpha_scale * log(CSDS.average) + CSDS.alpha_offset
    b = sqrt(CSDS.beta_scale * log(CSDS.average) + CSDS.beta_offset)

    steps = int(CSDS.maximum - CSDS.minimum) + 1

    maxT = 0

    smq = 0
    q_log_distr = []
    TQDistr = dict()
    for i in range(steps):
        T = max(CSDS.minimum + i, 1e-50)
        q = lognormal(T, a, b)
        smq += q

        TQDistr[int(T)] = q
        maxT = T

    TQarr = np.zeros(shape=(maxT + 1,), dtype=float)
    Rmean = 0
    for T, q in TQDistr.iteritems():
        TQarr[T] = q / smq
        Rmean += T * q
    Rmean /= smq

    return TQarr, Rmean
