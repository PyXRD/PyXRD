# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from mvc.models.properties import FloatProperty

class ProbabilityProperty(FloatProperty):
    """
     A descriptor that will invoke the 'update' method on the instance
     it belongs to.
    """

    def __init__(self, clamp=False, **kwargs):
        super(ProbabilityProperty, self).__init__(**kwargs)

    def __set__(self, instance, value):
        super(ProbabilityProperty, self).__set__(instance, value)
        instance.update()

    pass # end of class
