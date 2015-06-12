# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import traceback
import sys

import os
from imp import find_module
from types import ModuleType, ClassType

import importlib, pkgutil
def import_submodules(package_name):
    """ Import all submodules of a module, recursively

    :param package_name: Package name
    :type package_name: str
    :rtype: dict[types.ModuleType]
    """
    package = sys.modules[package_name]
    
    modules = {}
    for _, name, _ in pkgutil.walk_packages(package.__path__):
        try:
            modules[name] = importlib.import_module(package_name + '.' + name)
        except:
            logger.warning("Could not import %s refinement method modules, are all dependencies installed? Error was:" % name)
            _, _, tb = sys.exc_info()
            traceback.print_tb(tb)
    return modules
        
__all__ = import_submodules(__name__).keys()

from .refine_run import MethodMeta
get_all_refine_methods = MethodMeta.get_all_methods

"""
def get_all_refine_methods():

    methods = {}

    from .scipy_runs import RefineLBFGSBRun, RefineBasinHoppingRun
    methods[0] = RefineLBFGSBRun()
    methods[4] = RefineBasinHoppingRun()

    try:
        from .deap_cma import RefineCMAESRun
        methods[1] = RefineCMAESRun()
        from .deap_swarm import RefineMPSORun
        methods[2] = RefineMPSORun()
        from .deap_pcma import RefinePCMAESRun
        methods[5] = RefinePCMAESRun()
        from .deap_pso_cma import RefinePSOCMAESRun
        methods[6] = RefinePSOCMAESRun()
    
    try:
        from .custom_brute import RefineBruteForceRun
    except ImportError:
        from .scipy_runs import RefineBruteForceRun
    methods[3] = RefineBruteForceRun()

    return methods

__all__ = [
    "get_all_refine_methods"
]"""


