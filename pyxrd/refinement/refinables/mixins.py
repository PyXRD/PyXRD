# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

class _RefinementBase(object):
    """
    Base class for `RefinementGroup` and `RefinementValue` mixins. It's 
    used to provide common functionality and a way to check for the kind of
    refinement class we're dealing with when building the refinement tree.
            
    .. attribute:: refine_title

        A string used as the title for the group in the refinement tree

    .. attribute:: refine_descriptor

        A longer title string which gives more information (phase, component, etc) 
        
    .. attribute:: is_refinable

        Whether or not this instance is refinable
        
    .. attribute:: refinables
        
        An iterable with the names of the refinable properties 
        
    .. attribute:: refine_value
    
        Mapper for the actual refinable value (if available). This should be
        overriden by deriving classes.
        
    """

    @property
    def refine_title(self):
        return "Refinement Base"

    @property
    def refine_descriptor_data(self):
        return dict()

    @property
    def is_refinable(self):
        return True

    @property
    def refinables(self):
        return []

    @property
    def refine_info(self):
        return None

    @property
    def refine_value(self):
        return None
    @refine_value.setter
    def refine_value(self, value):
        pass

    pass # end of class

class RefinementGroup(_RefinementBase):
    """
    Mixin for objects that are not refinable themselves,
    but have refinable properties. They are presented in the refinement
    tree using their title value.
    Subclasses should override refine_title to make it more descriptive.
    
    .. attribute:: children_refinable

        Whether or not the child properties of this group can be refinable.
        This should normally always be True, unless for example if the entire
        group of properties have a single inherit property.
    
    """

    @property
    def refine_title(self):
        return "Refinement Group"

    @property
    def is_refinable(self):
        return False

    @property
    def children_refinable(self):
        return True

    @property
    def refinables(self):
        return self.Meta.get_refinable_properties()

    pass # end of class

class RefinementValue(_RefinementBase):
    """
        Mixin for objects that hold a single refinable property. They are
        collapsed into one line in the refinement tree. 
        Subclasses should override both the refine_title property to make it
        more descriptive, and the refine_value property to return and set the
        correct (refinable) attribute.
    """

    @property
    def refine_title(self):
        return "Refinement Value"

    pass # end of class
