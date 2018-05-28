#!/usr/bin/env python3

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

if __name__ == "__main__":
    # Add parent dir to the path:
    import os, sys
    sys.path.insert(1, os.path.join(sys.path[0], '../..'))    

    from pyxrd.logs import setup_logging
    from pyxrd.server import settings  # @UnusedImport
    setup_logging(basic=True, prefix="PYRO NAMESERVER:")

    import Pyro4.naming
    Pyro4.naming.startNSloop()

