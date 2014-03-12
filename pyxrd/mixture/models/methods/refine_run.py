# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from pyxrd.generic.async import Cancellable

class RefineRun(Cancellable):
    name = "Name of the algorithm"
    description = "A slightly longer explenation of algorithm"
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
