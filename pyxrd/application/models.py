# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import hashlib

from pyxrd.generic.models import PyXRDModel
from pyxrd.generic.io.json_codec import PyXRDEncoder

from mvc.models.properties.signal_property import SignalProperty
from mvc.models.properties.labeled_property import LabeledProperty

class AppModel(PyXRDModel):
    """
        Simple model that stores the state of the application window.
        Should never be made persistent.
        
        Attributes:
            needs_plot_update: a mvc.Signal to indicate the plot needs an
                update. This models listens for the 'needs_update' signal on the
                loaded project and propagates this accordingly.
            current_project: the currently loaded project
            current_specimen: the currently selected specimen, is None if more
                than one specimen is selected.
            current_specimens: a list of currently selected specimens, is never
                None, even if only one specimen is selected.
            single_specimen_selected: a boolean indicating whether or not a
                single specimen is selected
            multiple_specimen_selected: a boolean indicating whether or not
                multiple specimen are selected
    """

    # SIGNALS:
    needs_plot_update = SignalProperty()

    # PROPERTIES:
    current_project = LabeledProperty(default=None, text="Current project")
    
    @current_project.setter
    def current_project(self, value):
        _current_project = type(self).current_project._get(self)
        if _current_project is not None: 
            self.relieve_model(_current_project)
            self._project_hash = None
        _current_project = value
        type(self).current_project._set(self, value)
        type(type(self)).object_pool.clear()
        if _current_project is not None: self.observe_model(_current_project)
        self.clear_selected()
        self.needs_plot_update.emit()

    @property
    def current_filename(self):
        return self.current_project.filename if self.current_project else None

    current_specimen = LabeledProperty(default=None, text="Current specimen")
    @current_specimen.setter
    def current_specimen(self, value):
        type(self).current_specimens._set(self, [value])
        type(self).current_specimen._set(self, value)

    current_specimens = LabeledProperty(default=[], text="Current specimens")
    @current_specimens.setter
    def current_specimens(self, value):
        if value == None:
            value = []
        type(self).current_specimens._set(self, value)
        if len(self._current_specimens) == 1:
            type(self).current_specimen._set(self, self._current_specimens[0])
        else:
            type(self).current_specimen._set(self, None)

    @property
    def project_loaded(self):
        return self.current_project is not None

    @property
    def specimen_selected(self):
        return self.current_specimen is not None

    @property
    def single_specimen_selected(self):
        return self.specimen_selected and len(self.current_specimens) == 1

    @property
    def multiple_specimens_selected(self):
        return len(self.current_specimens) > 1

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, project=None):
        """ Initializes the AppModel with the given Project. """
        super(AppModel, self).__init__()
        self.current_project = project
        if project: project.parent = self

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @PyXRDModel.observe("data_changed", signal=True)
    @PyXRDModel.observe("visuals_changed", signal=True)
    def notify_needs_update(self, model, prop_name, info):
        self.needs_plot_update.emit()

    def clear_selected(self):
        self.current_specimens = None

    # ------------------------------------------------------------
    #      Project change management:
    # ------------------------------------------------------------
    _project_hash = None
    def update_project_last_save_hash(self):
        if self.current_project is not None:
            dump = PyXRDEncoder.dump_object(self.current_project).encode(errors='ignore')
            self._project_hash = hashlib.sha224(dump).hexdigest()
    def check_for_changes(self):
        current_hash = None
        if self.current_project is not None:
            dump = PyXRDEncoder.dump_object(self.current_project).encode(errors='ignore')
            current_hash = hashlib.sha224(dump).hexdigest()
        return current_hash != self._project_hash

    pass # end of class
