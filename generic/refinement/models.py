# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from generic.models.base import PyXRDModel
from generic.models.properties import PropIntel
from generic.io import storables, Storable

@storables.register()
class RefinementInfo(PyXRDModel, Storable):
    """
        A model that is used to store the refinement information for each
        refinable value (in other models): minimum and maximum value and
        a flag to indicate wether this value is selected for refinement.
    """

    #MODEL INTEL:
    __model_intel__ = [
        PropIntel(name="minimum",         data_type=float,  storable=True),
        PropIntel(name="maximum",         data_type=float,  storable=True),
        PropIntel(name="refine",          data_type=bool,   storable=True),
    ]

    ref_info_name = "%s_ref_info"

    minimum = None
    maximum = None
    refine = False
    
    def __init__(self, minimum=None, maximum=None, refine=False, **kwargs):
        PyXRDModel.__init__(self)
        Storable.__init__(self)
        self.refine = bool(refine)
        self.minimum = float(minimum) if minimum!=None else None
        self.maximum = float(maximum) if maximum!=None else None
        
    def to_json(self):
        return self.json_properties()
        
    def json_properties(self):
        return [self.minimum, self.maximum, self.refine]
              
    pass #end of class   
