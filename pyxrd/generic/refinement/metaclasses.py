# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.gtkmvc.support.propintel import PropIntel
from pyxrd.generic.refinement.models import RefinementInfo
from pyxrd.gtkmvc.support.metaclasses import UUIDMeta


class PyXRDRefinableMeta(UUIDMeta):
    """
        A metaclass for models with refinable properties.
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
            if cls._is_refinable(prop):
                ref_info_name = RefinementInfo.get_attribute_name(prop)
                info_args = kwargs.pop(ref_info_name, None)
                if info_args:
                    prop_infos[ref_info_name] = RefinementInfo.from_json(*info_args)
                else:
                    prop_infos[ref_info_name] = RefinementInfo(prop.minimum, prop.maximum, False)

        # Create the instance passing the stripped keyword arguments:
        instance = UUIDMeta.__call__(cls, *args, **kwargs)

        # Set the refinement attributes on the newly created instance:
        for ref_info_name, ref_info in prop_infos.iteritems():
            setattr(instance, ref_info_name, ref_info)

        # Return the instance:
        return instance

    # ------------------------------------------------------------
    #      Other methods & functions:
    # ------------------------------------------------------------
    def _is_refinable(cls, prop):  # @NoSelf
        """Returns True if 'prop' is a representing a refinable property"""
        return prop.refinable and prop.data_type in (float, int)

    def expand_property(cls, prop, default, _dict):  # @NoSelf
        """Expands refinable properties (adds a RefinementInfo attribute)"""
        if cls._is_refinable(prop):
            # Get attribute name:
            attr_name = RefinementInfo.get_attribute_name(prop)
            # Create a new PropIntel and add the attribute:
            new_prop = PropIntel(name=attr_name, data_type=object, storable=True)
            cls.set_attribute(_dict, attr_name, None)
            # Yield the created PropIntel so the super class can handle it:
            return [new_prop, ]
        else:
            # Nothing special to do:
            return UUIDMeta.expand_property(cls, prop, default, _dict)

    pass # end of class
