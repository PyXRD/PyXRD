# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.




"""

 - an AtomRatio's sum (not the ratio itself) can be driven by another AtomRatio or from an AtomContents
 - an AtomContents' value can be driven  

"""

import types

from pyxrd.mvc.observers import ListObserver
from pyxrd.mvc import Model, PropIntel

from pyxrd.generic.models import DataModel
from pyxrd.generic.io import storables, Storable, get_case_insensitive_glob
from pyxrd.generic.refinement.mixins import RefinementValue
from pyxrd.generic.refinement.metaclasses import PyXRDRefinableMeta

class ComponentPropMixin(object):
    """
        A mixin which provides some common utility functions for retrieving
        properties using a string description (e.g. 'layer_atoms.1' or 'b_cell')
    """

    def __init__(self, *args, **kwargs):
        # Nothing to do but ignore any extraneous args & kwargs passed down
        super(ComponentPropMixin, self).__init__()

    def _parseattr(self, attr):
        """
            Function used for handling (deprecated) 'property strings':
            attr contains a string (e.g. cell_a or layer_atoms.2) which can be 
            parsed into an object and a property.
            Current implementation uses UUID's, however this is still here for
            backwards-compatibility...
            Will be removed at some point!
        """
        if not isinstance(attr, types.StringTypes):
            return attr

        if attr == "" or attr == None:
            return None

        def get_atom_by_index(atoms, index):
            for atom in atoms:
                if atom.atom_nr == index:
                    return atom
            return None

        attr = attr.replace("data_", "", 1) # for backwards compatibility
        attrs = attr.split(".")
        if attrs[0] == "layer_atoms":
            atom = get_atom_by_index(self.component._layer_atoms, int(attrs[1]))
            if atom is not None:
                return atom, "pn"
            else:
                return None
        elif attrs[0] == "interlayer_atoms":
            atom = get_atom_by_index(self.component._interlayer_atoms, int(attrs[1]))
            if atom is not None:
                return atom, "pn"
            else:
                return None
        else:
            return self.component, attr

