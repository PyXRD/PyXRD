# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from math import exp, sqrt, log, pi
import inspect
import time

sqrtpi = sqrt(pi)
sqrt2pi = sqrt(2*pi)
sqrt8 = sqrt(8)

def print_timing(func):
    def wrapper(*args, **kwargs):
        t1 = time.time()
        res = func(*args, **kwargs)
        t2 = time.time()
        print '%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0)
        return res
    return wrapper

def get_case_insensitive_glob(*strings):
    '''Ex: '*.ora' => '*.[oO][rR][aA]' '''
    return ['*.%s' % ''.join(["[%s%s]" % (c.lower(), c.upper()) for c in string.split('.')[1]]) for string in strings]
    
def retreive_lowercase_extension(glob):
    '''Ex: '*.[oO][rR][aA]' => '*.ora' '''
    return ''.join([ c.replace("[", "").replace("]", "")[:-1] for c in glob.split('][')])

def find_ge(a, x):
    'Find leftmost item greater than or equal to x'
    i = bisect_left(a, x)
    if i != len(a):
        return a[i]
    raise ValueError

def whoami():
    return inspect.stack()[1][3]

#expects the data to be sorted!!
def interpolate(data, x):
    x1, y1 = (0,0)
    x2, y2 = (0,0)
    for tx,ty in data:
        if tx > x:
            x1, y1 = (tx,ty)
            break
        else:
            x2, y2 = (tx,ty)
    return y1 + (x-x1) * (y2 - y1) / (x2 - x1)
   
"""def erf(x):
    # constants
    a1 =  0.254829592
    a2 = -0.284496736
    a3 =  1.421413741
    a4 = -1.453152027
    a5 =  1.061405429
    p  =  0.3275911

    # Save the sign of x
    sign = 1
    if x < 0:
        sign = -1
    x = abs(x)

    # A&S formula 7.1.26
    t = 1.0/(1.0 + p*x)
    y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t*exp(-x*x)
    
    return sign*y"""
    
#def erf(x, steps=1000):
#    result = 0.0
#    x = float(x)
#    dt = x / float(steps)
#    for i in range(steps+1):
#        t = float(i + 0.5)*dt
#        result += exp(-t**2)*dt
#    result *= 2 / sqrtpi
#    return result
   
def repos(ln, old_pos, new_pos):
    lb = min(new_pos, old_pos)
    ub = max(new_pos, old_pos)
    adj_range = []
    if new_pos < old_pos:
        adj_range.append(old_pos)
        adj_range += range(lb, ub)
    else:
        adj_range += range(lb+1, ub+1)
        adj_range.append(old_pos)
    return range(0,lb) + adj_range + range(ub,ln-1)
    
def simple_repos(ln, old_pos, new_pos):
    r1 = range(ln)
    val = r1[old_pos]
    del r1[old_pos]
    r1.insert(new_pos, val)
    return r1
    
def smart_repos(ln, old_pos, new_pos):
    if ln > 65:
        return repos(ln, old_pos, new_pos)
    else:
        return simple_repos(ln, old_pos, new_pos)
        
class DelayedProxy():
    __modified__ = set([])

    def __init__(self, subject):
        self.__subject__ = subject
    def __getattr__(self, name):
        if not name in ["__modified__", "__dict__"]:
            return getattr( self.__subject__, name )
    def __setattr__(self, name, val):
        if not name in ["__modified__", "__dict__"]:
            self.__modified__.add(name)
            self.__dict__[name] = val
    
    def apply_changes(self):
        print "Applying changes made to object of type %s:" % type(self.__subject__)
        for name in self.__modified__:
            if not name in ["__subject__"]:
                print "  - %s" % name
                setattr(self.__subject__, name, self.__dict__[name])
        self.__modified__ = set([])
    
    def discard_changes(self):
        print "Discarding previously made changes to object of type %s:" % type(self.__subject__)
        for name in self.__modified__:
            if not name in ["__subject__"]:
                print "  - %s" % name
                del self.__dict__[name]
        self.__modified__ = set([])
        
def lognormal(T, a, b):
    return sqrt2pi * exp(-(log(T) - a)**2 / (2.0*(b**2))) / (abs(b)*T)
