#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

# import cProfile, pstats, StringIO

import logging
logger = logging.getLogger(__name__)

import multiprocessing
import os
import codecs
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
    if args and args.filename != "":
        logging.info("Proccessing args...")
        project_file, k, mixture_index = tuple(args.filename.split("###", 2))
        base_path = os.path.dirname(args.filename)
        stop_event = multiprocessing.Event()

        logging.info("Loading project file...")
        project = Project.load_object(project_file)
        logging.info(" ".join(["Running Project", os.path.basename(project_file), "Trial", k]))

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

                        #TODO move this somehwere in the main code:
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
                        else:
                            logging.warning("Unkown ref prop when getting title for %r" % ref_prop)
                            descriptor = "?Unkown?"
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

                    context.apply_best_solution()
                    mixture.optimizer.optimize()

                    project_file_output = base_path + "/" + os.path.basename(project_file).replace(".pyxrd", "") + " - mixture %s - trial %s.pyxrd" % (str(i), str(k))
                    project.save_object(file=project_file_output)

        pass # end