@storables.register()
class AtomRelation(DataModel, Storable, ComponentPropMixin, RefinementValue):

    # MODEL INTEL:
    __metaclass__ = PyXRDRefinableMeta
    class Meta(DataModel.Meta):
        properties = [
            PropIntel(name="name", label="Name", data_type=unicode, is_column=True, storable=True, has_widget=True),
            PropIntel(name="value", label="Value", data_type=float, is_column=True, storable=True, has_widget=True, widget_type='float_entry', refinable=True),
            PropIntel(name="enabled", label="Enabled", data_type=bool, is_column=True, storable=True, has_widget=True),
            PropIntel(name="driven_by_other", label="Driven by other", data_type=bool, is_column=True, storable=False, has_widget=False)
        ]
        store_id = "AtomRelation"
        file_filters = [
            ("Atom relation", get_case_insensitive_glob("*.atr")),
        ]
        allowed_relations = {}

    component = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:
    _value = 0.0
    def get_value(self): return self._value
    def set_value(self, value):
        self._value = float(value)
        self.data_changed.emit()

    _name = ""
    def get_name(self): return self._name
    def set_name(self, value):
        self._name = str(value)
        self.visuals_changed.emit()

    _enabled = False
    def get_enabled(self): return self._enabled
    def set_enabled(self, value):
        self._enabled = bool(value)
        self.data_changed.emit()


    _driven_by_other = False
    @property
    def driven_by_other(self):
        """
        Is True when the AtomRelation's value is driven by another AtomRelation.
        Should never be set directly or things might break!
        """
        return self._driven_by_other
    @driven_by_other.setter
    def driven_by_other(self, value):
        self._driven_by_other = bool(value)

    @property
    def applicable(self):
        """
        Is True when this AtomRelation was passed a component of which the atom
        ratios are not set to be inherited from another component.
        """
        return (self.parent is not None and not self.parent.inherit_atom_relations)

    # REFINEMENT VALUE IMPLEMENTATION:
    @property
    def refine_title(self):
        return self.name

    @property
    def refine_descriptor_data(self):
        return dict(
            phase_name=self.component.phase.refine_title,
            component_name=self.component.refine_title
        )

    @property
    def refine_value(self):
        return self.value
    @refine_value.setter
    def refine_value(self, value):
        self.value = value

    @property
    def inside_linked_component(self):
        return (self.component.linked_with is not None) and self.component.inherit_atom_relations

    @property
    def is_refinable(self):
        return self.enabled and not self.driven_by_other and not self.inside_linked_component

    @property
    def refine_info(self):
        return self.value_ref_info

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for an AtomRelation are:
                name: the name of this AtomRelation
                value: the value for this AtomRelation
                enabled: boolean indicating whether or not this AtomRelation is 
                 enabled
        """
        my_kwargs = self.pop_kwargs(kwargs,
            "data_name", "data_ratio", "ratio",
            *[names[0] for names in AtomRelation.Meta.get_local_storable_properties()]
        )
        super(AtomRelation, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        self.name = self.get_kwarg(kwargs, "", "name", "data_name")
        self.value = self.get_kwarg(kwargs, 0.0, "value", "ratio", "data_ratio")
        self.enabled = bool(self.get_kwarg(kwargs, True, "enabled"))

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def resolve_relations(self):
        raise NotImplementedError, "Subclasses should implement the resolve_relations method!"

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def create_prop_store(self, prop=None):
        if self.component is not None:
            import gtk
            store = gtk.ListStore(object, str, object)
            for atom in self.component._layer_atoms:
                store.append([atom, "pn", lambda o: o.name])
            for atom in self.component._interlayer_atoms:
                store.append([atom, "pn", lambda o: o.name])
            for relation in self.component._atom_relations:
                tp = relation.Meta.store_id
                if tp in self.Meta.allowed_relations:
                    for prop, name in self.Meta.allowed_relations[tp]:
                        store.append([relation, prop, name])
            return store

    def iter_references(self):
        raise NotImplementedError, "'iter_references' should be implemented by subclasses!"

    def _safe_is_referring(self, value):
        if value is not None and hasattr(value, "is_referring"):
            return value.is_referring([self, ])
        else:
            return False

    def is_referring(self, references=None):
        """
            Checks whether this AtomRelation is causing circular references.
            Can be used to check this before actually setting references by
            setting the 'references' keyword argument to a list containing the
            new reference value(s).
        """
        if references == None:
            references = []
        # 1. Bluntly check if we're not already somewhere referred to,
        #    if not, add ourselves to the list of references
        if self in references:
            return True
        references.append(self)

        # 2. Loop over our own references, check if they cause a circular
        #    reference, if not add them to the list of references.
        for reference in self.iter_references():
            if reference is not None and hasattr(reference, "is_referring"):
                if reference.is_referring(references):
                    return True
                else:
                    references.append(reference)

        return False

    def _set_driven_flag_for_prop(self, prop=None):
        """Internal method used to safely set the driven_by_other flag on an object.
        Subclasses can override to provide a check on the property set by the driver."""
        self.driven_by_other = True

    def apply_relation(self):
        raise NotImplementedError, "Subclasses should implement the apply_relation method!"

    pass # end of class

@storables.register()
class AtomRatio(AtomRelation):

    # MODEL INTEL:
    class Meta(AtomRelation.Meta):
        properties = [
            PropIntel(name="sum", label="Sum", data_type=float, widget_type='float_entry', is_column=True, storable=True, has_widget=True, minimum=0.0),
            PropIntel(name="atom1", label="Substituting Atom", data_type=object, is_column=True, storable=True, has_widget=True),
            PropIntel(name="atom2", label="Original Atom", data_type=object, is_column=True, storable=True, has_widget=True),
        ]
        store_id = "AtomRatio"
        allowed_relations = {
            "AtomRatio": [
                ("__internal_sum__", lambda o: "%s: SUM" % o.name),
                ("value", lambda o: "%s: RATIO" % o.name),
            ],
            "AtomContents": [("value", lambda o: o.name)],
        }

    # SIGNALS:

    # PROPERTIES:
    _sum = 1.0
    def get_sum(self): return self._sum
    def set_sum(self, value):
        self._sum = float(value)
        self.data_changed.emit()

    def __internal_sum__(self, value):
        """
            Special setter for other AtomRelation objects depending on the value
            of the sum of the AtomRatio. This can be used to have multi-substitution
            by linking two (or more) AtomRatio's. Eg Al-by-Mg-&-Fe:
            AtomRatioMgAndFeForAl -> links together Al content and Fe+Mg content => sum = e.g. 4
            AtomRatioMgForFe -> links together the Fe and Mg content => sum = set by previous ratio.
        """
        self._sum = float(value)
        self.apply_relation()
    __internal_sum__ = property(fset=__internal_sum__)

    def _set_driven_flag_for_prop(self, prop, *args):
        """Internal method used to safely set the driven_by_other flag on an object.
        Subclasses can override to provide a check on the property set by the driver."""
        if prop != "__internal_sum__":
            super(AtomRatio, self)._set_driven_flag_for_prop(prop)

    _atom1 = [None, None]
    def get_atom1(self): return self._atom1
    def set_atom1(self, value):
        with self.data_changed.hold():
            if not self._safe_is_referring(value[0]):
                self._atom1 = value
                self.data_changed.emit()

    _atom2 = [None, None]
    def get_atom2(self): return self._atom2
    def set_atom2(self, value):
        with self.data_changed.hold():
            if not self._safe_is_referring(value[0]):
                self._atom2 = value
                self.data_changed.emit()

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs): # @ReservedAssignment
        """
            Valid keyword arguments for an AtomRatio are:
                sum: the sum of the atoms contents
                atom1: a tuple containing the first atom and its property name to read/set
                atom2: a tuple containing the first atom and its property name to read/set
            The value property is the 'ratio' of the first atom over the sum of both
        """
        my_kwargs = self.pop_kwargs(kwargs,
            "data_sum", "prop1", "data_prop1", "data_prop2", "prop2",
            *[names[0] for names in AtomRatio.Meta.get_local_storable_properties()]
        )
        super(AtomRatio, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        self.sum = self.get_kwarg(kwargs, self.sum, "sum", "data_sum")

        self._unresolved_atom1 = self._parseattr(self.get_kwarg(kwargs, [None, None], "atom1", "prop1", "data_prop1"))
        self._unresolved_atom2 = self._parseattr(self.get_kwarg(kwargs, [None, None], "atom2", "prop2", "data_prop2"))

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def json_properties(self):
        retval = Storable.json_properties(self)
        retval["atom1"] = [retval["atom1"][0].uuid if retval["atom1"][0] else None, retval["atom1"][1]]
        retval["atom2"] = [retval["atom2"][0].uuid if retval["atom2"][0] else None, retval["atom2"][1]]
        return retval

    def resolve_relations(self):
        if isinstance(self._unresolved_atom1[0], basestring):
            self._unresolved_atom1[0] = type(type(self)).object_pool.get_object(self._unresolved_atom1[0])
        self.atom1 = list(self._unresolved_atom1)
        del self._unresolved_atom1
        if isinstance(self._unresolved_atom2[0], basestring):
            self._unresolved_atom2[0] = type(type(self)).object_pool.get_object(self._unresolved_atom2[0])
        self.atom2 = list(self._unresolved_atom2)
        del self._unresolved_atom2

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def apply_relation(self):
        if self.enabled and self.applicable:
            for value, (atom, prop) in [(self.value, self.atom1), (1.0 - self.value, self.atom2)]:
                if atom and prop:
                    # do not fire events, just set attributes:
                    with atom.data_changed.ignore():
                        setattr(atom, prop, value * self.sum)
                        if hasattr(atom, "_set_driven_flag_for_prop"):
                            atom._set_driven_flag_for_prop(prop)

    def iter_references(self):
        for atom in [self.atom1[0], self.atom2[0]]:
            yield atom

    pass # end of class

class AtomContentObject(Model):
    """
        Wrapper around an atom object used in the AtomContents model.
        Stores the atom, the property to set and it's default amount.
    """
    class Meta(Model.Meta):
        properties = [
            PropIntel(name="atom", label="Atom", data_type=object, is_column=True),
            PropIntel(name="prop", label="Prop", data_type=object, is_column=True),
            PropIntel(name="amount", label="Amount", data_type=float, is_column=True, minimum=0.0),
        ]

    atom = None
    prop = None
    amount = 0.0

    def __init__(self, atom, prop, amount, **kwargs):
        super(AtomContentObject, self).__init__()
        self.atom = atom
        self.prop = prop
        self.amount = amount

    def update_atom(self, value):
        if not (self.atom == "" or self.atom is None or self.prop is None):
            with self.atom.data_changed.ignore():
                setattr(self.atom, self.prop, self.amount * value)
                if hasattr(self.atom, "_set_driven_flag_for_prop"):
                    self.atom._set_driven_flag_for_prop(self.prop)

    pass

@storables.register()
class AtomContents(AtomRelation):

    # MODEL INTEL:
    class Meta(AtomRelation.Meta):
        properties = [
            PropIntel(name="atom_contents", label="Atom contents", class_type=AtomContentObject, data_type=object, is_column=True, storable=True, has_widget=True),
        ]
        store_id = "AtomContents"
        allowed_relations = {
            "AtomRatio": [
                ("__internal_sum__", lambda o: "%s: SUM" % o.name),
                ("value", lambda o: "%s: RATIO" % o.name),
            ],
        }

    # SIGNALS:

    # PROPERTIES:
    _atom_contents = None
    def get_atom_contents(self): return self._atom_contents

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for an AtomContents are:
                atom_contents: a list of tuples containing the atom content 
                 object uuids, property names and default amounts 
        """
        my_kwargs = self.pop_kwargs(kwargs,
            *[names[0] for names in type(self).Meta.get_local_storable_properties()]
        )
        super(AtomContents, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        # Load atom contents:
        self._atom_contents = []
        for uuid, prop, amount in self.get_kwarg(kwargs, [], "atom_contents"):
            # uuid's are resolved when resolve_relations is called
            self._atom_contents.append(AtomContentObject(uuid, prop, amount))

        def on_change(*args):
            if self.enabled: # no need for updates in this case
                self.data_changed.emit()

        self._atom_contents_observer = ListObserver(
            on_change,
            on_change,
            prop_name="atom_contents",
            model=self
        )

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def json_properties(self):
        retval = Storable.json_properties(self)
        retval["atom_contents"] = list([
            [
                atom_contents.atom.uuid if atom_contents.atom else None,
                atom_contents.prop,
                atom_contents.amount
            ] for atom_contents in retval["atom_contents"]
        ])
        return retval

    def resolve_relations(self):
        # Disable event dispatching to prevent infinite loops
        enabled = self.enabled
        self.enabled = False
        # Change rows with string references to objects (uuid's)
        for atom_content in self.atom_contents:
            if isinstance(atom_content.atom, basestring):
                atom_content.atom = type(type(self)).object_pool.get_object(atom_content.atom)
        # Set the flag to its original value
        self.enabled = enabled

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def apply_relation(self):
        if self.enabled and self.applicable:
            for atom_content in self.atom_contents:
                atom_content.update_atom(self.value)

    def set_atom_content_values(self, path, new_atom, new_prop):
        """    
            Convenience function that first checks if the new atom value will
            not cause a circular reference before actually setting it.
        """
        with self.data_changed.hold():
            atom_content = self.atom_contents[int(path[0])]
            if atom_content.atom != new_atom:
                old_atom = atom_content.atom
                atom_content.atom = None # clear...
                if not self._safe_is_referring(new_atom):
                    atom_content.atom = new_atom
                else:
                    atom_content.atom = old_atom
            else:
                atom_content.atom = None
            atom_content.prop = new_prop

    def iter_references(self):
        for atom_content in self.atom_contents:
            yield atom_content.atom

    pass # end of class
