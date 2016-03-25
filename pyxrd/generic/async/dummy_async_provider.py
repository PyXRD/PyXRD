#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon

from .dummy_async_server import DummyAsyncServer

class DummyAsyncServerProvider(object):
    
    _server = DummyAsyncServer()
    
    @classmethod
    def get_server(cls):
        return cls._server
    
    @classmethod
    def launch_server(cls):
        if cls._server is None:
            cls._server = DummyAsyncServer()
        
    @classmethod
    def stop_server(cls):
        cls._server.shutdown()
        del cls._server
        
    pass #end of class