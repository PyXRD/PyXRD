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
import Pyro4.naming

try:
    import threading as threading
except ImportError: 
    import dummy_threading as threading
    
try:
    from fastrlock.rlock import FastRLock as RLock
except ImportError:
    from threading import RLock

from pyxrd.generic.async.exceptions import *
from pyxrd.data.appdirs import user_log_dir

import settings
from utils import start_script
from status_thread import StatusThread

class Pyro4AsyncServerProvider(object):
    """
        Provider for the Pyro4 PyXRD server
    """
    
    _STATUS_NS_NOT_RUNNING = ("#FFFF00", "Nameserver Error", "Pyro4 Nameserver not running")
    _STATUS_ERR_NS_RUNNING = ("#FF0000", "Nameserver Exception", "Exception when checking if Pyro4 Nameserver is running")
    
    _STATUS_NS_NOT_LISTED = ("#FFFF00", "Nameserver Error", "Pyro4 PyXRD server not listed")
    _STATUS_ERR_NS_LISTED = ("#FF0000", "Nameserver Exception", "Exception when checking if Pyro4 PyXRD server is listed")
    
    _STATUS_NO_CONN_PYXRD_SERVER  = ("#FFFF00", "PyXRD Server Error", "Cannot connect to Pyro4 PyXRD server")
    _STATUS_ERR_CONN_PYXRD_SERVER = ("#FF0000", "PyXRD Server Exception", "Exception when connecting to Pyro4 PyXRD server")
    
    _STATUS_SUCCESS = ("#00FF00", "Connected (Pyro4)", "Succesfully connected to Pyro4 PyXRD Server")
    
    _updater = None
    
    status = _STATUS_NS_NOT_RUNNING
    status_lock = RLock()
    
    NS_CACHE_TIMEOUT = 30
    ns = None
    ns_ts = 0
    @classmethod
    def _locate_ns(cls):
        if cls.ns is None or time.time() - cls.ns_ts >= cls.NS_CACHE_TIMEOUT:
            cls.ns = Pyro4.naming.locateNS()
            cls.ns_ts = time.time()
        return cls.ns
    
    PROXY_CACHE_TIMEOUT = 30
    proxy = None
    proxy_ts = 0
    @classmethod
    def _get_proxy(cls):
        if cls.proxy is None or time.time() - cls.proxy_ts >= cls.PROXY_CACHE_TIMEOUT:
            if cls.proxy is None:
                cls.proxy = Pyro4.Proxy("PYRONAME:%s" % settings.PYRO_NAME)
            else:
                cls.proxy.pyroBind()
            cls.proxy_ts = time.time()
        return cls.proxy
    
    
    @classmethod
    def check_nameserver_alive(cls):
        try:
            ns = cls._locate_ns()
            ns.ping()
            return True
        except any:
            print_exc()
            return False
    
    @classmethod
    def check_server_is_listed(cls):
        try:
            ns = cls._locate_ns()
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
        """ 
            Should return a three-tuple consisting of the status colour, label and a description:
                ("#FF0000", "Error", "Nameserver not running")
            Status is updated periodically.
        """
        # first call:
        if cls._updater == None:
            cls._update_status(cls._get_status())
            cls._updater = StatusThread(5, cls)
            cls._updater.setDaemon(True)
            cls._updater.start()
        
        return cls.status
    
    @classmethod
    def _update_status(cls, status):
        with cls.status_lock:
            cls.status = status
    
    @classmethod
    def _get_status(cls):
        try:
            if not cls.check_nameserver_alive():
                return  cls._STATUS_NS_NOT_RUNNING
        except:
            print_exc()
            return cls._STATUS_ERR_NS_RUNNING
        try:         
            if not cls.check_server_is_listed():
                return cls._STATUS_NS_NOT_LISTED
        except:
            print_exc()
            return cls._STATUS_ERR_NS_LISTED
        try:         
            if not cls.check_server_is_alive():
                return cls._STATUS_NO_CONN_PYXRD_SERVER
        except:
            print_exc()
            return cls._STATUS_ERR_CONN_PYXRD_SERVER
        return cls._STATUS_SUCCESS
    
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
