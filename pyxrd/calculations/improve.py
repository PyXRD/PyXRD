# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

try:
    from cStringIO import StringIO #@UnusedImport
except:
    from StringIO import StringIO #@Reimport

from scipy.optimize import fmin_l_bfgs_b

from .exceptions import wrap_exceptions

def setup_project(projectf):
    from pyxrd.file_parsers.json_parser import JSONParser
    from pyxrd.project.models import Project
    type(Project).object_pool.clear()

    f = StringIO(projectf)
    project = JSONParser.parse(f)
    f.close()

    return project

@wrap_exceptions
def run_refinement(projectf, mixture_index):
    """
        Runs a refinement setup for 
            - projectf: project data
            - mixture_index: what mixture in the project to use
    """
    if projectf is not None:
        from pyxrd.data import settings
        settings.initialize()

        # Retrieve project and mixture:
        project = setup_project(projectf)
        del projectf

        import gc
        gc.collect()

        mixture = project.mixtures[mixture_index]
        mixture.refinement.update_refinement_treestore()
        refiner = mixture.refinement.get_refiner()
        refiner.refine()

        return list(refiner.history.best_solution), refiner.history.best_residual

@wrap_exceptions
def improve_solution(projectf, mixture_index, solution, residual, l_bfgs_b_kwargs={}):
    if projectf is not None:
        from pyxrd.data import settings
        settings.initialize()

        # Retrieve project and mixture:
        project = setup_project(projectf)
        del projectf

        mixture = project.mixtures[mixture_index]

        with mixture.data_changed.ignore():

            # Setup context again:
            mixture.update_refinement_treestore()
            refiner = mixture.refinement.get_refiner()

            # Refine solution
            vals = fmin_l_bfgs_b(
                refiner.get_residual,
                solution,
                approx_grad=True,
                bounds=refiner.ranges,
                **l_bfgs_b_kwargs
            )
            new_solution, new_residual = tuple(vals[0:2])

        # Return result
        return new_solution, new_residual
    else:
        return solution, residual
