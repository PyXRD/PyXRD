#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import time, atexit, os
from traceback import print_exc

import logging
logger = logging.getLogger(__name__)

import Pyro4

from pyxrd.generic.async.exceptions import *
from pyxrd.data.appdirs import user_log_dir

import settings
from utils import start_script

class Pyro4AsyncServerProvider(object):
    """
        Provider for the Pyro4 PyXRD server
    """
    
    @classmethod
    def check_server_is_alive(cls):
        try:
            server = cls.get_server(auto_start=False)
            return server.loopCondition()
        except:
            logging.info("Pyro4 PyXRD server not (yet) running!")
            return False
    
    @classmethod
    def get_server(cls, auto_start=True):
        if auto_start: 
            cls.launch_server()
        try:
            return Pyro4.Proxy("PYRONAME:%s" % settings.PYRO_NAME)
        except any:
            print_exc()
            logging.error("Could not connect to Pyro4 PyXRD server.")
            raise ServerNotRunningException("Pyro4 PyXRD Server is not running!")
    
    @classmethod
    def launch_server(cls):
        if not cls.check_server_is_alive():
            log_file = os.path.join(user_log_dir('PyXRD'), 'server.log')
            start_script("run_server.py", auto_kill=not settings.KEEP_SERVER_ALIVE, log_file=log_file)
            ttl = 15
            delay = 0.2
            while not cls.check_server_is_alive():
                time.sleep(delay) # wait
                ttl -= 1
                if ttl == 0:
                    raise ServerStartTimeoutExcecption("Pyro4 PyXRD Server is not running!")
            logging.info("Pyro4 PyXRD server is running!")
            if not settings.KEEP_SERVER_ALIVE:
                atexit.register(cls.stop_server)
        
    @classmethod
    def stop_server(cls):
        try:
            server = cls.get_server(auto_start=False)
            server.shutdown()
        except:
            logging.error("Error when trying to shut down Pyro4 PyXRD server!")
            print_exc()
            raise ServerNotRunningException("Pyro4 PyXRD Server is not running!")
        
    pass #end of class