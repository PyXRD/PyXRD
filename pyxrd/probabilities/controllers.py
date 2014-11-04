# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from mvc import Controller

from pyxrd.generic.controllers import BaseController

from pyxrd.probabilities.views import get_correct_probability_views
from pyxrd.probabilities.models import RGbounds

def get_correct_probability_controllers(probability, parent_controller, independents_view, dependents_view):
    if probability is not None:
        G = probability.G
        R = probability.R
        if (RGbounds[R, G - 1] > 0):
            return BaseController(model=probability, parent=parent_controller, view=independents_view), \
                   MatrixController(current=R, model=probability, parent=parent_controller, view=dependents_view)
        else:
            raise ValueError, "Cannot (yet) handle R%d for %d layer structures!" % (R, G)

class EditProbabilitiesController(BaseController):

    independents_view = None
    matrix_view = None
    auto_adapt = False

    def __init__(self, *args, **kwargs):
        BaseController.__init__(self, *args, **kwargs)
        self._init_views(kwargs["view"])
        self.update_views()

    def _init_views(self, view):
        self.independents_view, self.dependents_view = get_correct_probability_views(self.model, view)
        self.independents_controller, self.dependents_controller = get_correct_probability_controllers(self.model, self, self.independents_view, self.dependents_view)
        view.set_views(self.independents_view, self.dependents_view)

    @BaseController.model.setter
    def model(self, model):
        if self.view is not None:
            self.independents_controller.model = None # model
            self.dependents_controller.model = None # model
        super(EditProbabilitiesController, self)._set_model(model)
        if self.view is not None:
            self.independents_controller.model = model
            self.dependents_controller.model = model
            self.update_views()

    def update_views(self): # needs to be called whenever an independent value changes
        with self.model.data_changed.hold():
            self.dependents_view.update_matrices(self.model)
            self.independents_view.update_matrices(self.model)

    def register_adapters(self):
        return

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("data_changed", signal=True)
    def notif_updated(self, model, prop_name, info):
        self.update_views()
        return

    pass # end of class

class MatrixController(BaseController):
    auto_adapt = False

    def __init__(self, current, *args, **kwargs):
        BaseController.__init__(self, *args, **kwargs)
        self.current_W = current
        self.current_P = current

    def register_adapters(self):
        return

    def on_w_prev_clicked(self, widget, *args):
        self.current_W = self.view.show_w_matrix(self.current_W - 1)
    def on_w_next_clicked(self, widget, *args):
        self.current_W = self.view.show_w_matrix(self.current_W + 1)

    def on_p_prev_clicked(self, widget, *args):
        self.current_P = self.view.show_p_matrix(self.current_P - 1)
    def on_p_next_clicked(self, widget, *args):
        self.current_P = self.view.show_p_matrix(self.current_P + 1)

    pass # end of class
