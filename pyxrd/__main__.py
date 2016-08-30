# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, sys

# Make sure the current path is used for loading PyXRD modules:
mod = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not mod in sys.path:
    sys.path.insert(1, mod)

from pyxrd.core import run_main
run_main()
