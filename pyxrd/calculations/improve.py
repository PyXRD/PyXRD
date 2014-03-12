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
    # Only import these at this point, the cause a considerable increase in
    # memory usage, so if no projectf was passed to improve_solutions, this
    # module does not use more then it needs.
    from pyxrd.data import settings
    if settings.CACHE == "FILE":
        settings.CACHE = "FILE_FETCH_ONLY"
    else:
        settings.CACHE = None
    settings.apply_runtime_settings()

    from pyxrd.project.models import Project
    type(Project).object_pool.clear()

    f = StringIO()
    f.write(projectf)
    project = Project.load_object(f)
    f.close()

    return project

@wrap_exceptions
def run_refinement(projectf, mixture_index, options):
    if projectf is not None:
        from pyxrd.data import settings
        settings.CACHE = None
        settings.apply_runtime_settings()

        from pyxrd.generic import pool
        pool.get_pool()

        from pyxrd.project.models import Project

        type(Project).object_pool.clear()
        project = Project.load_object(None, data=projectf)
        del projectf
        import gc
        gc.collect()

        mixture = project.mixtures[mixture_index]
        mixture.update_refinement_treestore()
        mixture.refiner.setup_context(store=False) # we already have a dumped project
        context = mixture.refiner.context
        context.options = options

        mixture.refiner.refine(stop=pool.pool_stop)

        return list(context.best_solution), context.best_residual, (context.record_header, context.records) #@UndefinedVariable

@wrap_exceptions
def improve_solution(projectf, mixture_index, solution, residual, l_bfgs_b_kwargs={}):
    if projectf is not None:
        # Retrieve project and mixture:
        project = setup_project(projectf)
        del projectf

        mixture = project.mixtures[mixture_index]

        with mixture.data_changed.ignore():

            # Setup context again:
            mixture.update_refinement_treestore()
            mixture.refiner.setup_context(store=False) # we already have a dumped project
            context = mixture.refiner.context

            # Refine solution
            vals = fmin_l_bfgs_b(
                context.get_residual_for_solution,
                solution,
                approx_grad=True,
                bounds=context.ranges,
                **l_bfgs_b_kwargs
            )
            new_solution, new_residual = tuple(vals[0:2])

        # Return result
        return new_solution, new_residual
    else:
        return solution, residual
