#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os

import numpy as np

from pyxrd.project.models import Project


def get_result_description(mixture):
    n, m = mixture.phase_matrix.shape

    res = "---------------------------------------------------------\n"
    res += "%s mixture results\n" % mixture.name
    res += "---------------------------------------------------------\n"
    res += "\n   %d specimens:\n" % n
    for i in range(n):
        res += "       - %s   bgr: %5.2f   scl: %5.2f\n" % (mixture.specimens[i].name.ljust(15), mixture.bgshifts[i], mixture.scales[i])
    res += "    (bgr=background shift, scl=absolute scale factor)\n"
    res += "\n   %d phases:\n" % m

    phase_props = [
        "name",
        "wt%",
        "sigma_star",
        "T_mean",
        "probs",
    ]
    comp_props = [
        "name",
        "wt%",
        "d-spacing",
        "relations",
    ]

    phases = np.unique(mixture.phase_matrix)
    max_G = 1
    for phase in phases:
        max_G = max(phase.G, max_G)

    num_rows = len(phase_props) + len(comp_props) * max_G
    num_cols = phases.size + 1

    text_matrix = np.zeros(shape=(num_rows, num_cols), dtype=object)
    text_matrix[:] = ""
    i = 1
    for phase_index in range(m):
        phases = np.unique(mixture.phase_matrix[:, phase_index])
        for phase in phases:
            j = 0
            for prop in phase_props:
                text_matrix[j, 0] = prop
                text = ""
                if prop == "name":
                    text = "%s" % phase.name
                elif prop == "wt%":
                    text = "%.1f" % (mixture.fractions[phase_index] * 100.0)
                elif prop == "sigma_star":
                    text = "%.1f" % phase.sigma_star
                elif prop == "T_mean":
                    text = "%.1f" % phase.CSDS_distribution.average
                elif prop == "probs":
                    text += "\""
                    for descr in phase.probabilities.get_prob_descriptions():
                        text += "%s\n" % descr
                    text += "\""
                text_matrix[j, i] = text
                j += 1
            for k, component in enumerate(phase.components):
                for prop in comp_props:
                    text_matrix[j, 0] = prop
                    text = ""
                    if prop == "name":
                        text = "%s" % component.name
                    elif prop == "wt%":
                        text = "%.1f" % (phase.probabilities.mW[k] * 100)
                    elif prop == "d-spacing":
                        text = "%.3f" % component.cell_c
                        if component.delta_c != 0:
                            text += " +/- %s" % component.delta_c
                    elif prop == "relations":
                        text += "\""
                        for relation in component.atom_relations:
                            text += "%s: %.3f\n" % (relation.name, relation.value)
                        text += "\""
                    text_matrix[j, i] = text
                    j += 1
            i += 1
    return text_matrix


def run(args):
    # batch csv file generator for a file containin a number of projects
    if args and args.filename != "":
        projects = []
        with open(args.filename, 'r') as f:
            for project_file in f:
                project_file = project_file.rstrip()
                print "Parsing: %s" % project_file
                project = Project.load_object(project_file)
                for i, mixture in enumerate(project.mixtures):

                    np.savetxt(
                        "%s/%s" % (os.path.dirname(project_file), os.path.basename(project_file).replace(".pyxrd", "-%d.csv" % i, 1)),
                        get_result_description(mixture), fmt='%s', delimiter=';'
                    )
                del project

        print "Finished!"
