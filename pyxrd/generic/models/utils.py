# coding=UTF-8
# ex:ts=4:sw=4:et

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

def not_none(passed, default):
    """
        Convenience function for shortening long statements in __init__ functions
        where this pattern is used a lot.
    """
    return passed if passed is not None else default