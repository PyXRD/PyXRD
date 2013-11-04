# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import numpy as np
from scipy import stats

from pyxrd.generic.custom_math import smooth

def find_closest(value, array, col=0):
    """
        Find closest value to another value in an array 
    """
    nparray = np.array(zip(*array)[col])
    idx = (np.abs(nparray - value)).argmin()
    return array[idx]

def score_minerals(peak_list, minerals):
    """
        Scoring function for mineral peaks
        peak_list: list of tuples containing observed peak position and (abs) intensity
        minerals: dict with the mineral name as key and a peak list as value,
           analogeous to the first argument but with relative intensities
           
        Uses a simple appoach:
        loop over the reference minerals, 
         loop over first 10 strongest peaks for that mineral (starting at 
          stronger reflections towards weaker)
         find a peak in the observed peak data set that matches
         if matching add to the list of matched peaks
         if not matching and this is the strongest reflections, ignore mineral
        after this initial loop we have a list of matched peaks,
        this list is then used to calculate a score for the mineral by looking
        at how well positions and intensities match with the reference and how
        many peaks are actually matched of course. Higher values means a higher
        likelihood this mineral is present.
    """
    max_pos_dev = 0.01 # fraction
    scores = []
    for mineral, abbreviation, mpeaks in minerals:
        tot_score = 0
        p_matches = []
        i_matches = []
        already_matched = []
        mpeaks = sorted(mpeaks, key=lambda peak: peak[0], reverse=True)
        if len(mpeaks) > 15:
            mpeaks = mpeaks[:15]

        for i, (mpos, mint) in enumerate(mpeaks):
            epos, eint = find_closest(mpos, peak_list)
            if abs(epos - mpos) / mpos <= max_pos_dev and not epos in already_matched:
                p_matches.append([mpos, epos])
                i_matches.append([mint, eint])
                already_matched.append(epos)
            elif i == 0:
                break # if strongest peak does not match, ignore mineral

        if len(p_matches) > 3:
            p_matches = np.array(p_matches)
            i_matches = np.array(i_matches)

            i_matches[:, 1] = i_matches[:, 1] / np.max(i_matches[:, 1])

            p_slope, p_intercept, p_r_value, p_value, p_std_err = stats.linregress(p_matches) # @UnusedVariable
            i_slope, i_intercept, i_r_value, p_value, i_std_err = stats.linregress(i_matches) # @UnusedVariable

            p_factor = (p_r_value ** 2) * min(1.0 / (abs(1.0 - p_slope) + 1E-50), 1000.) / 1000.0
            i_factor = (1.0 - min(i_std_err / 0.25, 5.0) / 5.0) * min(1.0 / (abs(1.0 - i_slope) + 1E-50), 1000.) / 1000.0 # * max(1. / (abs(i_intercept) + 1E-50), 100.) / 100.
            tot_score = len(p_matches) * p_factor * i_factor

        if tot_score > 0:
            scores.append((mineral, abbreviation, mpeaks, p_matches, tot_score))

    scores = sorted(scores, key=lambda score: score[-1], reverse=True)
    return scores

def peakdetect(y_axis, x_axis=None, lookahead=500, delta=0):
    """ single run of multi_peakdetect """
    mintabs, maxtabs = multi_peakdetect(y_axis, x_axis, lookahead, [delta])
    return mintabs[0], maxtabs[0]

def multi_peakdetect(y_axis, x_axis=None, lookahead=500, deltas=[0]):
    """
    Converted from/based on a MATLAB script at http://billauer.co.il/peakdet.html
    
    Algorithm for detecting local maximas and minmias in a signal.
    Discovers peaks by searching for values which are surrounded by lower
    or larger values for maximas and minimas respectively
    
    keyword arguments:
    y_axis -- A list containg the signal over which to find peaks
    x_axis -- A x-axis whose values correspond to the 'y_axis' list and is used
        in the return to specify the postion of the peaks. If omitted the index
        of the y_axis is used. (default: None)
    lookahead -- (optional) distance to look ahead from a peak candidate to
        determine if it is the actual peak (default: 500) 
        '(sample / period) / f' where '4 >= f >= 1.25' might be a good value
    deltas -- (optional) this specifies a minimum difference between a peak and
        the following points, before a peak may be considered a peak. Useful
        to hinder the algorithm from picking up false peaks towards to end of
        the signal. To work well delta should be set to 'delta >= RMSnoise * 5'.
        (default: 0)
            Delta function causes a 20% decrease in speed, when omitted
            Correctly used it can double the speed of the algorithm
    
    return -- two lists [maxtab, mintab] containing the positive and negative
        peaks respectively. Each cell of the lists contains a tupple of:
        (position, peak_value) 
        to get the average peak value do 'np.mean(maxtab, 0)[1]' on the results
    """
    rlen = range(len(deltas))
    maxtab = [ [] for i in rlen] # @UnusedVariable
    mintab = [ [] for i in rlen] # @UnusedVariable
    dump = [ [] for i in rlen] # Used to pop the first hit which always if false @UnusedVariable

    length = len(y_axis)
    if x_axis is None:
        x_axis = range(length)

    # perform some checks
    if length != len(x_axis):
        raise ValueError, "Input vectors y_axis and x_axis must have same length"
    if lookahead < 1:
        raise ValueError, "Lookahead must be above '1' in value"

    # needs to be a numpy array
    y_axis = np.asarray(y_axis)




    # Only detect peak if there is 'lookahead' amount of points after it
    for j, delta in enumerate(deltas):

        # maxima and minima candidates are temporarily stored in
        # mx and mn respectively
        mn, mx = np.Inf, -np.Inf

        for index, (x, y) in enumerate(zip(x_axis[:-lookahead], y_axis[:-lookahead])):
            if y > mx:
                mx = y
                mxpos = x
            if y < mn:
                mn = y
                mnpos = x
            ####look for max####
            if y < mx - delta and mx != np.Inf:
                # Maxima peak candidate found
                # look ahead in signal to ensure that this is a peak and not jitter
                if y_axis[index:index + lookahead].max() < mx:
                    maxtab[j].append((mxpos, mx))
                    dump[j].append(True)
                    # set algorithm to only find minima now
                    mx = np.Inf
                    mn = np.Inf

            ####look for min####
            if y > mn + delta and mn != -np.Inf:
                # Minima peak candidate found
                # look ahead in signal to ensure that this is a peak and not jitter
                if y_axis[index:index + lookahead].min() > mn:
                    mintab[j].append((mnpos, mn))
                    dump[j].append(False)
                    # set algorithm to only find maxima now
                    mn = -np.Inf
                    mx = -np.Inf


    # Remove the false hit on the first value of the y_axis
    for j in rlen:
        try:
            if dump[j][0]:
                maxtab[j].pop(0)
            else:
                mintab[j].pop(0)
            # del dump[j]
        except IndexError:
            # no peaks were found, should the function return empty lists?
            pass

    return maxtab, mintab

