# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import settings
from gtkmvc.model import Model
    
class AppModel(Model):
    current_project = None
    current_filename = None
    
    _statistics_visible = None
    @Model.getter("statistics_visible")
    def get_statistics_visible(self, prop_name):
        return self._statistics_visible and (self._current_specimen != None) and (not settings.VIEW_MODE)
    @Model.setter("statistics_visible")
    def set_statistics_visible(self, prop_name, value):
        if self._current_specimen != None:
            self._statistics_visible = value
    
    _current_specimen = None
    @Model.getter("current_specimen")
    def get_current_specimen(self, prop_name):
        return self._current_specimen
    @Model.setter("current_specimen")
    def set_current_specimen(self, prop_name, value):
        self._current_specimen = value
    
    _current_specimens = None
    @Model.getter("current_specimens")
    def get_current_specimens(self, prop_name):
        return self._current_specimens
    @Model.setter("current_specimens")
    def set_current_specimens(self, prop_name, value):
        if value == None:
            value = []
        self._current_specimens = value
        if len(self._current_specimens) == 1:
            self._current_specimen = self._current_specimens[0]
        else:
            self._current_specimen = None
    
    @property
    def single_specimen_selected(self):
        return bool(self.current_specimen is not None or self.current_specimens == [])
    
    __observables__ = ( "current_project", "current_specimen", "current_specimens", "statistics_visible" )
    
    def __init__(self, project = None):
        Model.__init__(self)
        self.current_project = project
        self._statistics_visible = False
