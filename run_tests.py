#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import sys, os
base = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(base, "pyxrd"))

if __name__ == "__main__":
    from test import run_all_tests
    run_all_tests()
