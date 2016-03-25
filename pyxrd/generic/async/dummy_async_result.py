#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon

class DummyAsyncResult(object):
    """ A non-asynchronous dummy implementation of the AsyncResult object """
    def __init__(self, func):
        self.result = func()
        
    def get(self):
        return self.result
    
    pass #end of class