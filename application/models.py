# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import settings
from gtkmvc.model import Model, Observer, Signal

from generic.metaclasses import pyxrd_object_pool
    
class AppModel(Model):

    #MODEL INTEL:
    __observables__ = ( 
        "current_project",
        "current_specimen",
        "current_specimens",
        "statistics_visible",
        "needs_plot_update",
    )

    #SIGNALS:
    needs_plot_update = None

    #PROPERTIES:
    _current_project = None
    def get_current_project_value(self):
        return self._current_project
    def set_current_project_value(self, value):
        if self._current_project != None: self.relieve_model(self._current_project)
        self._current_project = value
        pyxrd_object_pool.clear()
        if self._current_project != None: self.observe_model(self._current_project)
    current_filename = None
    
    current_specimen = None
    
    _statistics_visible = None
    def set_statistics_visible_value(self, value): self._statistics_visible = value
    def get_statistics_visible_value(self):
        return self._statistics_visible and (self.current_specimen != None) and (not settings.VIEW_MODE)
    
    _current_specimens = None
    def get_current_specimens_value(self): return self._current_specimens
    def set_current_specimens_value(self, value):
        if value == None:
            value = []
        self._current_specimens = value
        if len(self._current_specimens) == 1:
            self.current_specimen = self._current_specimens[0]
        else:
            self.current_specimen = None
    
    @property
    def single_specimen_selected(self):
        return bool(self.current_specimen is not None or self.current_specimens == [])
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, project = None):
        Model.__init__(self)
        self.needs_plot_update = Signal()
        self.current_project = project
        self._statistics_visible = False
        
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Observer.observe("needs_update", signal=True)
    def notify_needs_update(self, model, prop_name, info):
        self.needs_plot_update.emit()
        
    pass #end of class
