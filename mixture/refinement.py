# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from generic.models import PyXRDMeta, PyXRDModel, PropIntel
from generic.io import Storable

class _RefinementBase(object):
    """
    Base class for `RefinementGroup` and `RefinementValue` mixins. It's 
    used to provide common functionality and a way to check for the kind of
    refinement class we're dealing with when building the refinement tree.
            
    .. attribute:: refine_title

        A string used as the title for the group in the refinement tree
        
    .. attribute:: is_refinable

        Wether or not this instance is refinable
        
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
        
    pass #end of class

class RefinementGroup(_RefinementBase):
    """
    Mixin for objects that are not refinable themselves,
    but have refinable properties. They are presented in the refinement
    tree using their title value.
    Subclasses should override refine_title to make it more descriptive.
    
    .. attribute:: children_refinable

        Wether or not the child properties of this group can be refinable.
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

class RefinementInfo(PyXRDModel, Storable):
    """
        A model that is used to store the refinement information for each
        refinable value (in other models): minimum and maximum value and
        a flag to indicate wether this value is selected for refinement.
    """

    #MODEL INTEL:
    __model_intel__ = [
        PropIntel(name="minimum",         data_type=float,  storable=True),
        PropIntel(name="maximum",         data_type=float,  storable=True),
        PropIntel(name="refine",          data_type=bool,   storable=True),
    ]

    ref_info_name = "%s_ref_info"

    minimum = None
    maximum = None
    refine = False
    
    def __init__(self, minimum=None, maximum=None, refine=False, **kwargs):
        PyXRDModel.__init__(self)
        Storable.__init__(self)
        self.refine = bool(refine)
        self.minimum = float(minimum) if minimum!=None else None
        self.maximum = float(maximum) if maximum!=None else None
        
    def to_json(self):
        return self.json_properties()
        
    def json_properties(self):
        return [self.minimum, self.maximum, self.refine]
        
    @classmethod
    def setup_ref_info(type, cls, name, bases, d, __model_intel__):
        #loop over the prop intels and add refinement info prop intels for
        #refinable scalars (floats and ints), their actual initialisation is
        #taken care of in the extract_ref_info and inject_ref_info methods
        ref_info_intels = list()
        for prop in __model_intel__:
            if prop.refinable and prop.data_type in (float, int):
                ref_info_name = RefinementInfo.ref_info_name % prop.name
                ref_info_intels.append(PropIntel(name=ref_info_name, data_type=object, storable=True))
                d[ref_info_name] = None
                setattr(cls, ref_info_name, None)
        __model_intel__.extend(ref_info_intels)
        
    @classmethod
    def get_ref_info(type, cls, args, kwargs):
        #loop over prop intels, find refinable scalars and if present,
        #extract any json data that was stored in the project file
        prop_infos = dict()        
        for prop_intel in cls.__model_intel__:
            if prop_intel.refinable and prop_intel.data_type in (float, int):          
                ref_info_name = RefinementInfo.ref_info_name % prop_intel.name            
                info_args = kwargs.pop(ref_info_name, None)
                if info_args:
                    prop_infos[ref_info_name] = RefinementInfo.from_json(*info_args)
                else:
                    prop_infos[ref_info_name] = RefinementInfo(minimum = prop_intel.minimum, maximum = prop_intel.maximum)
        return prop_infos
            
    @classmethod
    def set_ref_info(type, instance, prop_infos):
        for ref_info_name, ref_info in prop_infos.iteritems():
            setattr(instance, ref_info_name, ref_info)
        
    pass #end of class
    
RefinementInfo.register_storable()
PyXRDMeta.register_hook(
    RefinementInfo.setup_ref_info,
    RefinementInfo.get_ref_info,
    RefinementInfo.set_ref_info
)



