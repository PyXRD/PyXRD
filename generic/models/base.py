# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from warnings import warn

from gtkmvc.model_mt import ModelMT
from gtkmvc.model import Signal

from metaclasses import PyXRDMeta, pyxrd_object_pool
from properties import PropIntel

class PyXRDModel(ModelMT):
    """
       Standard model for PyXRD models, with support for refinable properties.
    """
    
    __metaclass__ = PyXRDMeta
    __model_intel__ = [
        PropIntel(name="uuid", data_type=str,  storable=True, observable=False),
    ]
    
    
    def get_depr(self, fun_kwargs, default, *keywords):
        """
        Can be used to check if any deprecated keywords are passed to a 
        function, and if not, return a default value. Additionally warns the 
        user about the fact that he is using a deprecated keyword.
        If more then one deprecated keyword argument is present, the value of
        the last keword as passed to this function is passed.
        By default, deprecated arguments should be ignored if a non-deprecated
        one is passed as well.
        
        *fun_kwargs* the keyword arguments as passed to the function
        
        *default* the default value if no deprecated arguments are present
        
        **keywords* the deprecated keywords
        
        :rtype: the retrieved value or the default one as explained above
        """
        if len(keywords) < 1:
            raise AttributeError, "get_depr() requires at least one alias (%d given)" % (len(keywords))
        
        value = default
        for key in keywords:
            if key in fun_kwargs:
                value = fun_kwargs[key]
                warn("The use of the keyword '%s' is deprecated for %s!" % (key, type(self)), DeprecationWarning)
        return value
    
    __uuid__ = None
    @property
    def uuid(self): 
        return self.__uuid__
    @uuid.setter
    def uuid(self, value):
        pyxrd_object_pool.remove_object(self)        
        self.__uuid__ = value
        pyxrd_object_pool.add_object(self)        
    
    def __init__(self, *args, **kwargs):
        ModelMT.__init__(self, *args, **kwargs)
        self.__stored_uuids__ = list()
               
    def get_prop_intel_by_name(self, name):
        for prop in self.__model_intel__:
            if prop.name == name:
                return prop
                
    def get_base_value(self, attr):
        intel = self.get_prop_intel_by_name(attr)
        if intel.inh_name!=None:
            return getattr(self, "_%s" % attr)
        else:
            return getattr(self, attr)
                
    pass # end of class
    
class ChildModel(PyXRDModel):

    #MODEL INTEL:
    __parent_alias__ = None
    __model_intel__ = [
        PropIntel(name="parent",  data_type=object),
        PropIntel(name="removed", data_type=object),
        PropIntel(name="added",   data_type=object),
    ]

    #SIGNALS:
    removed = None
    added = None

    #PROPERTIES:
    _parent = None
    def get_parent_value(self): return self._parent
    def set_parent_value(self, value):
        if value!=self._parent:
            self._unattach_parent()
            self._parent = value
            self._attach_parent()

    def __init__(self, parent=None):
        PyXRDModel.__init__(self)
        self.removed = Signal()
        self.added = Signal()

        if self.__parent_alias__ != None:
            setattr(self.__class__, self.__parent_alias__, property(lambda self: self.parent))         
        self.parent = parent

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------       
    def _unattach_parent(self):
        if self.parent != None:
            self.removed.emit()
    
    def _attach_parent(self):
        if self.parent != None:
            self.added.emit()
            
    pass #end of class
