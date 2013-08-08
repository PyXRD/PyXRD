# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import settings

def get_all_refine_methods():
    from .scipy_runs import RefineLBFGSBRun, RefineBasinHoppingRun
    from .deap_gen import RefineCMAESRun
    from .deap_swarm import RefineMPSORun
    
    try:
        from .custom_brute import RefineBruteForceRun
    except ImportError:
        from .scipy_runs import RefineBruteForceRun

    return {
            0: RefineLBFGSBRun(),
            1: RefineCMAESRun(),
            2: RefineMPSORun(),
            3: RefineBruteForceRun(),
            4: RefineBasinHoppingRun(),
    }

__all__ = [
    "get_all_refine_methods"
]


