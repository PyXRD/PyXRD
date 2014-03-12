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

class RefineContext(ChildModel):
    """
        A context model for the refinement procedure.
        Enables to keep track of the initial state, the current state and
        the best state found so far (a state being a combination of a 
        solution and its residual).
        Also loads the properties to be refined once, together with their
        ranges and initial values.
    """
    class Meta(ChildModel.Meta):
        properties = [ # TODO add labels
            PropIntel(name="solution_added"),
            PropIntel(name="status", column=True, data_type=str, has_widget=False),
            PropIntel(name="status_message", column=True, data_type=str, has_widget=False),
            PropIntel(name="initial_residual", column=True, data_type=float, has_widget=True, widget_type='label'),
            PropIntel(name="last_residual", column=True, data_type=float, has_widget=True, widget_type='label'),
            PropIntel(name="best_residual", column=True, data_type=float, has_widget=True, widget_type='label'),
        ]

    mixture = property(ChildModel.parent.fget, ChildModel.parent.fset)

    # SIGNALS:
    solution_added = None

    # OTHER:
    # objective_function = None
    options = None

    initial_solution = None
    initial_residual = None

    last_solution = None
    last_residual = None

    best_solution = None
    best_residual = None

    ref_props = None
    values = None
    ranges = None

    status = "not initialized"
    status_message = ""

    record_header = None
    records = None

    def __init__(self, parent=None, store=False, options={}):
        super(RefineContext, self).__init__(parent=parent)
        self.options = options

        logger.info("Creating RefineContext with the following refinables:")

        if parent is not None:
            self.ref_props = []
            self.values = []
            self.ranges = ()
            for node in parent.refinables.iter_children():
                ref_prop = node.object
                if ref_prop.refine and ref_prop.refinable:
                    logger.info("\t%s from %r" % (ref_prop.title, ref_prop.obj))
                    self.ref_props.append(ref_prop)
                    self.values.append(ref_prop.value)
                    self.ranges += ((ref_prop.value_min, ref_prop.value_max),)



        if store: self.store_project_state()

        self.initial_residual = self.mixture.optimizer.get_current_residual()
        self.initial_solution = np.array(self.values, dtype=float)

        self.best_solution = self.initial_solution
        self.best_residual = self.initial_residual

        self.last_solution = self.initial_solution
        self.last_residual = self.initial_residual

        self.solution_added = Signal()

        self.status = "created"

    def store_project_state(self):
        # Create this once, this is rather costly
        # Any multithreaded/processed function that needs the project state
        # can then reload the project and get the correct mixture, setup
        # this context again... etc.
        # Only do this for the main process though, otherwise memory usage will
        # go through the roof.
        self.project = self.mixture.project
        self.project_dump = self.project.dump_object(zipped=True).getvalue()
        self.mixture_index = self.project.mixtures.index(self.mixture)

    def apply_solution(self, solution):
        solution = np.asanyarray(solution)
        with self.mixture.needs_update.hold():
            with self.mixture.data_changed.hold():
                for i, ref_prop in enumerate(self.ref_props):
                    if not (solution.shape == ()):
                        ref_prop.value = float(solution[i])
                    else:
                        ref_prop.value = float(solution[()])

    def get_data_object_for_solution(self, solution):
        with self.mixture.needs_update.ignore():
            with self.mixture.data_changed.ignore():
                self.apply_solution(solution)
                return deepcopy(self.mixture.data_object)

    def get_residual_for_solution(self, solution):
        self.apply_solution(solution)
        return self.mixture.optimizer.get_optimized_residual()

    def update(self, solution, residual=None):
        residual = residual if residual is not None else self.get_residual_for_solution(solution)
        self.last_solution = solution
        self.last_residual = residual
        if self.best_residual == None or self.best_residual > self.last_residual:
            self.best_residual = self.last_residual
            self.best_solution = self.last_solution
        self.solution_added.emit(arg=(self.last_solution, self.last_residual))

    def apply_best_solution(self):
        self.apply_solution(self.best_solution)

    def apply_last_solution(self):
        self.apply_solution(self.last_solution)

    def apply_initial_solution(self):
        self.apply_solution(self.initial_solution)

    def record_state_data(self, state_data):
        keys, record = zip(*state_data)
        if self.record_header == None:
            self.record_header = keys
            self.records = []
        self.records.append(record)

    pass # end of class

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

    refine_lock = False
    def refine(self, stop, **kwargs):
        """
            This refines the selected properties using the selected algorithm.
            This should be run asynchronously to keep the GUI from blocking.
        """
        assert self.context is not None, "You need to setup the RefineContext before starting the refinement!"

        if not self.refine_lock: # TODO use a proper lock
            # Set lock
            self.refine_lock = True

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
                            if stop.is_set():
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

            # Unlock this method
            self.refine_lock = False

            # Return the context to whatever called this
            return self.context

    pass # end of class
