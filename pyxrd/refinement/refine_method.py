# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from pyxrd.generic.async import Cancellable
from .refine_method_meta import RefineMethodMeta

class RefineMethod(Cancellable):
    """
        The `RefineMethod` class is the base class for refinement methods.
        Sub-classes will be registered in the metaclass.
    """

    __metaclass__ = RefineMethodMeta

    name = "Name of the algorithm"

    description = "A slightly longer explanation of algorithm"

    # The value of this index is important;
    # Some ranges are reserved to prevent immediate overlaps:
    #  - negative values should not be used (not enforced)
    #  - the range 0 - 999 is reserved for built-in methods
    #  - all other values can be used for third-party methods, it is up to the
    #    final user to check if they don't overlap. If these methods become
    #    a built-in method, they recieve a new index in the preserved range
    index = -1

    disabled = True

    def __call__(self, context, stop=None, **kwargs):

        self._stop = stop

        for arg in self.options:
            kwargs[arg] = kwargs.get(arg, context.options.get(arg, getattr(self, arg)))

        return self.run(context, **kwargs)

    def run(self, context, **kwargs):
        raise NotImplementedError, "The run method of RefineRun should be implemented by sub-classes..."

    pass #end of class
