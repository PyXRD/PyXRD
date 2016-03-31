# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import numpy as np

from refine_history import RefineHistory
from refine_status import RefineStatus

class RefineSetupError(ValueError):
    """ Raised if an error exists in the refinement setup """
    pass

class Refiner(object):
    """
        A model for the refinement procedure.
    """
    
    method = None
    
    history = None
    status = None

    refinables = None

    def __init__(self, method, residual_callback, data_callback, refinables, event_cmgr):
        super(Refiner, self).__init__()
        
        assert method is not None, "Cannot refine without a refinement method!"
        assert callable(residual_callback), "Cannot refine without a residual callback!"
        assert callable(data_callback), "Cannot refine without a data callback!"
        assert refinables is not None, "Cannot refine without refinables!"
        assert event_cmgr is not None, "Cannot refine without an event context manager!"
        
        # Set these:
        self.method = method
        self.residual_callback = residual_callback
        self.data_callback = data_callback
        self.event_cmgr = event_cmgr

        # Create the refinement history object:
        logger.info("Setting up the refinement history.") 
        self.history = RefineHistory()

        # Create the refinement status object:
        logger.info("Setting up the refinement status object.")        
        self.status = RefineStatus(self.history)

        # Setup the refinable property list:
        logger.info("Refinement with the following refinables:")
        self.refinables = []
        self.ranges = ()
        self.labels = ()
        initial_values = []
        for node in refinables.iter_children():
            refinable = node.object
            if refinable.refine and refinable.refinable:
                logger.info(" - %s from %r" % (refinable.text_title, refinable.obj))
                self.refinables.append(refinable)
                initial_values.append(refinable.value)
                if not (refinable.value_min < refinable.value_max):
                    logger.info("Error in refinement setup!")
                    self.status.error = True
                    self.status.message = "Invalid parameter range for '%s'!" % (refinable.get_descriptor(),)
                    raise RefineSetupError, "Invalid parameter range for '%s'!" % (refinable.get_descriptor(),)
                self.ranges += ((refinable.value_min, refinable.value_max),)
                self.labels += ((refinable.text_title, refinable.title),)

        # Make sure we can refine something:
        if len(self.refinables) == 0:
            logger.error("No refinables selected!")
            self.status.error = True
            self.status.message = "No parameters selected!"
            raise RefineSetupError, "No parameters selected!"      

        # Register the initial solution:
        initial_solution = np.array(initial_values, dtype=float)
        self.history.set_initial_solution(
            initial_solution,
            self.get_residual(initial_solution)
        )

    def apply_solution(self, solution):
        """
            Applies the given solution
        """
        solution = np.asanyarray(solution)
        with self.event_cmgr.hold():
            for i, ref_prop in enumerate(self.refinables):
                if not (solution.shape == ()):
                    ref_prop.value = float(solution[i])
                else:
                    ref_prop.value = float(solution[()])

    def get_data_object(self, solution):
        """
            Gets the mixture data object after setting the given solution
        """
        with self.event_cmgr.ignore():
            self.apply_solution(solution)
            return self.data_callback()
        
    def get_residual(self, solution):
        """
            Gets the residual for the given solution after setting it
        """
        return self.residual_callback(self.get_data_object(solution))

    def update(self, solution, residual=None, iteration=0):
        """
            Update's the refinement contect with the given solution:
                - applies the solution & gets the residual if not given
                - stores it in the history
        """
        residual = residual if residual is not None else self.get_residual(solution)
        self.history.register_solution(iteration, solution, residual)

    def apply_best_solution(self):
        self.apply_solution(self.history.best_solution)

    def apply_last_solution(self):
        self.apply_solution(self.history.last_solution)

    def apply_initial_solution(self):
        self.apply_solution(self.history.initial_solution)
    
    def get_plot_samples(self):
        return self.history.samples[:,self.history.PLOT_SAMPLE_SELECTOR]
    
    def get_plot_labels(self):
        return [plot_label for plot_label, _ in self.labels] + ["Rp",]
    
    def refine(self, stop):       
        # Suppress updates:
        with self.event_cmgr.hold():
            # Make sure the stop signal is not set from a previous run:
            stop.clear()

            # Log some information:
            logger.info("-"*80)
            logger.info("Starting refinement with this setup:")
            msg_frm = "%22s: %s"
            logger.info(msg_frm % ("refinement method", self.method))
            logger.info(msg_frm % ("number of parameters", len(self.refinables)))

            # Run the refinement:
            with self.status:
                with self.history:
                    self.method(self, stop=stop)

            # Log some more information:
            logger.info('Total refinement took %0.3f ms' % self.status.get_total_time())
            logger.info('Best solution found was:')                
            for i, ref_prop in enumerate(self.refinables):
                logger.info("%25s: %f" % (
                    ref_prop.get_descriptor(), 
                    self.history.best_solution[i]
                ))
            logger.info("-"*80)
                
            # Return us to whatever called this
            return self
        
    pass # end of class
