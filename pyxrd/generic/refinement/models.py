# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.gtkmvc.support.propintel import PropIntel

from pyxrd.generic.models.base import PyXRDModel
from pyxrd.generic.io import storables, Storable

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
        properties = [
            PropIntel(name="minimum", data_type=float, storable=True),
            PropIntel(name="maximum", data_type=float, storable=True),
            PropIntel(name="refine", data_type=bool, storable=True),
        ]

    @staticmethod
    def get_attribute_name(prop):
        return "%s_ref_info" % prop.name

    minimum = None
    maximum = None
    refine = False

    def __init__(self, minimum, maximum, refine, *args, **kwargs):
        """
            Valid *positional* arguments for a RefinementInfo are:
                refine: whether or not the linked parameter is selected for refinement
                minimum: the minimum allowable value for the linked parameter
                maximum: the maximum allowable value for the linked parameter   
        """
        super(RefinementInfo, self).__init__()
        self.refine = refine
        self.minimum = minimum
        self.maximum = maximum

    def to_json(self):
        return self.json_properties()

    def json_properties(self):
        return [self.minimum, self.maximum, self.refine]

    pass # end of class
