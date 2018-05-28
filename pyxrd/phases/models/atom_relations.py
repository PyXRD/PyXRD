# coding=UTF-8
# ex:ts=4:sw=4:et=on
#
# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import types
from functools import partial

import gi
gi.require_version('Gtk', '3.0')  # @UndefinedVariable
from gi.repository import Gtk  # @UnresolvedImport

from mvc.models.properties import (
    LabeledProperty, StringProperty, BoolProperty, FloatProperty,
    SignalMixin, ReadOnlyMixin, ListProperty
)
from mvc.observers import ListObserver
from mvc import Model

from pyxrd.generic.models import DataModel
from pyxrd.generic.io import storables, Storable, get_case_insensitive_glob

from pyxrd.refinement.refinables.mixins import RefinementValue
from pyxrd.refinement.refinables.properties import RefinableMixin
from pyxrd.refinement.refinables.metaclasses import PyXRDRefinableMeta

class ComponentPropMixin(object):
    """
        A mixin which provides some common utility functions for retrieving
        properties using a string description (e.g. 'layer_atoms.1' or 'b_cell')
    """

    def _parseattr(self, attr):
        """
            Function used for handling (deprecated) 'property strings':
            attr contains a string (e.g. cell_a or layer_atoms.2) which can be 
            parsed into an object and a property.
            Current implementation uses UUID's, however this is still here for
            backwards-compatibility...
            Will be removed at some point!
        """
        if not isinstance(attr, str):
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
class AtomRelation(ComponentPropMixin, RefinementValue, DataModel, Storable, metaclass=PyXRDRefinableMeta):

    # MODEL INTEL:
    class Meta(DataModel.Meta):
        store_id = "AtomRelation"
        file_filters = [
            ("Atom relation", get_case_insensitive_glob("*.atr")),
        ]
        allowed_relations = {}

    component = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:
    #: The name of this AtomRelation
    name = StringProperty(
        default="", text="Name",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: The value of this AtomRelation
    value = FloatProperty(
        default=0.0, text="Value",
        visible=True, persistent=True, tabular=True, widget_type='float_entry',
        signal_name="data_changed", refinable=True,
        mix_with=(SignalMixin, RefinableMixin)
    )

    #: Flag indicating whether this AtomRelation is enabled or not
    enabled = BoolProperty(
        default=True, text="Enabled",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed",
        mix_with=(SignalMixin,)
    )

    #: Is True when this AtomRelation's value is driven by another AtomRelation.
    #: Should never be set directly or things might break!
    driven_by_other = BoolProperty(
        default=False, text="Driven by other",
        visible=False, persistent=False, tabular=True
    )

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
            *[prop.label for prop in AtomRelation.Meta.get_local_persistent_properties()]
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
        raise NotImplementedError("Subclasses should implement the resolve_relations method!")

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def create_prop_store(self, prop=None):
        if self.component is not None:
            store = Gtk.ListStore(object, str, str)
            for atom in self.component._layer_atoms:
                store.append([atom, "pn", atom.name])
            for atom in self.component._interlayer_atoms:
                store.append([atom, "pn", atom.name])
            for relation in self.component._atom_relations:
                tp = relation.Meta.store_id
                if tp in self.Meta.allowed_relations:
                    for prop, name in self.Meta.allowed_relations[tp]:
                        if callable(name):
                            name = name(relation)
                        store.append([relation, prop, name])
            return store

    def iter_references(self):
        raise NotImplementedError("'iter_references' should be implemented by subclasses!")

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
        raise NotImplementedError("Subclasses should implement the apply_relation method!")

    pass # end of class

@storables.register()
class AtomRatio(AtomRelation):

    # MODEL INTEL:
    class Meta(AtomRelation.Meta):
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
    #: The sum of the two atoms
    sum = FloatProperty(
        default=1.0, text="Sum", minimum=0.0,
        visible=True, persistent=True, tabular=True, widget_type='float_entry',
        signal_name="data_changed",
        mix_with=(SignalMixin,)
    )

    def __internal_sum__(self, value):
        """
        Special setter for other AtomRelation objects depending on the value of
        the sum of the AtomRatio. This can be used to have multi-substitution by
        linking two (or more) AtomRatio's. Eg Al-by-Mg-&-Fe:
        
        AtomRatioMgAndFeForAl -> links together Al content and Fe+Mg content
        
                              => sum = e.g. 4 set by user
                              
        AtomRatioMgForFe      -> links together the Fe and Mg content
        
                              => sum = set by previous ratio.
        """
        self._sum = float(value)
        self.apply_relation()
    __internal_sum__ = property(fset=__internal_sum__)

    def _set_driven_flag_for_prop(self, prop, *args):
        """Internal method used to safely set the driven_by_other flag on an object.
        Subclasses can override to provide a check on the property set by the driver."""
        if prop != "__internal_sum__":
            super(AtomRatio, self)._set_driven_flag_for_prop(prop)

    def _set_atom(self, value, label=None):
        if not self._safe_is_referring(value[0]):
            getattr(type(self), label)._set(self, value)

    #: The substituting atom
    atom1 = LabeledProperty(
        default=[None, None], text="Substituting Atom",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed", fset=partial(_set_atom, label="atom1"),
        mix_with=(SignalMixin,)
    )

    #: The Original atom
    atom2 = LabeledProperty(
        default=[None, None], text="Original Atom",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed", fset=partial(_set_atom, label="atom2"),
        mix_with=(SignalMixin,)
    )

    # ------------------------------------------------------------
    #      Initialization and other internals
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
            *[prop.label for prop in AtomRatio.Meta.get_local_persistent_properties()]
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
        if isinstance(self._unresolved_atom1[0], str):
            self._unresolved_atom1[0] = type(type(self)).object_pool.get_object(self._unresolved_atom1[0])
        self.atom1 = list(self._unresolved_atom1)
        del self._unresolved_atom1
        if isinstance(self._unresolved_atom2[0], str):
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

    atom = LabeledProperty(
        default=None, text="Atom",
        visible=False, persistent=False, tabular=True,
    )

    prop = LabeledProperty(
        default=None, text="Prop",
        visible=False, persistent=False, tabular=True,
    )

    amount = FloatProperty(
        default=0.0, text="Amount", minimum=0.0,
        visible=False, persistent=False, tabular=True,
    )

    def __init__(self, atom, prop, amount, *args, **kwargs):
        super(AtomContentObject, self).__init__(*args, **kwargs)
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
        store_id = "AtomContents"
        allowed_relations = {
            "AtomRatio": [
                ("__internal_sum__", lambda o: "%s: SUM" % o.name),
                ("value", lambda o: "%s: RATIO" % o.name),
            ],
        }

    # SIGNALS:

    # PROPERTIES:
    atom_contents = ListProperty(
        default=None, text="Atom contents",
        visible=True, persistent=True, tabular=True,
        data_type=AtomContentObject,
        mix_with=(ReadOnlyMixin,)
    )

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
            *[prop.label for prop in AtomContents.Meta.get_local_persistent_properties()]
        )
        super(AtomContents, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        # Load atom contents:
        atom_contents = []
        for uuid, prop, amount in self.get_kwarg(kwargs, [], "atom_contents"):
            # uuid's are resolved when resolve_relations is called
            atom_contents.append(AtomContentObject(uuid, prop, amount))
        type(self).atom_contents._set(self, atom_contents)

        def on_change(*args):
            if self.enabled: # no need for updates otherwise
                self.data_changed.emit()

        self._atom_contents_observer = ListObserver(
            on_change, on_change,
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
            if isinstance(atom_content.atom, str):
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
