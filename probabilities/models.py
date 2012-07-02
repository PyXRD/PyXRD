# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import numpy as np

from probabilities.R0models import R0G1Model, R0G2Model, R0G3Model, R0G4Model, R0G5Model, R0G6Model
from probabilities.R1models import R1G2Model, R1G3Model, R1G4Model
from probabilities.R2models import R2G2Model
from probabilities.R3models import R3G2Model

# Overview of what is:
#   x   = currently implemented
#   np  = not possible
#   -/o = not yet implemented
#   o   = priority
#
#       G1  G2  G3  G4  G5  G6
#   R0  x   x   x   x   x   x
#   R1  np  x   x   x   -   -
#   R2  np  x   o   -   -   -
#   R3  np  x   -   -   -   -

RGbounds = np.array([
    [1,  1,  1,  1,  1,  1],
    [-1, 1,  1,  1,  0,  0],
    [-1, 1,  0,  0,  0,  0],
    [-1, 1,  0,  0,  0,  0],
])

def get_Gbounds_for_R(R, G):
    global RGbounds
    maxR, maxG = RGbounds.shape
    low, upp = 1,6
    if R >= 0 and R < maxR:
        bounds = RGbounds[R]
        low, upp = 1 + np.argmax(bounds==1), maxG - np.argmax(bounds[::-1]==1)
    else:
        raise ValueError, "Cannot yet handle R%d!" % R
    return (low, upp, max(min(G, upp), low))

def get_Rbounds_for_G(G, R):
    global RGbounds
    maxR, maxG = RGbounds.shape
    low, upp = 0,0
    if G >= 1 and G <= maxG:
        bounds = RGbounds[:,G-1]
        low, upp = np.argmax(bounds==1), maxR - np.argmax(bounds[::-1]==1) - 1
    else:
        raise ValueError, "Cannot yet handle %d layer structures!" % G
    return (low, upp, max(min(R, upp), low))

def get_correct_probability_model(phase):
    global RGbounds
    if phase!=None:
        G = phase.data_G
        R = phase.data_R
        
        if (RGbounds[R,G-1] > 0):
            class_name = "R%dG%dModel" % (R,G)
            return globals()[class_name](parent=phase)
        else:
            raise ValueError, "Cannot (yet) handle R%d for %d layer structures!" % (R, G)

