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

pool = None
pool_stop = None

def _close_pool():
    # Close the pool:
    global pool, pool_stop
    logging.info("Closing multiprocessing pool ...")
    if pool is not None:
        pool_stop.set()
        pool.close()
        pool.join()

def _worker_initializer(pool_stop, debug, *args):

    # Spoof command line arguments so settings are loaded with correct
    # debugging flag
    import sys
    if debug and not "-d" in sys.argv:
        sys.argv.insert(1, "-d")
    if not debug and "-d" in sys.argv:
        sys.argv.remove("-d")

    # Load settings
    from pyxrd.data import settings

    if settings.DEBUG:
        from pyxrd import stacktracer
        stacktracer.trace_start(
            "trace-worker-%s.html" % multiprocessing.current_process().name,
            interval=5, auto=True) # Set auto flag to always update file!
    logger.info("Worker process initialized, DEBUG=%s" % debug)

def _create_pool(force=False):
    global pool, pool_stop
    from pyxrd.data import settings

    if pool_stop is None: # First time this is called
        pool_stop = multiprocessing.Event()
        settings.FINALIZERS.append(_close_pool)

    if pool is None or force:
        pool_stop.clear()
        logger.warning("Creating pool, DEBUG=%s" % settings.DEBUG)
        pool = multiprocessing.Pool(initializer=_worker_initializer, initargs=(pool_stop, settings.DEBUG,))

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


