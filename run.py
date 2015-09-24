#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

if __name__ == "__main__":

    from pyxrd.core import setup_logging, run_main

    # Setup basic logging
    setup_logging(basic=True)

    # This will generate a very slim pool of worker processes, with as little
    # as possible shared state
    from pyxrd.generic.pool import get_pool
    get_pool()

    # Setup & run PyXRD
    run_main()
