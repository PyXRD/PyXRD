#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from scipy.optimize import fmin_l_bfgs_b as optim



asf1 = np.array([0.126842, 4.708971, 1.194814, 1.558157, 1.170413, 3.239403, 4.875207, 108.506081, 0.111516, 48.292408, 1.928171])
asf2 = np.array([0.058851, 3.062918, 4.135106, 0.853742, 1.036792, 0.85252, 2.015803, 4.417941, 0.065307, 9.66971, 0.187818])

def func(asf, stl_range):
    f = np.zeros(stl_range.shape)
    for i in range(1, 6):
        f += asf[i] * np.exp(-asf[5 + i] * (stl_range) ** 2)
    f += asf[0]
    return f

stl_range = np.arange(0, 1, 0.01)

expected1 = func(asf1, stl_range)
expected2 = func(asf2, stl_range)

expected = (expected1 + expected2) / 2.0

def calculate_R2(x0, *args):
    global stl_range
    global expected
    calculated = func(x0, stl_range)
    return np.sum((calculated - expected) ** 2)

bounds = [
    (0, None),

    (None, None),
    (None, None),
    (None, None),
    (None, None),
    (None, None),

    (0.001, None),
    (0.001, None),
    (0.001, None),
    (0.001, None),
    (0.001, None),
]

x0 = asf2

lastx, lastR2, info = optim(calculate_R2, x0, approx_grad=True, pgtol=10e-24 , factr=2, iprint=-1, bounds=bounds)

print lastR2
print "\t".join([("%.10g" % fl).replace(".", ",") for fl in lastx])
print info
