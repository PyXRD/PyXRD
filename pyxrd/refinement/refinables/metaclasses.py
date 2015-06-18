# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from mvc.models.metaclasses import ModelMeta
from .models import RefinementInfo

class PyXRDRefinableMeta(ModelMeta):
    """
        A metaclass for regular mvc Models with refinable properties.
    """

    # ------------------------------------------------------------
    #      Instance creation:
    # ------------------------------------------------------------
    def __call__(cls, *args, **kwargs):   # @NoSelf
        """
        Strips the refinement info data from the keyword argument dictionary,
        passes the stripped dictionary to create the actual class instance,
        creates the attributes on the instance and returns it.
        """
        # Pop & parse any refinement info keyword arguments that might be present:
        prop_infos = dict()
        for prop in cls.Meta.all_properties:
            if prop.refinable:
                ref_info_name = prop.get_refinement_info_name()
                info_args = kwargs.pop(ref_info_name, None)
                if info_args:
                    prop_infos[ref_info_name] = RefinementInfo.from_json(*info_args)
                else:
                    prop_infos[ref_info_name] = RefinementInfo(prop.minimum, prop.maximum, False)

        # Create the instance passing the stripped keyword arguments:
        instance = ModelMeta.__call__(cls, *args, **kwargs)

        # Set the refinement attributes on the newly created instance:
        for ref_info_name, ref_info in prop_infos.iteritems():
            setattr(instance, ref_info_name, ref_info)

        # Return the instance:
        return instance

    pass # end of class
