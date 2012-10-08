#!/usr/bin/python

import pickle
import sys

import numpy as np

def run(project):
    #simple test:
    for mixture in project.mixtures.iter_objects():
        np.savetxt("output.txt", mixture.get_result_description(), fmt='%s', delimiter=';')
    """print "PICKLE DATA TEST FOR PROJECT %s" % project.data_name
    
    def dump_and_load(obj):
        obj_dump = pickle.dumps(obj)
        if hasattr(obj, "parent"):
            print "OBJECT HAS PARENT: %s" % obj.parent
        print "PICKLED DATA HAS SIZE %d" % sys.getsizeof(obj_dump)
        obj2 = pickle.loads(obj_dump)
        print "LOADED OBJECT IS: %s" % obj2
        if hasattr(obj2, "parent"):
            print "LOADED OBJECT HAS PARENT: %s" % obj2.parent
        return obj2

    p2 = dump_and_load(project)

    for mixt in p2.data_mixtures.iter_objects():
        if not mixt.auto_run:
            mixt.optimize(silent=True)
        mixt.apply_result()
    for spec in p2.data_specimens.iter_objects():
        spec.statistics.update_statistics()
        print spec.statistics.data_Rp"""
    
    
