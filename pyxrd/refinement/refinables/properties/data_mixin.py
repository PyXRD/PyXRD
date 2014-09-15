# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

class DataMixin(object):
    """
    Mixing for the ~:class:`mvc.models.properties.LabeledProperty` descriptor
    that allows this property to be set on the `data_object` object of the
    instance this property belongs to, instead of a private attribute.
    
    When this Mixin is used, the user can pass an additional keyword 
    argument to the descriptor:
        - data_object_label: the private attribute label for the data object,
          defaults to '_data_object' 
    """

    data_object_label = "_data_object"

    def _get_private_label(self):
        """ Private attribute label (holds the actual value on the model) """
        return "%s.%s" % (
            self.data_object_label,
            self.label
        )

    pass