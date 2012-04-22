# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import numpy as np

def peakdetect(y_axis, x_axis = None, lookahead = 500, delta = 0):
    mintabs, maxtabs = multi_peakdetect(y_axis, x_axis, lookahead, [delta])
    return mintabs[0], maxtabs[0]

def multi_peakdetect(y_axis, x_axis = None, lookahead = 500, deltas = [0]):
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
    maxtab = [ [] for i in rlen]
    mintab = [ [] for i in rlen]
    dump = [ [] for i in rlen]   #Used to pop the first hit which always if false
       
    length = len(y_axis)
    if x_axis is None:
        x_axis = range(length)
    
    #perform some checks
    if length != len(x_axis):
        raise ValueError, "Input vectors y_axis and x_axis must have same length"
    if lookahead < 1:
        raise ValueError, "Lookahead must be above '1' in value"
    
    #needs to be a numpy array
    y_axis = np.asarray(y_axis)
    

    
    
    #Only detect peak if there is 'lookahead' amount of points after it
    for j, delta in enumerate(deltas):
    
        #maxima and minima candidates are temporarily stored in
        #mx and mn respectively
        mn, mx = np.Inf, -np.Inf
    
        for index, (x, y) in enumerate(zip(x_axis[:-lookahead], y_axis[:-lookahead])):
            if y > mx:
                mx = y
                mxpos = x
            if y < mn:
                mn = y
                mnpos = x    
            ####look for max####
            if y < mx-delta and mx != np.Inf:
                #Maxima peak candidate found
                #look ahead in signal to ensure that this is a peak and not jitter
                if y_axis[index:index+lookahead].max() < mx:
                    maxtab[j].append((mxpos, mx))
                    dump[j].append(True)
                    #set algorithm to only find minima now
                    mx = np.Inf
                    mn = np.Inf
            
            ####look for min####
            if y > mn+delta and mn != -np.Inf:
                #Minima peak candidate found 
                #look ahead in signal to ensure that this is a peak and not jitter
                if y_axis[index:index+lookahead].min() > mn:
                    mintab[j].append((mnpos, mn))
                    dump[j].append(False)
                    #set algorithm to only find maxima now
                    mn = -np.Inf
                    mx = -np.Inf
    
    
    #Remove the false hit on the first value of the y_axis
    for j in rlen:
        try:
            if dump[j][0]:
                maxtab[j].pop(0)
                #print "pop max"
            else:
                mintab[j].pop(0)
                #print "pop min"
            #del dump[j]
        except IndexError:
            #no peaks were found, should the function return empty lists?
            pass
    
    return maxtab, mintab



def peakdetect_zero_crossing(y_axis, x_axis = None, window = 49):
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
    
    #needs to be a numpy array
    y_axis = np.asarray(y_axis)
    
    zero_indices = zero_crossings(y_axis, window = window)
    period_lengths = np.diff(zero_indices)
    
    bins = [y_axis[indice:indice+diff] for indice, diff in 
        zip(zero_indices, period_lengths)]
    
    even_bins = bins[::2]
    odd_bins = bins[1::2]
    #check if even bin contains maxima
    if even_bins[0].max() > abs(even_bins[0].min()):
        hi_peaks = [bin.max() for bin in even_bins]
        lo_peaks = [bin.min() for bin in odd_bins]
    else:
        hi_peaks = [bin.max() for bin in odd_bins]
        lo_peaks = [bin.min() for bin in even_bins]
    
    
    hi_peaks_x = [x_axis[np.where(y_axis==peak)[0]] for peak in hi_peaks]
    lo_peaks_x = [x_axis[np.where(y_axis==peak)[0]] for peak in lo_peaks]
    
    maxtab = [(x,y) for x,y in zip(hi_peaks, hi_peaks_x)]
    mintab = [(x,y) for x,y in zip(lo_peaks, lo_peaks_x)]
    
    return maxtab, mintab
        


def smooth(x,window_len=11,window='hanning'):
    """
    smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    input:
        x: the input signal 
        window_len: the dimension of the smoothing window; should be an odd integer
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
    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."


    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


    s=np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    return y
    
     
def zero_crossings(y_axis, x_axis = None, window = 49):
    """
    Algorithm to find zero crossings. Smoothens the curve and finds the
    zero-crossings by looking for a sign change.
    
    
    keyword arguments:
    y_axis -- A list containg the signal over which to find zero-crossings
    x_axis -- A x-axis whose values correspond to the 'y_axis' list and is used
        in the return to specify the postion of the zero-crossings. If omitted
        then the indice of the y_axis is used. (default: None)
    window -- the dimension of the smoothing window; should be an odd integer
        (default: 49)
    
    return -- the x_axis value or the indice for each zero-crossing
    """
    #smooth the curve
    length = len(y_axis)
    if x_axis == None:
        x_axis = range(length)
    
    x_axis = np.asarray(x_axis)
    
    y_axis = smooth(y_axis, window)[:length]
    zero_crossings = np.where(np.diff(np.sign(y_axis)))[0]
    times = [x_axis[indice] for indice in zero_crossings]
    
    #check if zero-crossings are valid
    diff = np.diff(times)
    if diff.std() / diff.mean() > 0.1:
        raise ValueError, "smoothing window too small, false zero-crossings found"
    
    return times
