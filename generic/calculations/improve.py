# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gc
from pympler import tracker
from pympler import refbrowser
import sys
try:    from cStringIO import StringIO
except: from StringIO import StringIO

from scipy.optimize import fmin_l_bfgs_b

import settings
    
from project.models import Project
from generic.models.metaclasses import pyxrd_object_pool

from .exceptions import wrap_exceptions

def setup_project(projectf):
    # Only import these at this point, the cause a considerable increase in
    # memory usage, so if no projectf was passed to improve_solutions, this
    # module does not use more then it needs.
    
    settings.CACHE = None
    settings.apply_runtime_settings()
        
    pyxrd_object_pool.clear()
    
    f = StringIO()
    f.write(projectf)
    project = Project.load_object(f)
    f.close()
    
    return project

@wrap_exceptions
def improve_solution(projectf, mixture_index, solution, residual, l_bfgs_b_kwargs={}):
    if projectf!=None:
        #Retrieve project and mixture:
        project = setup_project(projectf)
        del projectf
        
        mixture = project.mixtures.get_item_by_index(mixture_index)

        #Setup context again:
        mixture.update_refinement_treestore()
        mixture.refiner.setup_context(store=False) #we already have a dumped project
        context = mixture.refiner.context
                                       
        #Refine solution            
        vals = fmin_l_bfgs_b(
            context.get_residual_for_solution,
            solution,
            approx_grad=True,
            bounds=context.ranges,
            **l_bfgs_b_kwargs            
        )
        new_solution, new_residual = tuple(vals[0:2])
                
        #Return result
        return new_solution, new_residual
    else:
        return solution, residual
