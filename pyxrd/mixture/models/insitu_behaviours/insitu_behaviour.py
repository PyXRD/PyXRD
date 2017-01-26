# coding=UTF-8
# ex:ts=4:sw=4:et=on
#
# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from mvc.models.properties import StringProperty

from pyxrd.generic.io.custom_io import storables, Storable
from pyxrd.generic.models.base import DataModel

from pyxrd.refinement.refinables.mixins import RefinementGroup

@storables.register()
class InSituBehaviour(DataModel, RefinementGroup, Storable):
    """
        Interface class for coding in-situ behaviour scripts.
        Sub-classes should override or implement the methods below.
    """

    # MODEL INTEL:
    class Meta(DataModel.Meta):
        store_id = "InSituBehaviour" # Override this so it is a unique string
        concrete = False # Indicates this cannot be instantiated and added in the UI
        
    mixture = property(DataModel.parent.fget, DataModel.parent.fset)

    # REFINEMENT GROUP IMPLEMENTATION:
    @property
    def refine_title(self):
        return "In-situ behaviour"

    @property
    def refine_descriptor_data(self):
        return dict(
            phase_name=self.phase.refine_title,
            component_name="*"
        )

    #: The name of this Behaviour
    name = StringProperty(
        default="New Behaviour", text="Name",
        visible=True, persistent=True, tabular=True
    )
    
    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        my_kwargs = self.pop_kwargs(kwargs,
            *[prop.label for prop in InSituBehaviour.Meta.get_local_persistent_properties()]
        )
        super(InSituBehaviour, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.data_changed.hold():
            self.name = self.get_kwarg(kwargs, self.name, "name")
            
        pass #end of constructor
            
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def apply(self, phase):
        assert phase is not None, "Cannot apply on None"
        assert self.is_compatible_with(phase), "`%r` is not compatible with phase `%r`" % (self, phase)
                
    def is_compatible_with(self, phase):
        return False # sub classes need to override this 
               
    pass #end of class