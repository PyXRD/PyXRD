#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

# import cProfile, pstats, StringIO

import multiprocessing
import os
import codecs
from pyxrd.project.models import Project

"""
ADDED 0.01 NOISE
"""

from pyxrd.data import settings

def run(args):
    if args and args.filename != "":
        print "Proccessing args..."
        project_file, k, mixture_index = tuple(args.filename.split("###", 2))
        base_path = os.path.dirname(args.filename)
        stop_event = multiprocessing.Event()

        print "Loading project file..."
        project = Project.load_object(project_file)
        print "Running Project", os.path.basename(project_file), "Trial", k

        for i, mixture in enumerate(project.mixtures):
            if i == int(mixture_index):

                # pr = cProfile.Profile()
                # pr.enable()
                # try:
                with mixture.data_changed.hold():
                    settings.CACHE = "FILE" # enable active caching
                    mixture.update_refinement_treestore()
                    mixture.randomize()
                    mixture.optimizer.optimize()

                    settings.CACHE = "FILE_FETCH_ONLY" # disable active caching
                    mixture.refiner.setup_context(store=True)
                    mixture.refiner.refine(stop=stop_event)
                # except:
                #    pass
                # finally:
                #    pr.disable()
                #    with open("pyxrd_stats", "w+") as f:
                #        sortby = 'cumulative'
                #        ps = pstats.Stats(pr, stream=f).sort_stats(sortby)
                #        ps.print_stats()
                #    print "STATS DUMPED!"

                context = mixture.refiner.context

                recordf = os.path.basename(project_file).replace(".pyxrd", "")
                recordf = base_path + "/" + "record#" + str(k) + " " + recordf + " " + mixture.name
                with codecs.open(recordf, 'w', 'utf-8') as f:

                    f.write("################################################################################\n")
                    f.write(recordf + "\n")
                    f.write("Mixture " + str(i) + " and trial " + str(k) + "\n")
                    f.write("Property name, initial, best, min, max" + "\n")
                    for j, ref_prop in enumerate(context.ref_props):

                        if ref_prop.obj.Meta.store_id == 'Phase':
                            descriptor = ref_prop.obj.name.encode("utf-8")
                            descriptor += u" | * | "
                            descriptor += ref_prop.title.decode("utf-8")
                        elif ref_prop.obj.Meta.store_id in ('DritsCSDSDistribution', 'LogNormalCSDSDistribution'):
                            descriptor = ref_prop.obj.phase.name.encode("utf-8") + u" | * | " + ref_prop.title.decode("utf-8")
                        elif ref_prop.obj.name == 'Probabilities':
                            descriptor = ref_prop.obj.phase.name.encode("utf-8") + u" | * | " + ref_prop.title.decode("utf-8")
                        elif ref_prop.obj.Meta.store_id == 'Component':
                            descriptor = ref_prop.obj.phase.name.encode("utf-8") + u" | " + ref_prop.obj.name + u" | " + ref_prop.title.decode("utf-8")
                        elif ref_prop.obj.Meta.store_id == 'UnitCellProperty':
                            descriptor = ref_prop.obj.component.phase.name.encode("utf-8") + u" | " + ref_prop.component.name + u" | " + ref_prop.title.decode("utf-8")
                        # else:
                        #    descriptor = ref_prop.title

                        line = ", ".join([
                            descriptor,
                            str(context.initial_solution[j]),
                            str(context.best_solution[j]),
                            str(ref_prop.value_min),
                            str(ref_prop.value_max),
                        ])
                        f.write(line + "\n")
                    f.write("################################################################################\n")
                    if context.record_header is not None:
                        f.write(", ".join(context.record_header) + "\n")
                        for record in context.records:
                            f.write(", ".join(map(lambda f: "%.7f" % f, record)) + "\n")
                        f.write("################################################################################\n")
                    """context.apply_best_solution()
                    mixture.optimizer.optimize()
                    for bg, scale in izip(mixture.scales, mixture.bg_shifts):
                        print "BG1:", bg, "SCALE1:", scale
                    for fraction, phase in izip(mixture.fractions, mixture.phases):
                        print phase, "contents:", "%.1f" % fraction*100, " wt%"
                    f.write("################################################################################\n")"""

        pass # end
