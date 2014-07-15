# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from copy import deepcopy
from traceback import print_exc
import logging
logger = logging.getLogger(__name__)

import time

import numpy as np

# from pyxrd.generic.utils import print_timing

from pyxrd.mvc import PropIntel, Signal
from pyxrd.generic.models import ChildModel
from .refine_context import RefineContext

class Refiner(ChildModel):
    """
        A simple model that plugs onto the Mixture model. It provides
        the functionality related to refinement of parameters.
    """
    mixture = property(ChildModel.parent.fget, ChildModel.parent.fset)

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def setup_context(self, store=False):
        """
            Creates a RefineContext object filled with parameters based on the
            current state of the Mixture object.
        """
        self.parent.setup_refine_options()
        self.context = RefineContext(
            parent=self.parent,
            options=self.parent.refine_options,
            store=store
        )

    def delete_context(self):
        """
            Removes the RefineContext
        """
        self.context = None

    def refine(self, stop, **kwargs):
        """
            This refines the selected properties using the selected algorithm.
            This should be run asynchronously to keep the GUI from blocking.
        """
        assert self.context is not None, "You need to setup the RefineContext before starting the refinement!"

        # Suppress updates:
        with self.mixture.needs_update.hold():
            with self.mixture.data_changed.hold():

                # If something has been selected: continue...
                if len(self.context.ref_props) > 0:
                    # Run until it ends or it raises an exception:
                    t1 = time.time()
                    try:
                        if stop is not None:
                            stop.clear()
                        print "Calling:", self.mixture.get_refinement_method()
                        self.mixture.get_refinement_method()(self.context, stop=stop)
                    except any as error:
                        error.args += ("Handling run-time error: %s" % error,)
                        print_exc()
                        self.context.status = "error"
                        self.context.status_message = "Error occurred..."
                    else:
                        if stop is not None and stop.is_set():
                            self.context.status = "stopped"
                            self.context.status_message = "Stopping ..."
                        else:
                            self.context.status = "finished"
                            self.context.status_message = "Finished"
                    t2 = time.time()
                    logger.info('%s took %0.3f ms' % ("Total refinement", (t2 - t1) * 1000.0))
                else: # nothing selected for refinement
                    self.context.status = "error"
                    self.context.status_message = "No parameters selected!"

            # Return the context to whatever called this
            return self.context

    pass # end of class
