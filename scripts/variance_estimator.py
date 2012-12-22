#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os, sys
from math import log

import numpy as np
from itertools import combinations

from project.models import Project

def run(args):
    #batch csv file generator for a file containin a number of projects
    if args and args.filename!="":
        project = Project.load_object(args.filename)
        for i, mixture in enumerate(project.mixtures.iter_objects()):
            mixture.update_refinement_treestore()
            refs = []
            props = ("d001", "F1", "F2", "F3", "F4", "W1", "P11_or_P22",)
            for ref in mixture.refinables.iter_objects():
                if ref.refinable and ref.prop in props:
                    val = ref.value
                    delta = 0.1
                    if val > 1.0:
                        delta = log(val)
                    ref.value_min = val - delta
                    ref.value_max = val + delta
                    refs.append(ref)

            combs = list(combinations(refs, 2))
            fractions = np.zeros(shape=(len(combs), len(mixture.fractions)))
            rps = np.zeros(shape=(len(combs),))

            print len(combs) * 9, " calculations to be made!"

            for k, (ref1, ref2) in enumerate(combs):
                print "\rProgress: %00.f%%" % float(100.0 * k / len(combs)),
                for i in range(3):
                    for j in range(3):
                        ref1.value = ref1.value_min + float(i) * (ref1.value_max - ref1.value_min) / 2.0
                        ref2.value = ref2.value_min + float(j) * (ref2.value_max - ref2.value_min) / 2.0
                        rp = mixture.optimize()
                        if rp <= 30.0:
                            inv_rp = 30.0 - rp
                            fractions[k,:] = np.array(mixture.fractions, dtype=float)
                            rps[k] = inv_rp
                        #print "\rProgress: %00f%% - iter %d of 25" % (float(100.0 * k / len(combs)), i*5+(j+1))
                                       
            print "Phases:"
            print mixture.phases
            print "Unweighted average:"
            print np.average(fractions.transpose(), axis=1, weights=rps)
            print np.std(fractions.transpose()*rps, axis=1) / np.sum(rps)
            print "Weighted average:"
            print np.average(fractions.transpose(), axis=1, weights=rps)
            print np.std(fractions.transpose(), axis=1)
            print "Average Rp value:"
            print np.average(30.0-rps), "+/-", np.std(30.0-rps)

        
        del project
                
        print "Finished!"
