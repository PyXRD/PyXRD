# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from gtkmvc.model import Model, Observer, Signal

from generic.models import ChildModel, PropIntel
from generic.models.metaclasses import pyxrd_object_pool
from generic.models.mixins import ObjectListStoreChildMixin
from generic.io import storables, Storable

from atoms.models import Atom
from generic.refinement.mixins import RefinementGroup, RefinementValue

from gtk import ListStore

class ComponentPropMixin(object):
    """
        A mixin which provides some common utility functions for retrieving
        properties using a string description (e.g. 'layer_atoms.1' or 'b_cell')
    """

    def _parseattr(self, attr):
        """
            Function used for handling (deprecated) 'property strings':
            attr contains a string (e.g. cell_a or layer_atoms.2) which can be 
            parsed into an object and a property
        """
        if attr=="" or attr==None:
            return None
        
        attr = attr.replace("data_", "", 1) #for backwards compatibility
        attrs = attr.split(".")
        if attrs[0] == "layer_atoms":
            return self.component._layer_atoms._model_data[int(attrs[1])], "pn"
        elif attrs[0] == "interlayer_atoms":
            return self.component._interlayer_atoms._model_data[int(attrs[1])], "pn"
        else:
            return self.component, attr

@storables.register()
class AtomRelation(ChildModel, Storable, ObjectListStoreChildMixin, ComponentPropMixin, RefinementValue):

    #MODEL INTEL:
    __parent_alias__ = "component"
    __model_intel__ = [
        PropIntel(name="name",    label="Name",    data_type=unicode,   is_column=True,  storable=True,  has_widget=True),
        PropIntel(name="value",   label="Value",   data_type=float,     is_column=True,  storable=True,  has_widget=True, widget_type='float_input', refinable=True),
        PropIntel(name="enabled", label="Enabled", data_type=bool,      is_column=True,  storable=True,  has_widget=True),
        
        PropIntel(name="changed", data_type=object),
    ]
    __store_id__ = "AtomRelation"
    allowed_relations = {}

    #SIGNALS:
    changed = None

    #PROPERTIES:
    _value = 0.0
    def get_value_value(self): return self._value
    def set_value_value(self, value):
        self._value = value
        self.changed.emit()
        self.liststore_item_changed()
        
    _name = ""
    def get_name_value(self): return self._name
    def set_name_value(self, value):
        self._name = value
        self.liststore_item_changed()
    
    _enabled = False
    def get_enabled_value(self): return self._enabled
    def set_enabled_value(self, value):
        self._enabled = value
        self.changed.emit()        
    
    @property
    def applicable(self):
        """
        Is true when this AtomRelations was passed a component of which the atom
        ratios are not set to be inherited from another component.
        """
        return (self.parent!=None and not self.parent.inherit_atom_relations)
    
    #REFINEMENT VALUE IMPLEMENTATION:
    @property
    def refine_title(self):
        return self.name

    @property
    def refine_value(self):
        return self.value
    @refine_value.setter
    def refine_value(self, value):
        self.value = value
        
    @property 
    def is_refinable(self):
        return self.enabled

    @property
    def refine_info(self):
        return self.value_ref_info
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, name=None, value=0.0, enabled=True, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        ObjectListStoreChildMixin.__init__(self)
        RefinementValue.__init__(self)
        
        self.changed = Signal()
        self.name = name
        self.value = value
        self.enabled = enabled
        
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------ 
    def resolve_relations(self):
        raise NotImplementedError, "Subclasses should implement the resolve_relations method!"
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def create_prop_store(self, prop=None):
        assert(self.component != None)
        store = ListStore(object, str, object)
        for i, atom in enumerate(self.component._layer_atoms.iter_objects()):
            store.append([atom, "pn", lambda o: o.name])
        for i, atom in enumerate(self.component._interlayer_atoms.iter_objects()):
            store.append([atom, "pn", lambda o: o.name])  
        for i, relation in enumerate(self.component._atom_relations.iter_objects()):
            tp = type(relation)
            if tp in self.allowed_relations:
                prop, name = self.allowed_relations[tp]
                store.append([relation, prop, name])          
        return store
    
    def apply_relation(self):
        raise NotImplementedError, "Subclasses should implement the update_value method!"
    
    pass #end of class
    
