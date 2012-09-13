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
from generic.controllers import BaseController

from probabilities.views import EditProbabilitiesView, get_correct_probability_views
from probabilities.models import RGbounds

def get_correct_probability_controllers(probability, parent_controller, independents_view, dependents_view):
    if probability!=None:
        G = probability.G
        R = probability.R
        rank = probability.rank
        if (RGbounds[R,G-1] > 0):
            return IndependentsController(model=probability, parent=parent_controller, view=independents_view), \
                   MatrixController(current=R, model=probability, parent=parent_controller, view=dependents_view)
        else:
            raise ValueError, "Cannot (yet) handle R%d for %d layer structures!" % (R, G)

class EditProbabilitiesController(BaseController):

    independents_view = None
    matrix_view = None

    def __init__(self, *args, **kwargs):
        BaseController.__init__(self, *args, **kwargs)
        self._init_views(kwargs["view"])
        self.update_views()
        
    def _init_views(self, view):
        self.independents_view, self.dependents_view = get_correct_probability_views(self.model, view)
        self.independents_controller, self.dependents_controller = get_correct_probability_controllers(self.model, self, self.independents_view, self.dependents_view)
        view.set_views(self.independents_view, self.dependents_view)

    def update_views(self): #needs to be called whenever an independent value changes
        self.dependents_view.update_matrices(self.model)
        self.independents_view.update_matrices(self.model)
        
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("updated", signal=True)
    def notif_updated(self, model, prop_name, info):
        self.update_views()
        return

    pass #end of class
    
class IndependentsController(BaseController):
    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name in self.model.__have_no_widget__:
                    pass
                elif name in self.model.__refinables__:
                    #FloatEntryValidator(self.view["prob_%s" % name])
                    self.adapt(name)
                else:
                    pass
            return
    pass #end of class
  
class MatrixController(BaseController):
    def __init__(self, current, *args, **kwargs):
        BaseController.__init__(self, *args, **kwargs)
        self.current_W = current
        self.current_P = current

    def on_w_prev_clicked(self, widget, *args):
        self.current_W = self.view.show_w_matrix(self.current_W - 1)
    def on_w_next_clicked(self, widget, *args):
        self.current_W = self.view.show_w_matrix(self.current_W + 1)

    def on_p_prev_clicked(self, widget, *args):
        self.current_P = self.view.show_p_matrix(self.current_P - 1)
    def on_p_next_clicked(self, widget, *args):
        self.current_P = self.view.show_p_matrix(self.current_P + 1)

    pass #end of class
