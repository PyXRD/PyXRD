# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from math import isnan

from pyxrd.data import settings

from pyxrd.calculations.CSDS import calculate_distribution
from pyxrd.calculations.data_objects import CSDSData
from pyxrd.generic.models import DataModel
from pyxrd.generic.io import storables, Storable

from pyxrd.generic.refinement.mixins import RefinementGroup, RefinementValue
from pyxrd.generic.refinement.metaclasses import PyXRDRefinableMeta
from mvc import PropIntel


class _AbstractCSDSDistribution(DataModel, Storable):

    # MODEL INTEL:
    __metaclass__ = PyXRDRefinableMeta
    class Meta(DataModel.Meta):
        description = "Abstract CSDS distr."
        explanation = ""
        properties = [
            PropIntel(name="distrib", label="CSDS Distribution", data_type=object, is_column=True),
            PropIntel(name="inherited", label="Inherited", data_type=bool),
        ]

    phase = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:
    inherited = False

    _data_object = None
    @property
    def data_object(self):
        return self._data_object

    _distrib = None
    def get_distrib(self):
        if self._distrib == None:
            self.update_distribution()
        return self._distrib

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def update_distribution(self):
        raise NotImplementedError

    pass # end of class

class _LogNormalMixin(object):

    # PROPERTIES:
    def get_maximum(self): return self._data_object.maximum
    def get_minimum(self): return self._data_object.minimum

    def get_average(self): return self._data_object.average
    def set_average(self, value):
        # ignore fault values:
        try: value = float(value)
        except ValueError: return
        if isnan(value):
            value = self.average
        if value < 1.0:
            value = 1.0
        if value != self._data_object.average:
            with self.data_changed.hold_and_emit():
                self._data_object.average = value
                self._data_object.maximum = int(settings.LOG_NORMAL_MAX_CSDS_FACTOR * self.average)
                self._update_distribution()

    def get_alpha_scale(self): return self._data_object.alpha_scale
    def set_alpha_scale(self, value):
        try: value = float(value)
        except ValueError: return # ignore fault values
        if value != self._data_object.alpha_scale:
            with self.data_changed.hold_and_emit():
                self._data_object.alpha_scale = value
                self._update_distribution()

    def get_alpha_offset(self): return self._data_object.alpha_offset
    def set_alpha_offset(self, value):
        try: value = float(value)
        except ValueError: return # ignore fault values
        if value != self._data_object.alpha_offset:
            with self.data_changed.hold_and_emit():
                self._data_object.alpha_offset = value
                self._update_distribution()

    def get_beta_scale(self): return self._data_object.beta_scale
    def set_beta_scale(self, value):
        try: value = float(value)
        except ValueError: return # ignore fault values
        if value != self._data_object.beta_scale:
            with self.data_changed.hold_and_emit():
                self._data_object.beta_scale = value
                self._update_distribution()

    def get_beta_offset(self): return self._data_object.beta_offset
    def set_beta_offset(self, value):
        try: value = float(value)
        except ValueError: return # ignore fault values
        if value != self._data_object.beta_offset:
            with self.data_changed.hold_and_emit():
                self._data_object.beta_offset = value
                self._update_distribution()

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, average=10, alpha_scale=0.9485, alpha_offset=-0.0017,
            beta_scale=0.1032, beta_offset=0.0034, *args, **kwargs):

        super(_LogNormalMixin, self).__init__(*args, **kwargs)

        self._data_object = CSDSData()

        self._data_object.average = average
        self._data_object.maximum = int(settings.LOG_NORMAL_MAX_CSDS_FACTOR * average)
        self._data_object.minimum = 1
        self._data_object.alpha_scale = alpha_scale
        self._data_object.alpha_offset = alpha_offset
        self._data_object.beta_scale = beta_scale
        self._data_object.beta_offset = beta_offset

        self._update_distribution()

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def _update_distribution(self):
        self._distrib = calculate_distribution(self.data_object)

    pass # end of class

