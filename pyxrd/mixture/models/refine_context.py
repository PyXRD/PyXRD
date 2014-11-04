# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import cPickle as pickle

import logging
logger = logging.getLogger(__name__)

import numpy as np

from mvc import PropIntel, Signal
from pyxrd.generic.models import ChildModel

class RefineSetupError(ValueError):
    """ Raised if an error exists in the refinement setup """
    pass

class RefineContext(ChildModel):
    """
        A context model for the refinement procedure.
        Enables to keep track of the initial state, the current state and
        the best state found so far (a state being a tuple of a solution and
        its residual).
        Also loads the properties to be refined once, together with their
        ranges and initial values and the refinement options.
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
                    logger.info(" - %s from %r" % (ref_prop.text_title, ref_prop.obj))
                    self.ref_props.append(ref_prop)
                    self.values.append(ref_prop.value)
                    if not (ref_prop.value_min < ref_prop.value_max):
                        logger.info("Error in refinement setup!")
                        raise RefineSetupError, "Refinable property `%s` needs a valid range!" % (ref_prop.get_descriptor(),)
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

    def get_uniform_solutions(self, num):
        """
            Returns `num` solutions (uniformly distributed within their ranges) 
            for the selected parameters.
        """
        start_solutions = np.random.random_sample((num, len(self.ref_props)))
        ranges = np.asarray(self.ranges, dtype=float)
        return ranges[:, 0] + start_solutions * (ranges[:, 1] - ranges[:, 0])

    def set_initial_solution(self, solution):
        """
            Re-sets the initial solutions to a given solution array 
        """
        self.initial_solution = np.array(solution, dtype=float)
        self.apply_solution(self.initial_solution)
        self.initial_residual = self.mixture.optimizer.get_current_residual()

        self.best_solution = self.initial_solution
        self.best_residual = self.initial_residual

        self.last_solution = self.initial_solution
        self.last_residual = self.initial_residual

    def apply_solution(self, solution):
        """
            Applies the given solution
        """
        solution = np.asanyarray(solution)
        with self.mixture.needs_update.hold():
            with self.mixture.data_changed.hold():
                for i, ref_prop in enumerate(self.ref_props):
                    if not (solution.shape == ()):
                        ref_prop.value = float(solution[i])
                    else:
                        ref_prop.value = float(solution[()])

    def get_data_object_for_solution(self, solution):
        """
            Gets the mixture data object after setting the given solution
        """
        with self.mixture.needs_update.ignore():
            with self.mixture.data_changed.ignore():
                self.apply_solution(solution)
                return pickle.dumps(self.mixture.data_object)

    def get_pickled_data_object_for_solution(self, solution):
        """
            Gets the mixture data object after setting the given solution
        """
        with self.mixture.needs_update.ignore():
            with self.mixture.data_changed.ignore():
                self.apply_solution(solution)
                return pickle.dumps(
                    self.mixture.data_object,
                    protocol=pickle.HIGHEST_PROTOCOL
                )

    def get_residual_for_solution(self, solution):
        """
            Gets the residual for the given solution after setting it
        """
        self.apply_solution(solution)
        return self.mixture.optimizer.get_optimized_residual()

    def update(self, solution, residual=None):
        """
            Update's the refinement contect with the given solution:
                - applies the solution & gets the residual if not given
                - stores it as the `last_solution`
                - checks if this solution is better then the current best solution,
                  and if so, stores it as such
                - emits the `solution_added` signal for any part interested
                
            This function and it's signal can be used to record a refinement
            history. This function only stores the initial, the best and the
            latest solution. The record_state_data can be used to store a record
            of the refinement.
        """
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