def peakdetect_zero_crossing(y_axis, x_axis=None, window=49):
    """
    Algorithm for detecting local maximas and minmias in a signal.
    Discovers peaks by dividing the signal into bins and retrieving the
    maximum and minimum value of each the even and odd bins respectively.
    Division into bins is performed by smoothing the curve and finding the
    zero crossings.
    
    Suitable for repeatable sinusoidal signals with some amount of RMS noise
    tolerable. Excecutes faster than 'peakdetect', although this function will
    break if the offset of the signal is too large. It should also be noted
    that the first and last peak will probably not be found, as this algorithm
    only can find peaks between the first and last zero crossing.
    
    keyword arguments:
    y_axis -- A list containg the signal over which to find peaks
    x_axis -- A x-axis whose values correspond to the 'y_axis' list and is used
        in the return to specify the postion of the peaks. If omitted the index
        of the y_axis is used. (default: None)
    window -- the dimension of the smoothing window; should be an odd integer
        (default: 49)
    
    return -- two lists [maxtab, mintab] containing the positive and negative
        peaks respectively. Each cell of the lists contains a tupple of:
        (position, peak_value) 
        to get the average peak value do 'np.mean(maxtab, 0)[1]' on the results
    """
    if x_axis is None:
        x_axis = range(len(y_axis))

    length = len(y_axis)
    if length != len(x_axis):
        raise ValueError, 'Input vectors y_axis and x_axis must have same length'

    # needs to be a numpy array
    y_axis = np.asarray(y_axis)

    zero_indices = zero_crossings(y_axis, window=window)
    period_lengths = np.diff(zero_indices)

    bins = [y_axis[indice:indice + diff] for indice, diff in
        zip(zero_indices, period_lengths)]

    even_bins = bins[::2]
    odd_bins = bins[1::2]
    # check if even bin contains maxima
    if even_bins[0].max() > abs(even_bins[0].min()):
        hi_peaks = [even.max() for even in even_bins]
        lo_peaks = [odd.min() for odd in odd_bins]
    else:
        hi_peaks = [odd.max() for odd in odd_bins]
        lo_peaks = [even.min() for even in even_bins]


    hi_peaks_x = [x_axis[np.where(y_axis == peak)[0]] for peak in hi_peaks]
    lo_peaks_x = [x_axis[np.where(y_axis == peak)[0]] for peak in lo_peaks]

    maxtab = [(x, y) for x, y in zip(hi_peaks, hi_peaks_x)]
    mintab = [(x, y) for x, y in zip(lo_peaks, lo_peaks_x)]

    return maxtab, mintab

def zero_crossings(y_axis, x_axis=None, window=24):
    """
    Algorithm to find zero crossings. Smoothens the curve and finds the
    zero-crossings by looking for a sign change.
    
    
    keyword arguments:
    y_axis -- A list containg the signal over which to find zero-crossings
    x_axis -- A x-axis whose values correspond to the 'y_axis' list and is used
        in the return to specify the postion of the zero-crossings. If omitted
        then the indice of the y_axis is used. (default: None)
    window -- half of the dimension of the smoothing window;
        (default: 24)
    
    return -- the x_axis value or the indice for each zero-crossing
    """
    # smooth the curve
    length = len(y_axis)
    if x_axis == None:
        x_axis = range(length)

    x_axis = np.asarray(x_axis)

    y_axis = smooth(y_axis, window)
    zero_crossings = np.where(np.diff(np.sign(y_axis)))[0]
    times = [x_axis[indice] for indice in zero_crossings]

    # check if zero-crossings are valid
    diff = np.diff(times)
    if diff.std() / diff.mean() > 0.1:
        raise ValueError, "smoothing window too small, false zero-crossings found"

    return times
