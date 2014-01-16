# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.mvc import Signal, PropIntel

from pyxrd.generic.models import PyXRDModel

class AppModel(PyXRDModel):
    """
        Simple model that stores the state of the application window.
        Should never be made persistent.
        
        Attributes:
            needs_plot_update: a mvc.Signal to indicate the plot needs an
                update. This models listens for the 'needs_update' signal on the
                loaded project and propagates this accordingly.
            current_project: the currently loaded project
            statistics_visble: a boolean indicating whether or not statistic
                should be visible
            current_specimen: the currently selected specimen, is None if more
                than one specimen is selected.
            current_specimens: a list of currently selected specimens, is never
                None, even if only one specimen is selected.
            single_specimen_selected: a boolean indicating whether or not a
                single specimen is selected
            multiple_specimen_selected: a boolean indicating whether or not
                multiple specimen are selected
    """
    # MODEL INTEL:
    class Meta(PyXRDModel.Meta):
        properties = [
            PropIntel(name="current_project", observable=True),
            PropIntel(name="current_specimen", observable=True),
            PropIntel(name="current_specimens", observable=True),
            PropIntel(name="statistics_visible", observable=True),
            PropIntel(name="needs_plot_update", observable=True)
        ]

    # SIGNALS:
    needs_plot_update = None

    # PROPERTIES:
    _current_project = None
    def get_current_project(self):
        return self._current_project
    def set_current_project(self, value):
        if self._current_project is not None: self.relieve_model(self._current_project)
        self._current_project = value
        type(type(self)).object_pool.clear()
        if self._current_project is not None: self.observe_model(self._current_project)
        self.clear_selected()
        self.needs_plot_update.emit()
    current_filename = None

    _statistics_visible = None
    def set_statistics_visible(self, value): self._statistics_visible = value
    def get_statistics_visible(self):
        return self._statistics_visible and self.current_specimen is not None and self.current_project.layout_mode != 1

    _current_specimen = None
    def get_current_specimen(self): return self._current_specimen
    def set_current_specimen(self, value):
        self._current_specimens = [value]
        self._current_specimen = value

    _current_specimens = []
    def get_current_specimens(self): return self._current_specimens
    def set_current_specimens(self, value):
        if value == None:
            value = []
        self._current_specimens = value
        if len(self._current_specimens) == 1:
            self._current_specimen = self._current_specimens[0]
        else:
            self._current_specimen = None

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
        self.needs_plot_update = Signal()
        self.current_project = project
        self._statistics_visible = False

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @PyXRDModel.observe("data_changed", signal=True)
    @PyXRDModel.observe("visuals_changed", signal=True)
    def notify_needs_update(self, model, prop_name, info):
        self.needs_plot_update.emit()

    def clear_selected(self):
        self.current_specimens = None

    pass # end of class
