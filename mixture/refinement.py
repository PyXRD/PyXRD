# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

class _RefinementBase(object):
    """
        Base class for `RefinementGroup` and `RefinementValue` mixins. It's 
        used to provide common functionailty and a way to check for the kind of
        refinement class we're dealing with when building the refinement tree.
    """
    
    @property
    def refine_title(self):
        return "Refinement Base"
        
    @property
    def is_refinable(self):
        return True
        
    @property 
    def refinables(self):
        return []
        
    @property
    def refine_value(self):
        return None
    @refine_value.setter
    def refine_value(self, value):
        pass
        
    pass #end of class

class RefinementGroup(_RefinementBase):
    """
        Mixin for objects that are not refinable themselves,
        but have refinable properties. They are presented in the refinement
        tree using their title value.
        Subclasses should override refine_title to make it more descriptive.
    """
    
    @property
    def refine_title(self):
        return "Refinement Group"
       
    @property 
    def is_refinable(self):
        return False
       
    @property 
    def refinables(self):
        return self.__refinables__
        
    pass #end of class
        
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
        
    pass #end of class
    
