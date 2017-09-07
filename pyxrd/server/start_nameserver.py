#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

# Keep these:
import settings
import Pyro4
import Pyro4.naming

if __name__ == "__main__":
    
    from pyxrd.logs import setup_logging
    setup_logging(basic=True, prefix="PYRO NAMESERVER:")
    
    Pyro4.naming.startNSloop()
