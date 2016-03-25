#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os

import Pyro4

from pyxrd.data.appdirs import user_log_dir

from pyxrd_server import PyXRDServer
from utils import start_script

import settings

if __name__ == "__main__":

    from pyxrd.logs import setup_logging
    setup_logging(basic=True, prefix="PYRO SERVER:")
    
    import logging
    logger = logging.getLogger(__name__)

    server = PyXRDServer()

    daemon = Pyro4.Daemon()

    try:
        ns = Pyro4.locateNS()
    except Pyro4.naming.NamingError:
        logger.info("NamingError encountered when trying to locate the nameserver")
        log_file = os.path.join(user_log_dir('PyXRD'), 'nameserver.log')
        start_script("start_nameserver.py", auto_kill=not settings.KEEP_SERVER_ALIVE, log_file=log_file)
        ns = Pyro4.locateNS()

    server_uri = daemon.register(server)
    ns.register(settings.PYRO_NAME, server_uri) # settings.PYRO_NAME)

    try:
        daemon.requestLoop(server.loopCondition)
    finally:
        daemon.shutdown()
