# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from pyxrd.generic.async import Cancellable

class MethodMeta(type):
    """
        The metaclass for creating a Method (sub)class
        Will register the class type so we can build a list of Method classes
        dynamically.
        If the (sub)class does not want to be registered, it should set
        the 'disabled' class attribute to True.
    """
    registered_methods = {}
    
    def __new__(meta, name, bases, class_dict):  # @NoSelf
        cls = type.__new__(meta, name, bases, class_dict)
        if not getattr(cls, 'disabled', False):
            meta.registered_methods[getattr(cls, 'index')] = cls
        return cls
    
    @classmethod
    def get_all_methods(meta):  # @NoSelf
        return meta.registered_methods

    pass #end of class

class RefineRun(Cancellable):
    """
        The `RefineRun` class is the base class for refinement methods.
        Sub-classes will be registered in the metaclass.
    """
    
    __metaclass__ = MethodMeta
    
    name = "Name of the algorithm"
    description = "A slightly longer explenation of algorithm"
    index = -1
    disabled = True 
    options = []

    """
        extra_options:
         list of tuples containing:
            ( option_name,         arg_name,    type,  default, range/choices )
        e.g.:
            ( 'Stagnation limit', 'stagnation', float, 0.0001, [10, 1E-12] )
            ( 'Flag',             'some_flag',  bool,  False,  [True, False] )
            ( 'Multi',            'some_multi', str,   'Default',  ['Default', 'Automatic', 'Manual'] )
    """

    def __call__(self, context, stop=None, **kwargs):

        self._stop = stop

        for _, arg, _, default, _ in self.options:
            kwargs[arg] = kwargs.get(arg, context.options.get(arg, default))

        return self.run(context, **kwargs)

    def run(self, context, **kwargs):
        raise NotImplementedError, "The run method of RefineRun should be implemented by sub-classes..."
    
    pass #end of class