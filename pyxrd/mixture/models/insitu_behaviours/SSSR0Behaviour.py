# coding=UTF-8
# ex:ts=4:sw=4:et=on
#
# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import scipy.stats
from math import sqrt

from mvc.models.properties.float_properties import FloatProperty

from pyxrd.generic.io.custom_io import storables
from pyxrd.refinement.refinables.properties import RefinableMixin

from .insitu_behaviour import InSituBehaviour

BEHAVIOUR_CLASS = "SSSR0Behaviour"

@storables.register()
class SSSR0Behaviour(InSituBehaviour):
    """
    	Behaviour class for R0 Smectite with 3 components
    """

    # MODEL INTEL:
    class Meta(InSituBehaviour.Meta):
        store_id = "SSSR0Behaviour"
        concrete = True # indicates this can be instantiated and added in the UI

    cation_hydration_factor = FloatProperty(
        description="Related to the cation hydration enthalpy",
        default=0.54, text="Cation hydration factor",
        minimum=0.0, maximum=2.0,
        refinable=True, persistent=True, visible=True,
        mix_with=(RefinableMixin,)
    )
     
    min_swelling_layer_charge = FloatProperty(
        description="The minimum layer charge required for swelling",
        default=-0.1, text="Minimum swelling layer charge",
        minimum = -2, maximum=0,
        refinable=True, persistent=True, visible=True,
        mix_with=(RefinableMixin,)
    )
      
    layer_charge_mean = FloatProperty(
        description="The mean of the normal layer charge distribution",
        default=-0.4, text="Mean layer charge",
        minimum = -2, maximum=0,
        refinable=True, persistent=True, visible=True,
        mix_with=(RefinableMixin,)
    )

    layer_charge_stdev = FloatProperty(
        default=0.05, text="The standard deviation of the layer charges",
        minimum = 0.0001, maximum=0.75,
        refinable=True, persistent=True, visible=True,
        mix_with=(RefinableMixin,)
    )
        
    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        my_kwargs = self.pop_kwargs(kwargs,
            *[prop.label for prop in SSSR0Behaviour.Meta.get_local_persistent_properties()]
        )
        super(SSSR0Behaviour, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.data_changed.hold():
            self.cation_hydration_factor = self.get_kwarg(kwargs, self.cation_hydration_factor, "cation_hydration_factor")
            self.min_swelling_layer_charge = self.get_kwarg(kwargs, self.min_swelling_layer_charge, "min_swelling_layer_charge")
            self.layer_charge_mean = self.get_kwarg(kwargs, self.layer_charge_mean, "layer_charge_mean")
            self.layer_charge_stdev = self.get_kwarg(kwargs, self.layer_charge_stdev, "layer_charge_stdev")
            
        pass #end of constructor

            
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_layer_charge_distribution(self, mean = -0.4, stdev = 0.05):        
        distr = scipy.stats.norm(mean, stdev)
        return distr

    def get_layer_type_distribution(self, distr, boundaries):
        """
            Returns a 3-tuple with the % of layers having:
            0 layers of water
            1 layers of water
            2 layers of water
        """
        (B0to1, B1to2, B2to0) = boundaries
        cdfB0to1 = distr.cdf(B0to1) # Get # layers with B0to1 or smaller layer charge 
        cdfB1to2 = distr.cdf(B1to2) # Get # layers with B1to2 or smaller layer charge
        cdfB2to0 = distr.cdf(B2to0) # Get # layers with B2to0 or smaller layer charge
        total = distr.cdf(0)        # Get # layers with B2 or smaller layer charge
        # returns fraction of 0w, 1w and 2w layers:
        return (cdfB0to1+total-cdfB2to0)/total,(cdfB1to2-cdfB0to1)/total,(cdfB2to0-cdfB1to2)/total
        
    def get_layer_type_boundaries(self, RH):
        """
            Gets the layer type boundaries (expressed as layer charge)
            in function of RH (expressed as a fraction)
        """
        RH_step_size = (self.cation_hydration_factor*sqrt(RH))
        b2to0_RH_factor = self.min_swelling_layer_charge
        b1to2_RH_factor = b2to0_RH_factor - RH_step_size
        b0to1_RH_factor = b1to2_RH_factor - RH_step_size
        
        return b0to1_RH_factor, b1to2_RH_factor, b2to0_RH_factor
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def apply(self, phase, RH):
        super(SSSR0Behaviour, self).apply(phase)

        RH = RH / 100.
        
        print("Applying SSSR0Behaviour to %s" % phase, "For RH: %.2f" % RH)

        # Get layer charge coundaries for the given relative humidity
        boundaries = self.get_layer_type_boundaries(RH)
        
        print(" boundaries:", boundaries)

        # Get the layer charge distribution for the given phase
        lc_distr = self.get_layer_charge_distribution(self.layer_charge_mean, self.layer_charge_stdev)
        print(" lc_distr:", lc_distr)
        
        # Calculate the layer type distribution for the calculated boundaries and distribution
        W0, W1, W2 = self.get_layer_type_distribution(lc_distr, boundaries)
        print(" W0:", W0)
        print(" W1:", W1)
        print(" W2:", W2)
        
        # Set probability model factors:
        phase.probabilities.F0 = W2
        phase.probabilities.F1 = W1/(W1+W0)
        
        # TODO update d-spacings
                
    def is_compatible_with(self, phase):
        # TODO check names of components
        try:
            return (phase.R == 0 and phase.G == 3)
        except:
            return False   
        
    pass
