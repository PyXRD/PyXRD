# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.


from pyxrd.generic.models.metaclasses import PyXRDMeta
from pyxrd.generic.models.properties import PropIntel
from pyxrd.generic.utils import get_unique_list

from pyxrd.generic.refinement.models import RefinementInfo

class PyXRDRefinableMeta(PyXRDMeta):
    """
        A metaclass for models with refinable properties.
    """

    extra_key_names = PyXRDMeta.extra_key_names + [
        "refinables",
    ]

    # ------------------------------------------------------------
    #      Type initialisation:
    # ------------------------------------------------------------
    def __init__(cls, name, bases, d): # @NoSelf
        # get the model intel for this class type (excluding bases):
        model_intel = get_unique_list(d.get("__model_intel__", list()))

        ref_info_intels = list()
        for prop in model_intel:
            if prop.refinable and prop.data_type in (float, int):
                ref_info_name = RefinementInfo.ref_info_name % prop.name
                ref_info_intels.append(PropIntel(name=ref_info_name, data_type=object, storable=True))
                d[ref_info_name] = None
                setattr(cls, ref_info_name, None)

        model_intel.extend(ref_info_intels)

        d["__model_intel__"] = model_intel

        return PyXRDMeta.__init__(cls, name, bases, d)

    # ------------------------------------------------------------
    #      Instance creation:
    # ------------------------------------------------------------
    def __call__(cls, *args, **kwargs):   # @NoSelf
        # Pop & parse any refinement info keyword arguments that might be present:
        prop_infos = dict()
        for prop_intel in cls.__model_intel__:
            if prop_intel.refinable and prop_intel.data_type in (float, int):
                ref_info_name = RefinementInfo.ref_info_name % prop_intel.name
                info_args = kwargs.pop(ref_info_name, None)
                if info_args:
                    prop_infos[ref_info_name] = RefinementInfo.from_json(*info_args)
                else:
                    prop_infos[ref_info_name] = RefinementInfo(minimum=prop_intel.minimum, maximum=prop_intel.maximum)

        # Create the instance passing the stripped keyword arguments:
        instance = PyXRDMeta.__call__(cls, *args, **kwargs)

        # Set the refinement attributes on the instance
        for ref_info_name, ref_info in prop_infos.iteritems():
            setattr(instance, ref_info_name, ref_info)

        # Return our instance:
        return instance

    # ------------------------------------------------------------
    #      Other methods & functions:
    # ------------------------------------------------------------
    def __generate_refinables__(cls, name, bases, d, prop): # @NoSelf
        if prop.refinable: d["__refinables__"].append(prop.name)
        return name, bases, d


    pass # end of class
