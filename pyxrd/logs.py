#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os
import queue
import logging
from logging.handlers import QueueHandler, QueueListener

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
        # Setup file log:
        file_handler = logging.FileHandler(log_file, 'w')
        disk_fmt = logging.Formatter(
            '%(asctime)s %(levelname)-8s %(name)-40s %(message)s',
            datefmt='%m-%d %H:%M')
        file_handler.setFormatter(disk_fmt)

        # Setup console log:
        log_handler = logging.StreamHandler()
        full = logging.Formatter(fmt)
        log_handler.setFormatter(full)

        # Setup queue handler:
        log_que = queue.Queue(-1)
        queue_handler = QueueHandler(log_que)
        queue_listener = QueueListener(log_que, file_handler, log_handler, respect_handler_level=True)
        queue_listener.start()
        
        # Add queue handler:
        logger = logging.getLogger('')
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
        logger.addHandler(queue_handler)
    else:
        # Very basic output for the root object:
        logging.basicConfig(format=fmt)
        logger = logging.getLogger('')
        logger.addHandler(queue_handler)
        
    settings.FINALIZERS.append(queue_listener.stop)
