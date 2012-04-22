# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import settings
from gtkmvc.model import Model
    
class AppModel(Model):

    #MODEL INTEL:
    __observables__ = ( "current_project", "current_specimen", "current_specimens", "statistics_visible" )

    #PROPERTIES:
    current_project = None
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
        self.current_project = project
        self._statistics_visible = False
        
    pass #end of class
