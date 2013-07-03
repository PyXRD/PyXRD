# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from traceback import format_exc
import multiprocessing

import time

import numpy as np
import scipy

from gtkmvc import Signal
from generic.utils import print_timing
from generic.models import ChildModel, PropIntel

import settings

from .genetics import RefineGeneticsRun, RefineHybridRun
from .scipy_runs import RefineLBFGSBRun, RefineBasinHoppingRun

if settings.MULTI_USE_PROCESSES:
    from .custom_brute import RefineBruteForceRun
else:
    from .scipy_runs import RefineBruteForceRun

class RefineContext(ChildModel):
    """
        A context model for the refinement procedure.
        Enables to keep track of the initial state, the current state and
        the best state found so far (a state being a combination of a 
        solution and its residual).
        Also loads the properties to be refined once, together with their
        ranges and initial values.
    """
    __parent_alias__ = "mixture"
    
    __model_intel__ = [ #TODO add labels
        PropIntel(name="solution_added"),
        PropIntel(name="status",               column=True, data_type=str,   has_widget=False),
        PropIntel(name="initial_residual",     column=True, data_type=float, has_widget=True),
        PropIntel(name="last_residual",        column=True, data_type=float, has_widget=True),
        PropIntel(name="best_residual",        column=True, data_type=float, has_widget=True),        
    ]
    
    #SIGNALS:
    solution_added = None
    
    #OTHER:
    objective_function = None
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

    record_header = None
    records = None
    
    def __init__(self, parent=None, options={}):
        super(RefineContext, self).__init__(parent=parent)
        self.options = options
                
        if parent!=None:
            self.ref_props = []
            self.values = []
            self.ranges = ()
            for ref_prop in parent.refinables.iter_objects():
                if ref_prop.refine and ref_prop.refinable:
                    self.ref_props.append(ref_prop)
                    self.values.append(ref_prop.value)
                    self.ranges += ((ref_prop.value_min, ref_prop.value_max),)
            
        self.initial_residual = self.mixture.optimizer.get_current_residual()
        self.initial_solution = np.array(self.values, dtype=float)    

        self.best_solution = self.initial_solution
        self.best_residual = self.initial_residual
        
        self.last_solution = self.initial_solution
        self.last_residual = self.initial_residual
            
        self.solution_added = Signal()
            
        self.status = "created"

    def apply_solution(self, solution):
        solution = np.asanyarray(solution)
        for i, ref_prop in enumerate(self.ref_props):
            if not (solution.shape==()):
                ref_prop.value = solution[i]
            else:
                ref_prop.value = solution[()]
        residual = self.mixture.optimizer.optimize(silent=True)
        return residual

    def update(self, solution):
        self.dry_update(solution, self.apply_solution(solution))
            
    def dry_update(self, solution, residual):
        self.last_solution = solution
        self.last_residual = residual
        if self.best_residual==None or self.best_residual > self.last_residual:
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
                    
    pass #end of class

class Refiner(ChildModel):
    """
        A simple model that plugs onto the Mixture model. It provides
        the functionality related to refinement of parameters.
    """
    __parent_alias__ = "mixture"
    
    refine_methods = {
        0: RefineLBFGSBRun(),
        1: RefineGeneticsRun(),
        2: RefineBruteForceRun(),
        3: RefineHybridRun(),
        4: RefineBasinHoppingRun(),
    }

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    def setup_context(self):
        """
            Creates a RefineContext object filled with parameters based on the
            current state of the Mixture object.
        """
        self.parent.setup_refine_options()
        self.context = RefineContext(
            parent=self.parent,
            options=self.parent.refine_options
        )
        
    def delete_context(self):
        """
            Removes the RefineContext
        """
        self.context = None

    refine_lock = False
    def refine(self, params):
        """
            This refines the selected properties using the selected algorithm.
            This should be run asynchronously to keep the GUI from blocking.
        """
        assert self.context!=None, "You need to setup the RefineContext before starting the refinement!"
        
        if not self.refine_lock:
            # Set lock
            self.refine_lock = True            
        
            # Suppres updates:
            self.mixture.project.freeze_updates()
              
            # If something has been selected: continue...                      
            if len(self.context.ref_props) > 0:               
                # The objective function:
                # needs to be declared inline as it needs acces to the params
                # dict.
                # FIXME this doesn't actually get called in multiprocessing mode
                # for some refiners... we should always leave this to the refiners??
                # and do some house-holding code to make them thread-process-friendly?
                def get_residual_from_solution(solution):
                    if not (params["kill"] or params["stop"]):
                        self.context.update(solution)
                        time.sleep(0.01) #What's this?
                        return self.context.last_residual
                    elif params["kill"]:
                        raise GeneratorExit
                    elif params["stop"]:
                        raise StopIteration
                self.context.best_residual, self.context.best_solution = None, None
                self.context.objective_function = get_residual_from_solution
                
                self.context.run_params = params
                
                #Run until it ends or it raises an exception:
                t1 = time.time()
                try:
                    self.mixture.get_refine_method()(self.context)
                except StopIteration:
                    self.context.last_solution, self.context.last_residual = self.context.best_solution, self.context.best_residual
                    self.context.status = "stopped"
                except GeneratorExit:
                    pass #no action needed
                except any as error:
                    print "Handling run-time error: %s" % error
                    print format_exc()
                    self.context.status = "error"
                self.context.status = "finished"
                t2 = time.time()
                print '%s took %0.3f ms' % ("Total refinement", (t2-t1)*1000.0)
            else: #nothing selected for refinement
                self.context.status = "error"          
                
            #Unluck the GUI & this method
            self.refine_lock = False
            self.mixture.project.thaw_updates()
               
            #Return the context to whatever called this
            return self.context

    pass #end of class
