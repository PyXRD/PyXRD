#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

B_DO_PROFILING = False
if B_DO_PROFILING:
    import cProfile, pstats

import logging
logger = logging.getLogger(__name__)

import multiprocessing
import os
import codecs
import numpy as np
from pyxrd.project.models import Project

"""
ADDED 0.01 NOISE
"""

from pyxrd.data import settings

def run(args):
    """
    This is a simple script that will open a PyXRD project file,
    will run a refinement for a certain mixture, and store the results
    in an overview file and the best solution as a new project file.
    The refinement setup is left unchanged, so be sure you have correctly 
    defined parameter ranges and chosen a good refinement strategy (CMA-ES
    is recommended).
    
    To use this script, launch it using PyXRD's core.py launcher script as:
      python core.py -s pyxrd/scripts/refinement_generator.py "$FILENAME###$I###$J"
    in which: 
        - $FILENAME can be replaced with the absolute path to the actual
          project filename
        - $I is the index of the mixture to refine and
        - $J is the 'trial' number, which is added to the record file and to the
          best solution project file.
        - leave the three # (hashes) where they are, they are used as separators 
        
    You can use this script (e.g. on high-performance computing clusters) to
    run several iterations of the same project. Reasaons why you would want 
    to do this are for benchmarking, checking solution reliability, ... 
    Just change the trial number from e.g. 0 to 49 to have 50 iterations.
    """

    ## TODO:
    ##  - use a uniform distribution of starting solutions:
    ##      xs = np.random.uniform(size=50)
    ##      ys = np.random.uniform(size=50)
    ##      zs = np.random.uniform(size=50)

    ##
    ## When the jobs are submitted, load the project and mixture once,
    ## create the # of staring solutions and store them in a file (using np IO)
    ## Then here we can load them and pick the one we need.
    ##

    if args and args.filename != "":
        logging.info("Proccessing args...")
        project_file, k, mixture_index = tuple(args.filename.split("###", 2))
        base_path = os.path.dirname(args.filename)
        start_solutions_fname = os.path.join(
            base_path,
            "start_solutions %s mixture %s" % (os.path.basename(project_file), mixture_index)
        )
        stop_event = multiprocessing.Event()

        logging.info("Loading project file...")
        project = Project.load_object(project_file)
        logging.info(" ".join(["Running Project", os.path.basename(project_file), "Trial", k]))

        for i, mixture in enumerate(project.mixtures):
            if i == int(mixture_index):

                if B_DO_PROFILING:
                    pr = cProfile.Profile()
                    pr.enable()
                try:
                    with mixture.data_changed.hold():

                        mixture.update_refinement_treestore()
                        mixture.refiner.setup_context(store=True)

                        if int(k) == 0: #First run, create solutions & store for later use:
                            start_solutions = mixture.refiner.context.get_uniform_solutions(50)
                            np.savetxt(start_solutions_fname, start_solutions)
                        else:
                            start_solutions = np.loadtxt(start_solutions_fname)

                        settings.CACHE = "FILE" # enable active caching
                        mixture.refiner.context.set_initial_solution(start_solutions[k, ...])
                        mixture.optimizer.optimize()
                        settings.CACHE = "FILE_FETCH_ONLY" # disable active caching

                        mixture.refiner.refine(stop=stop_event)
                except:
                    raise
                finally:
                    if B_DO_PROFILING:
                        pr.disable()
                        with open("pyxrd_stats", "w+") as f:
                            sortby = 'cumulative'
                            ps = pstats.Stats(pr, stream=f).sort_stats(sortby)
                            ps.print_stats()

                context = mixture.refiner.context

                recordf = os.path.basename(project_file).replace(".pyxrd", "")
                recordf = base_path + "/" + "record#" + str(k) + " " + recordf + " " + mixture.name
                with codecs.open(recordf, 'w', 'utf-8') as f:

                    f.write("################################################################################\n")
                    f.write(recordf + "\n")
                    f.write("Mixture " + str(i) + " and trial " + str(k) + "\n")
                    f.write("Property name, initial, best, min, max" + "\n")
                    for j, ref_prop in enumerate(context.ref_props):
                        line = ", ".join([
                            ref_prop.get_descriptor(),
                            str(context.initial_solution[j]),
                            str(context.best_solution[j]),
                            str(ref_prop.value_min),
                            str(ref_prop.value_max),
                        ])
                        f.write(line + "\n")
                    f.write("################################################################################\n")

                    def write_records(f, record_header, records):
                        f.write(", ".join(record_header) + "\n")
                        for record in records:
                            f.write(", ".join(map(lambda f: "%.7f" % f, record)) + "\n")
                        f.write("################################################################################\n")
                    if context.record_header is not None:
                        write_records(f, context.record_header, context.records)
                    if hasattr(context, "pcma_records"):
                        for record_header, records in context.pcma_records:
                            write_records(f, record_header, records)

                    # Apply found solution and save:
                    context.apply_best_solution()
                    mixture.optimizer.optimize()

                    project_file_output = base_path + "/" + os.path.basename(project_file).replace(".pyxrd", "") + " - mixture %s - trial %s.pyxrd" % (str(i), str(k))
                    project.save_object(file=project_file_output)

        pass # end
