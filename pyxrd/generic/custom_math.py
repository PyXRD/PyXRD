# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from math import log10, floor, exp, sqrt, log, pi

import numpy as np

sqrtpi = sqrt(pi)
sqrt2pi = sqrt(2 * pi)
sqrt8 = sqrt(8)

def mmult(A, B):
    return np.sum(np.transpose(A, (0, 2, 1))[:, :, :, np.newaxis] * B[:, :, np.newaxis, :], -3)

def mdot(A, B):
    C = np.zeros(shape=A.shape, dtype=np.complex)
    for i in range(A.shape[0]):
        C[i] = np.dot(A[i], B[i])
    return C

def mtim(A, B):
    C = np.zeros(shape=A.shape, dtype=np.complex)
    for i in range(A.shape[0]):
        C[i] = np.multiply(A[i], B[i])
    return C


def solve_division(A, B):
    bt = np.transpose(B, axes=(0, 2, 1))
    at = np.transpose(A, axes=(0, 2, 1))
    return np.array([np.transpose(np.linalg.lstsq(bt[i], at[i])[0]) for i in range(bt.shape[0])])

def round_sig(x, sig=1):
    if x == 0:
        return 0
    else:
        return round(x, sig - int(floor(log10(abs(x)))) - 1)

def capint(lower, value, upper, out=None):
    if value < lower or value > upper:
        return out if out is not None else min(max(value, lower), upper)
    else:
        return value

def lognormal(T, a, b):
    return sqrt2pi * exp(-(log(T) - a) ** 2 / (2.0 * (b ** 2))) / (abs(b) * T)

def add_noise(x, noise_fraction=0.05):
    if x.size > 0:
        abs_value = noise_fraction * np.amax(x)
        return x + np.random.standard_normal(x.shape) * abs_value
    else:
        return x

def smooth(x, half_window_len=3, window='blackman'):
    """smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the beginning and end part of the output signal.
    
    input:
        x: 1D array like (assumed to be spaced equally)
        half_window_len: half of the dimension of the smoothing window, actual window
            is calculated from this so that: window_len = 2*half_window_len + 1, this
            ensures that the window is always an odd number, regardless of user input;
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal
        
    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)
    
    see also: 
    
    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter
 
    TODO: the window parameter could be the window itself if an array instead of a string
    """

    window_len = half_window_len * 2 + 1

    if x.ndim != 1:
        x = np.ndarray.flatten(x)

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."

    if window_len < 3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


    s = np.r_[x[window_len - 1:0:-1], x, x[-1:-window_len:-1]]
    if window == 'flat': # moving average
        w = np.ones(window_len, 'd')
    else:
        w = eval('np.' + window + '(window_len)')

    y = np.convolve(w / w.sum(), s, mode='valid')
    return y[half_window_len:-half_window_len]
