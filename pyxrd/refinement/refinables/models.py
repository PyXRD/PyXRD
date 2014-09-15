# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from mvc.models.properties import FloatProperty, BoolProperty

from pyxrd.generic.models.base import PyXRDModel
from pyxrd.generic.io import storables, Storable
from pyxrd.generic.utils import not_none

@storables.register()
class RefinementInfo(PyXRDModel, Storable):
    """
        A model that is used to store the refinement information for each
        refinable value (in other models): minimum and maximum value and
        a flag to indicate whether this value is selected for refinement.
    """

    # MODEL INTEL:
    class Meta(PyXRDModel.Meta, Storable.Meta):
        store_id = "RefinementInfo"

    minimum = FloatProperty(default=0.0, text="Minimum", persistent=True)
    maximum = FloatProperty(default=1.0, text="Maximum", persistent=True)
    refine = BoolProperty(default=False, text="Refine", persistent=True)

    def __init__(self, minimum, maximum, refine, *args, **kwargs):
        """
            Valid *positional* arguments for a RefinementInfo are:
                refine: whether or not the linked parameter is selected for refinement
                minimum: the minimum allowable value for the linked parameter
                maximum: the maximum allowable value for the linked parameter   
        """
        super(RefinementInfo, self).__init__()
        self.refine = refine
        self.minimum = not_none(minimum, 0.0)
        self.maximum = not_none(maximum, 1.0)

    def to_json(self):
        return self.json_properties()

    def json_properties(self):
        return [self.minimum, self.maximum, self.refine]

    pass # end of class
