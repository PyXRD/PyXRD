# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import multiprocessing

USING_SCOOP = False
try:
    from scoop import futures
    if futures._controller is None:
        raise ImportError, "SCOOP was not started properly."
    USING_SCOOP = True
except ImportError:
    logger.warning("Could not import SCOOP, falling back to multiprocessing pool!")

from pyxrd.data import settings

pool = None
pool_stop = None

def _close_pool():
    # Close the pool:
    global pool, pool_stop
    if pool is not None:
        logging.info("Closing multiprocessing pool ...")
        pool_stop.set()
        pool.close()
        pool.join()

def _worker_initializer(*args):
    from pyxrd.core import _apply_settings
    if settings.CACHE == "FILE":
        settings.CACHE = "FILE_FETCH_ONLY"
    _apply_settings(True, settings.DEBUG, False)
    logger.info("Worker process initialized")

def _create_pool(force=False):
    global pool, pool_stop

    if pool_stop is None: # First time this is called
        pool_stop = multiprocessing.Event()
        settings.FINALIZERS.append(_close_pool)

    if pool is None or force:
        pool_stop.clear()
        pool = multiprocessing.Pool(maxtasksperchild=100, initializer=_worker_initializer, initargs=(pool_stop,))

    return pool

def _restart_pool():
    global pool
    pool.terminate()
    _create_pool(True)

def get_pool():
    global USING_SCOOP
    if USING_SCOOP:
        return futures
    else:
        if not multiprocessing.current_process().daemon:
            return _create_pool()
        else:
            return None


