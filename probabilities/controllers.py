# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import locale

import gtk

from gtkmvc import Model, Controller
from gtkmvc.adapters import Adapter

from generic.validators import FloatEntryValidator 
from generic.views import ChildObjectListStoreView
from generic.controllers import ChildController

from probabilities.views import EditProbabilitiesView, get_correct_probability_views


def get_correct_probability_controllers(phase, parent_controller, independents_view, dependents_view):
    if phase!=None:
        G = phase.data_G
        R = phase.data_R
        if R == 0 or G == 1:
            return R0IndependentsController(N=G, model=phase.probabibilites, parent=parent_controller, view=independents_view), \
                   R0R1MatrixController(N=G, model=phase.probabibilites, parent=parent_controller, view=dependents_view)
        elif G > 1:
            if R == 1: #------------------------- R1:
                if G == 2:
                    return R1G2IndependentsController(model=phase.probabibilites, parent=parent_controller, view=independents_view), \
                           R0R1MatrixController(N=G, model=phase.probabibilites, parent=parent_controller, view=dependents_view)
                elif G == 3:
                    return R1G3IndependentsController(model=phase.probabibilites, parent=parent_controller, view=independents_view), \
                           R0R1MatrixController(N=G, model=phase.probabibilites, parent=parent_controller, view=dependents_view)
                elif G == 4:
                    raise ValueError, "Cannot yet handle R1 g=4" # ,R0R1MatrixView(N=G, parent=parent_view)
            elif R == 2: #----------------------- R2:
                if G == 2:
                    raise ValueError, "Cannot yet handle R2 g=2"
                elif G == 3:
                    raise ValueError, "Cannot yet handle R2 g=3"
                elif G == 4:
                    raise ValueError, "Cannot yet handle R2 g=4"            
            elif R == 3: #----------------------- R3:
                if G == 2:
                    raise ValueError, "Cannot yet handle R3 g=2"
                elif G == 3:
                    raise ValueError, "Cannot yet handle R3 g=3"
                elif G == 4:
                    raise ValueError, "Cannot yet handle R3 g=4"
            else:
                raise ValueError, "Cannot (yet) handle Reichweite's other then 0, 1, 2 or 3"

class EditProbabilitiesController(ChildController):

    independents_view = None
    matrix_view = None

    def __init__(self, *args, **kwargs):
        ChildController.__init__(self, *args, **kwargs)
               
        self._init_views()
        self.update_views()
        
    def _init_views(self):
        self.independents_view, self.dependents_view = get_correct_probability_views(self.model, self.view)
        self.independents_controller, self.dependents_controller = get_correct_probability_controllers(self.model, self, self.independents_view, self.dependents_view)
        self.view.set_independents_view(self.independents_view)
        self.view.set_dependents_view(self.dependents_view)

    def update_views(self): #needs to be called whenever an independent value changes
        #self.independents_view.update()
        self.matrix_view.update_matrices(self.model.get_distribution_matrix(), self.model.get_probability_matrix())

    pass
    
class R0IndependentsController(ChildController):

    def __init__(self, N=1, **kwargs):
        ChildController.__init__(self, **kwargs)

    pass #TODO
    
class R1G2IndependentsController(ChildController):

    def __init__(self, *args, **kwargs):
        ChildController.__init__(self, *args, **kwargs)

    pass #TODO
    
class R1G3IndependentsController(ChildController):

    def __init__(self, *args, **kwargs):
        ChildController.__init__(self, *args, **kwargs)

    pass #TODO
    
class R0R1MatrixController(ChildController):

    def __init__(self,  N=1, *args, **kwargs):
        ChildController.__init__(self, *args, **kwargs)

    pass #TODO
