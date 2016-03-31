# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import traceback
import sys
import importlib, pkgutil

from imp import find_module
from types import ModuleType, ClassType

import logging
logger = logging.getLogger(__name__)

"""
    This scans the module for submudules and imports them. This will
    trigger the registration of any refinement method classes 
    (i.e. RefineRun subclasses).
    
    Every RefineRun class is callable. 
    When calling a RefineRun sub-class, you should pass the RefineContext as the first
    argument, a stop signal, and an optional dict of options (see the class
    definitions for what options you can use). 
    Internally, this will set-up the class and then call its own `run()` method, 
    starting the refinement.  

    As such, to an external user, these 'classes' appear as simple functions.
"""


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