@storables.register()
class LogNormalCSDSDistribution(_LogNormalMixin, _AbstractCSDSDistribution, RefinementGroup):

    # MODEL INTEL:
    class Meta(_AbstractCSDSDistribution.Meta):
        description = "Generic log-normal CSDS distr. (Eberl et al. 1990)"
        properties = [
            PropIntel(name="maximum", label="Maximum CSDS", minimum=1, maximum=1000, is_column=True, data_type=float),
            PropIntel(name="minimum", label="Minimum CSDS", minimum=1, maximum=1000, is_column=True, data_type=float),
            PropIntel(name="average", label="Average CSDS", minimum=1, maximum=200, is_column=True, data_type=float, refinable=True, storable=True, has_widget=True),

            PropIntel(name="alpha_scale", label="α scale factor", minimum=0, maximum=10, is_column=True, data_type=float, refinable=True, storable=True, has_widget=True),
            PropIntel(name="alpha_offset", label="α offset factor", minimum=-5, maximum=5, is_column=True, data_type=float, refinable=True, storable=True, has_widget=True),
            PropIntel(name="beta_scale", label="β² scale factor", minimum=0, maximum=10, is_column=True, data_type=float, refinable=True, storable=True, has_widget=True),
            PropIntel(name="beta_offset", label="β² offset factor", minimum=-5, maximum=5, is_column=True, data_type=float, refinable=True, storable=True, has_widget=True),
        ]
        store_id = "LogNormalCSDSDistribution"

    # REFINEMENT GROUP IMPLEMENTATION:
    @property
    def refine_title(self):
        return "CSDS Distribution"

    @property
    def refine_descriptor_data(self):
        return dict(
            phase_name=self.phase.name,
            component_name="*"
        )

    pass # end of class

@storables.register()
class DritsCSDSDistribution(_LogNormalMixin, _AbstractCSDSDistribution, RefinementValue):

    # MODEL INTEL:
    class Meta(_AbstractCSDSDistribution.Meta):
        description = "Log-normal CSDS distr. (Drits et. al, 1997)"
        properties = [
            PropIntel(name="maximum", label="Maximum CSDS", minimum=1, maximum=1000, is_column=True, data_type=float),
            PropIntel(name="minimum", label="Minimum CSDS", minimum=1, maximum=1000, is_column=True, data_type=float),
            PropIntel(name="average", label="Average CSDS", minimum=1, maximum=200, is_column=True, data_type=float, refinable=True, storable=True, has_widget=True),

            PropIntel(name="alpha_scale", label="α scale factor", minimum=0, maximum=10, is_column=True, data_type=float),
            PropIntel(name="alpha_offset", label="α offset factor", minimum=-5, maximum=5, is_column=True, data_type=float),
            PropIntel(name="beta_scale", label="β² scale factor", minimum=0, maximum=10, is_column=True, data_type=float),
            PropIntel(name="beta_offset", label="β² offset factor", minimum=-5, maximum=5, is_column=True, data_type=float),
        ]
        store_id = "DritsCSDSDistribution"

    # PROPERTIES:
    def get_alpha_scale(self): return 0.9485
    set_alpha_scale_value = property() # delete this function

    def get_alpha_offset(self): return 0.017
    set_alpha_offset_value = property() # delete this function

    def get_beta_scale(self): return 0.1032
    set_beta_scale_value = property() # delete this function

    def get_beta_offset(self): return 0.0034
    set_beta_offset_value = property() # delete this function

    # REFINEMENT VALUE IMPLEMENTATION:
    @property
    def refine_title(self):
        return "Average CSDS"

    @property
    def refine_descriptor_data(self):
        return dict(
            phase_name=self.phase.name,
            component_name="*",
            property_name=self.refine_title
        )

    @property
    def refine_value(self):
        return self.average
    @refine_value.setter
    def refine_value(self, value):
        self.average = value

    @property
    def refine_info(self):
        return self.average_ref_info

    @property
    def is_refinable(self):
        return not self.inherited

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        for key in ["alpha_scale", "alpha_offset", "beta_scale", "beta_offset"]:
            kwargs.pop(key, None)
        super(DritsCSDSDistribution, self).__init__(*args, **kwargs)

    pass # end of class

CSDS_distribution_types = [
    LogNormalCSDSDistribution,
    DritsCSDSDistribution
]
