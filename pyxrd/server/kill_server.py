#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from traceback import print_exc

import settings
import Pyro4

if __name__ == "__main__":
    try:
        server = Pyro4.Proxy("PYRONAME:%s" % settings.PYRO_NAME)
        server.shutdown()
    except:
        logging.error("Error when trying to shut down Pyro server!")
        print_exc()