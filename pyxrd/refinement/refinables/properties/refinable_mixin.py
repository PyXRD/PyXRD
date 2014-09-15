# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

class RefinableMixin(object):
    """
    Mixing for the ~:class:`mvc.models.properties.LabeledProperty` descriptor
    that allows the property to be refinable.
    When this Mixin is used, the user should pass 4 additional keyword 
    arguments to the descriptor:
        - refinable: boolean set to True if the property is refinable
        - refinable_info_format: the format for the refinement info attribute
        - minimum: the minimum allowed value (or None as default)
        - maximum: the maximum allowed value (or None as default) 
    """

    refinable = True
    refinable_info_format = "%(label)s_ref_info"

    minimum = None
    maximum = None

    def get_refinement_info_name(self):
        return self.refinable_info_format % { 'label': self.label }

    pass #end of class