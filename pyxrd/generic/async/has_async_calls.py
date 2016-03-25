# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from .providers import get_provider
from .exceptions import *
from .dummy_async_server import DummyAsyncServer

class HasAsyncCalls(object):
    """
        Class providing utility functions for async calls
    """
    
    def submit_async_call(self, func):
        """ Utility that passes function calls down to the async server """
        try:
            self._async_server = get_provider().get_server()
        except (ServerNotRunningException, ServerStartTimeoutExcecption):
            logger.warning("Could not get the default provided async server, using dummy implementation")
            self._async_server = DummyAsyncServer()
        return self._async_server.submit(func)
        

    def fetch_async_result(self, result):
        """ Utility that parses the result objects returned by submit_async_call"""
        return result.get()

    pass #end of class