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
    def check_nameserver_alive(cls):
        try:
            ns = Pyro4.naming.locateNS()
            ns.ping()
            return True
        except any:
            print_exc()
            return False
    
    @classmethod
    def check_server_is_listed(cls):
        try:
            ns = Pyro4.naming.locateNS()
            objects = ns.list()
            if settings.PYRO_NAME in objects:
                return True
            else:
                return False
        except any:
            print_exc()
            return False
    
    """
        Async Provider Implementation: 
    """
    @classmethod
    def get_status(cls):
        """ should return a three-tuple consisting of the status colour, label and a description:
            ("#FF0000", "Error", "Nameserver not running")
        """
        try:         
            if not cls.check_nameserver_alive():
                return ("#FFFF00", "Nameserver Error", "Pyro4 Nameserver not running")
        except:
            print_exc()
            return ("#FF0000", "Nameserver Exception", "Exception when checking if Pyro4 Nameserver is running")
        
        try:         
            if not cls.check_server_is_listed():
                return ("#FFFF00", "Nameserver Error", "Pyro4 PyXRD server not listed")
        except:
            print_exc()
            return ("#FF0000", "Nameserver Exception", "Exception when checking if Pyro4 PyXRD server is listed")
        
        try:         
            if not cls.check_server_is_alive():
                return ("#FFFF00", "PyXRD Server Error", "Cannot connect to Pyro4 PyXRD server")
        except:
            print_exc()
            return ("#FF0000", "PyXRD Server Exception", "Exception when connecting to Pyro4 PyXRD server")
                    
        return ("#00FF00", "Connected (Pyro4)", "Succesfully connected to Pyro4 PyXRD Server")
    
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