# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from multiprocessing import TimeoutError

import logging
logger = logging.getLogger(__name__)

class Cancellable(object):
    """
        Object which has a (threaded) action that can be cancelled by the user.
    """
    _stop = None

    def _user_cancelled(self):
        return bool(self._stop is not None and self._stop.is_set())

    pass #end of class

# TODO part of this stuff should be merged with the pool module ?

class HasAsyncCalls(Cancellable):

    def submit_async_call(self, func):
        """ Utility that passes function calls either to SCOOP (if it's available)
        or down to a multiprocessing call."""
        from pyxrd.generic.pool import USING_SCOOP, get_pool
        pool = get_pool()
        if USING_SCOOP: # SCOOP
            result = pool.submit(func)
        elif pool is not None: # Regular multiprocessing pool
            result = pool.apply_async(func)
        else: # No parallelization:
            result = func()
        return result

    __can_time_out = False
    __async_get_fail_count = 0
    __async_get_raise_error = False

    def cancel_calls(self):
        self.__can_time_out = True

    def fetch_async_result(self, result):
        """ Utility that parses the result objects returned by submit_async_call"""
        from pyxrd.generic.pool import USING_SCOOP, get_pool
        pool = get_pool()
        if USING_SCOOP:  # SCOOP result object
            return result.result()
        elif pool is not None: # Multiprocessing pool result object
            async_get_fail_count = 0
            if self.__can_time_out:
                while True:
                    try:
                        return result.get(timeout=2)
                    except TimeoutError:
                        async_get_fail_count += 1
                        if async_get_fail_count > 50:
                            logging.error(
                                "AsyncResult.get() timed out 50 times" \
                                " after 2 seconds, something is blocking!")
                            if self.__async_get_raise_error:
                                raise
            else:
                return result.get()
        else: # No parallelization:
            return result

    def restart_pool(self):
        from pyxrd.generic.pool import USING_SCOOP
        if USING_SCOOP:
            pass #TODO
        else:
            try:
                from pyxrd.generic.pool import _restart_pool
                _restart_pool()
            except ImportError:
                pass # If we get here, we're not using a Multiprocessing pool

    pass #end of class


