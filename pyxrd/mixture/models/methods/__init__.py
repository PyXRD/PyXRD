# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.data import settings
import logging
logger = logging.getLogger(__name__)

def get_all_refine_methods():

    methods = {}

    from .scipy_runs import RefineLBFGSBRun, RefineBasinHoppingRun
    methods[0] = RefineLBFGSBRun()
    methods[4] = RefineBasinHoppingRun()

    try:
        from .deap_gen import RefineCMAESRun
        methods[1] = RefineCMAESRun()
        from .deap_swarm import RefineMPSORun
        methods[2] = RefineMPSORun()
    except ImportError:
        logger.warning("Could not import DEAP refinement algorithms, is DEAP installed?")

    try:
        from .custom_brute import RefineBruteForceRun
    except ImportError:
        from .scipy_runs import RefineBruteForceRun
    methods[3] = RefineBruteForceRun()

    return methods

__all__ = [
    "get_all_refine_methods"
]


