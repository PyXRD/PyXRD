#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os
import logging

def setup_logging(basic=False, prefix=None):
    """
        Setup logging module.
    """
    from pyxrd.data import settings

    # Whether PyXRD should spew out debug messages
    debug = settings.DEBUG
    # Filename used for storing the logged messages
    log_file = settings.LOG_FILENAME
    # Flag indicating if a full logger should be setup (False) or
    # if simple, sparse logging is enough (True)
    basic = not settings.GUI_MODE

    fmt = '%(name)s - %(levelname)s: %(message)s'
    if prefix is not None:
        fmt = prefix + " " + fmt 

    if log_file is not None and not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file))

    if not basic:
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename=log_file,
                            filemode='w')

        # Get root logger:
        logger = logging.getLogger()

        # Setup error stream:
        console = logging.StreamHandler()
        full = logging.Formatter(fmt)
        console.setFormatter(full)

        # Add console logger to the root logger:
        logger.addHandler(console)
    else:
        # Very basic output for the root object:
        logging.basicConfig(format=fmt)
