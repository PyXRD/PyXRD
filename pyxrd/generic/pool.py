# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from copy import deepcopy

def create_async(func, args_getter):
    def async(self, pool):       
        """
            This will return the corresponding AsyncResult object.
        """
        args = getattr(self, args_getter)
        if callable(args): args = args()
        args = deepcopy(args) #prevents mutables being changed before they're in the queue
        return pool.apply_async(func, args)
    return async
