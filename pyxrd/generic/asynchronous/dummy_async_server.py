#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon

from .dummy_async_result import DummyAsyncResult

class DummyAsyncServer(object):
    """ A non-asynchronous dummy implementation of the AsyncServer object """
    
    def loopCondition(self):
        return True

    def submit(self, func):
        return DummyAsyncResult(func)

    def shutdown(self):
        pass
    
    pass #end of class