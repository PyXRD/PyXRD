# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.mvc.models.properties import LabeledProperty

class ProbabilityProperty(LabeledProperty):
    """
     A descriptor that will invoke the 'update' method on the instance
     it belongs to.
     Can optionally clamp numeric values to a minimum and maximum.
    """

    def __init__(self, clamp=False, minimum=0.0, maximum=1.0, cast_to=None, **kwargs):
        super(ProbabilityProperty, self).__init__(**kwargs)
        self.cast_to = cast_to
        self.clamp = clamp
        self.minimum = minimum
        self.maximum = maximum

    def __set__(self, instance, value):
        if self.clamp:
            value = min(max(value, self.minimum), self.maximum)
        if self.cast_to is not None:
            value = self.cast_to(value)
        if getattr(instance, self.label) != value:
            super(ProbabilityProperty, self).__set__(instance, value)
            instance.update()

    pass # end of class
