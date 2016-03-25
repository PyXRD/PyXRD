#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import sys, os
import logging
logger = logging.getLogger(__name__)

import multiprocessing

def _worker_initializer(pool_stop, debug, *args):
    # Spoof command line arguments so settings are loaded with correct
    # debugging flag
    if debug and not "-d" in sys.argv:
        sys.argv.insert(1, "-d")
    if not debug and "-d" in sys.argv:
        sys.argv.remove("-d")

    # Load settings
    from pyxrd.data import settings
    settings.initialize()

    if settings.DEBUG:
        from pyxrd import stacktracer
        stacktracer.trace_start(
            "trace-worker-%s.html" % multiprocessing.current_process().name,
            interval=5, auto=True) # Set auto flag to always update file!
    logger.info("Worker process initialized, DEBUG=%s" % debug)
    pass

class PyXRDServer(object):

    pool = None
    pool_stop = None

    running = True

    def loopCondition(self):
        return self.running

    def __init__(self):
        from pyxrd.data import settings
        settings.initialize()

        logger.warning("Creating pool, DEBUG=%s" % settings.DEBUG)

        self.pool_stop = multiprocessing.Event()
        self.pool_stop.clear()

        maxtasksperchild = 10 if 'nt' == os.name else None

        self.pool = multiprocessing.Pool(
            initializer=_worker_initializer,
            maxtasksperchild=maxtasksperchild,
            initargs=(
                self.pool_stop,
                settings.DEBUG,
            )
        )

        # register the shutdown
        settings.FINALIZERS.append(self.shutdown)

    def submit(self, func):
        """
            The callback 'func' will be submitted to a multiprocessing
            pool created by the server. The result object will be returned.
        """
        result = self.pool.apply_async(func)
        self._pyroDaemon.register(result)
        return result
    
    def submit_sync(self, func):
        """
            This will run the 'func' callback directly on the server process.
            Use this with care as it will block the server. 
            Can be used to pass in a full project refinement using the 
            pyxrd.calculations.run_refinement method.
        """
        result = func()
        self._pyroDaemon.register(result)
        return result

    def shutdown(self):
        """
            Shuts down the server.
        """
        # Close the pool:
        logging.info("Closing multiprocessing pool ...")
        if self.pool is not None:
            self.pool_stop.set()
            self.pool.close()
            self.pool.join()
        self.running = False

    pass #end of class
