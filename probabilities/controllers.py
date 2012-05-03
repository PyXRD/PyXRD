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


def get_correct_probability_controllers(probability, parent_controller, independents_view, dependents_view):
    if probability!=None:
        G = probability.G
        R = probability.R
        if R == 0 or G == 1:
            return R0R1IndependentsController(model=probability, parent=parent_controller, view=independents_view), \
                   R0R1MatrixController(N=G, model=probability, parent=parent_controller, view=dependents_view)
        elif G > 1:
            if R == 1: #------------------------- R1:
                if G == 2:
                    return R0R1IndependentsController(model=probability, parent=parent_controller, view=independents_view), \
                           R0R1MatrixController(N=G, model=probability, parent=parent_controller, view=dependents_view)
                elif G == 3:
                    return R0R1IndependentsController(model=probability, parent=parent_controller, view=independents_view), \
                           R0R1MatrixController(N=G, model=probability, parent=parent_controller, view=dependents_view)
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
        self._init_views(kwargs["view"])
        self.update_views()
        
    def _init_views(self, view):
        self.independents_view, self.dependents_view = get_correct_probability_views(self.model, view)
        self.independents_controller, self.dependents_controller = get_correct_probability_controllers(self.model, self, self.independents_view, self.dependents_view)
        view.set_views(self.independents_view, self.dependents_view)

    def update_views(self): #needs to be called whenever an independent value changes
        self.dependents_view.update_matrices(self.model.get_distribution_matrix(), self.model.get_probability_matrix())
        self.independents_view.update_matrices(self.model)
        
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("updated", signal=True)
    def notif_updated(self, model, prop_name, info):
        self.update_views()
        return
        
        
        
    pass #end of class
    
class R0R1IndependentsController(ChildController):

    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name in ["parent", "added", "removed", "updated"]:
                    pass
                elif name in self.model.__refineables__:
                    FloatEntryValidator(self.view["prob_%s" % name])
                    self.adapt(name)
                else:
                    print name
                    #FloatEntryValidator(self.view["prob_%s" % name])
                    #self.adapt(name)
            return

    pass #TODO
    
"""class R1G2IndependentsController(ChildController):

    def register_adapters(self):
        print "R1G2IndependentsController.register_adapters()"
        if self.model is not None:
            for name in self.model.get_properties():
                if name in ["parent", "added", "removed", "updated"]:
                    pass
                else:
                    print name
                    FloatEntryValidator(self.view["prob_%s" % name])
                    self.adapt(name)
            return

    pass #TODO
    
class R1G3IndependentsController(ChildController):

    def __init__(self, *args, **kwargs):
        ChildController.__init__(self, *args, **kwargs)

    pass #TODO"""
    
class R0R1MatrixController(ChildController):

    def __init__(self,  N=1, *args, **kwargs):
        ChildController.__init__(self, *args, **kwargs)

    pass #TODO
