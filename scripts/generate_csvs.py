#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, sys

import numpy as np

from project.models import Project

def run(args):
    #batch csv file generator for a file containin a number of projects
    if args and args.filename!="":
        projects = []
        with open(args.filename, 'r') as f:
            for project_file in f:
                project_file = project_file.rstrip()
                print "Parsing: %s" % project_file
                project = Project.load_object(project_file)
                for i, mixture in enumerate(project.mixtures.iter_objects()):
                    np.savetxt(
                        "%s/%s" % (os.path.dirname(project_file), os.path.basename(project_file).replace(".pyxrd", "-%d.csv" % i, 1)), 
                        mixture.get_result_description(), fmt='%s', delimiter=';'
                    )
                del project
                
        print "Finished!"