@storables.register()
class AtomRatio(AtomRelation):
    
    #MODEL INTEL:
    __parent_alias__ = "component"
    __model_intel__ = [
        PropIntel(name="sum",       label="Sum",                     data_type=float,  widget_type='float_input', is_column=True,  storable=True,  has_widget=True, minimum=0.0),
        PropIntel(name="atom1",     label="Substituting Atom",       data_type=object, is_column=True,  storable=True,  has_widget=True),
        PropIntel(name="atom2",     label="Original Atom",           data_type=object, is_column=True,  storable=True,  has_widget=True),
    ]
    __store_id__ = "AtomRatio"
    
    #SIGNALS:
    
    #PROPERTIES:       
    _sum = 1.0
    def get_sum_value(self): return self._sum
    def set_sum_value(self, value):
        self._sum = float(value)
        self.changed.emit()
    
    def __internal_sum__(self, value):
        self._sum = float(value)
        self.apply_relation()
    __internal_sum__ = property(fset=__internal_sum__)
       
    _atom1 = [None, None]
    def get_atom1_value(self): return self._atom1
    def set_atom1_value(self, value):
        self._atom1 = value
        self.changed.emit()
    
    _atom2 = [None, None]
    def get_atom2_value(self): return self._atom2    
    def set_atom2_value(self, value):
        self._atom2 = value
        self.changed.emit()

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, sum=0.0, atom1=[None, None], atom2=[None, None], name="New Ratio", **kwargs):
        AtomRelation.__init__(self, name=name, **kwargs)
        
        self.sum = sum or self.get_depr(kwargs, self._sum, "data_sum")
               
        atom1 = atom1 or self._parseattr(self.get_depr(kwargs, [None, None], "prop1", "data_prop1"))
        if isinstance(atom1[0], basestring): atom1[0] = pyxrd_object_pool.get_object(atom1[0])
        self.atom1 = list(atom1)
        
        atom2 = atom2 or self._parseattr(self.get_depr(kwargs, [None, None], "prop2", "data_prop2"))
        if isinstance(atom2[0], basestring): atom2[0] = pyxrd_object_pool.get_object(atom2[0])
        self.atom2 = list(atom2)
        
             
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------                        
    def json_properties(self):
        retval = Storable.json_properties(self)
        retval["atom1"] = [retval["atom1"][0].uuid if retval["atom1"][0] else None, retval["atom1"][1]]
        retval["atom2"] = [retval["atom2"][0].uuid if retval["atom2"][0] else None, retval["atom2"][1]]
        return retval             
                
    def resolve_relations(self):
        pass #not needed for AtomRatio

                
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def apply_relation(self):
        if self.enabled and self.applicable:
            if self.atom1:
                obj, prop = self.atom1
                if obj and prop:
                    setattr(obj, prop, self.value*self.sum)
            if self.atom2:
                obj, prop = self.atom2
                if obj and prop:
                    setattr(obj, prop, (1.0-self.value)*self.sum)
        
    pass #end of class
    
@storables.register()
class AtomContents(AtomRelation):
    
    #MODEL INTEL:
    __parent_alias__ = "component"
    __model_intel__ = [
        PropIntel(name="atom_contents", label="Atom contents",  data_type=object,    is_column=True,  storable=True,  has_widget=True),
    ]
    __store_id__ = "AtomContents"
        
    allowed_relations = {
        AtomRatio: ("__internal_sum__", lambda o: o.name),
    }
        
    #SIGNALS:
    
    #PROPERTIES:       
    _atom_contents = None
    def get_atom_contents_value(self): return self._atom_contents
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, atom_contents=None, name="New Contents", **kwargs):
        AtomRelation.__init__(self,  name=name, **kwargs)
        self._atom_contents = ListStore(object, object, float)
        
        if atom_contents:
            for row in atom_contents:
                self._atom_contents.append(row)
                
        def on_change(*args):
            if self.enabled: #no need for updates in this case
                from traceback import print_stack
                print_stack()
                self.changed.emit()
        self._atom_contents.connect("row-changed", on_change)
        self._atom_contents.connect("row-inserted", on_change)
        self._atom_contents.connect("row-deleted", on_change)
        
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------                        
    def json_properties(self):
        retval = Storable.json_properties(self)    
        retval["atom_contents"] = list([
            [row[0].uuid if row[0] else None, row[1], row[2]] 
            for row in retval["atom_contents"]
        ])
        return retval
        
    def resolve_relations(self):
        # Disable event dispatching to prevent infinite loops
        enabled = self.enabled
        self.enabled = False
        # Change rows with string references to objects (uuid's)
        for row in self._atom_contents:
            if isinstance(row[0], basestring):
                row[0] = pyxrd_object_pool.get_object(row[0])
        # Set the flag to its original value
        self.enabled = enabled
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def apply_relation(self):
        if self.enabled and self.applicable:
            for atom, prop, amount in self.atom_contents:
                if not (atom=="" or atom==None or prop==None): 
                    setattr(atom, prop, amount*self.value)
        
    pass #end of class
