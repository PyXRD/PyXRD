# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from Queue import Empty
import multiprocessing

from scipy.optimize import fmin_l_bfgs_b

from .base_workers import PyXRDWorker, PyXRDWorkerMethod

class MixtureWorkerMethod(PyXRDWorkerMethod): 
    def __init__(self, mixture_index, *args):
        super(MixtureWorkerMethod, self).__init__(*args)
        self.mixture = self.project.mixtures.get_item_by_index(mixture_index)
        if not hasattr(self.mixture.refiner, "context") or self.mixture.refiner.context==None:
            self.mixture.update_refinement_treestore()
            self.mixture.refiner.setup_context()
        
    def clean(self):
        del self.mixture
        super(MixtureWorker.Method, self).clean()
                
    pass #end of class

class RefineWorkerMethod(MixtureWorkerMethod):         
    def __call__(self):
        try:
            key, (solution,) = self.job_queue.get(False, 0.05)
            residual = self.mixture.refiner.context.apply_solution(solution)
            self.result_queue.put((key, residual))
            self.job_queue.task_done()
        except Empty:
            pass #don't block, there might be other methods running on this process...                    
    pass #end of class

class ImproveWorkerMethod(MixtureWorkerMethod):         
    def __call__(self):
        try:
            key, (solution,) = self.job_queue.get(False, 0.05)
            vals = fmin_l_bfgs_b(
                self.mixture.refiner.context.apply_solution,
                solution,
                approx_grad=True,
                bounds=self.mixture.refiner.context.ranges,
                factr=1e18,
                pgtol=1e-02,
                epsilon=1e-05,
                maxiter=1
            )
            better, fitness = vals[0:2]
            self.result_queue.put((key, (better, fitness)))
            self.job_queue.task_done()                
        except Empty:
            pass #don't block, there might be other methods running on this process...   
    pass #end of class

class MixtureWorker(PyXRDWorker):

    Method = MixtureWorkerMethod

    def __init__(self, mixture, *args):
        super(MixtureWorker, self).__init__(*args)
        self.mixture_index = self.project.mixtures.index(mixture)
        
    def get_setup_args(self):
        #these are passed to the child Method class's __init__ function:
        return (self.mixture_index,) + super(MixtureWorker, self).get_setup_args()

    pass #end of class
    
class ImproveWorker(MixtureWorker):
    Method = ImproveWorkerMethod
    pass #end of class
    
class RefineWorker(MixtureWorker):
    Method = RefineWorkerMethod
    pass #end of class
