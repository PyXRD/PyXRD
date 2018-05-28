# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import zipfile
from warnings import warn

from mvc.models.properties import (
    FloatProperty, SignalMixin, BoolProperty, StringProperty,
    LabeledProperty, SignalProperty, ObserveMixin, ListProperty,

)
from mvc.observers.list_observer import ListObserver

from pyxrd.generic.io import storables, Storable, COMPRESSION
from pyxrd.generic.models import DataModel
from pyxrd.generic.models.properties import InheritableMixin

from pyxrd.calculations.components import get_factors
from pyxrd.calculations.data_objects import ComponentData

from pyxrd.refinement.refinables.mixins import RefinementGroup
from pyxrd.refinement.refinables.metaclasses import PyXRDRefinableMeta
from pyxrd.refinement.refinables.properties import RefinableMixin

from pyxrd.atoms.models import Atom

from pyxrd.file_parsers.json_parser import JSONParser

from .atom_relations import AtomRelation
from .unit_cell_prop import UnitCellProperty

@storables.register()
class Component(RefinementGroup, DataModel, Storable, metaclass=PyXRDRefinableMeta):

    # MODEL INTEL:
    class Meta(DataModel.Meta):
        store_id = "Component"

    _data_object = None
    @property
    def data_object(self):
        weight = 0.0

        self._data_object.layer_atoms = [None] * len(self.layer_atoms)
        for i, atom in enumerate(self.layer_atoms):
            self._data_object.layer_atoms[i] = atom.data_object
            weight += atom.weight

        self._data_object.interlayer_atoms = [None] * len(self.interlayer_atoms)
        for i, atom in enumerate(self.interlayer_atoms):
            self._data_object.interlayer_atoms[i] = atom.data_object
            weight += atom.weight

        self._data_object.volume = self.get_volume()
        self._data_object.weight = weight
        self._data_object.d001 = self.d001
        self._data_object.default_c = self.default_c
        self._data_object.delta_c = self.delta_c
        self._data_object.lattice_d = self.lattice_d

        return self._data_object

    phase = property(DataModel.parent.fget, DataModel.parent.fset)

    # SIGNALS:
    atoms_changed = SignalProperty()

    # UNIT CELL DIMENSION SHORTCUTS:
    @property
    def cell_a(self):
        return self._ucp_a.value
    @property
    def cell_b(self):
        return self._ucp_b.value
    @property
    def cell_c(self):
        return self.d001

    # PROPERTIES:

    #: The name of the Component
    name = StringProperty(
        default="", text="Name",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: Flag indicating whether to inherit the UCP a from :attr:`~linked_with`
    @BoolProperty(
        default=False, text="Inh. cell length a",
        visible=True, persistent=True, tabular=True,
    )
    def inherit_ucp_a(self):
        return self._ucp_a.inherited
    @inherit_ucp_a.setter
    def inherit_ucp_a(self, value):
        self._ucp_a.inherited = value

    #: Flag indicating whether to inherit the UCP b from :attr:`~linked_with`
    @BoolProperty(
        default=False, text="Inh. cell length b",
        visible=True, persistent=True, tabular=True,
    )
    def inherit_ucp_b(self):
        return self._ucp_b.inherited
    @inherit_ucp_b.setter
    def inherit_ucp_b(self, value):
        self._ucp_b.inherited = value

    #: Flag indicating whether to inherit d001 from :attr:`~linked_with`
    inherit_d001 = BoolProperty(
        default=False, text="Inh. cell length c",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed",
        mix_with=(SignalMixin,)
    )

    #: Flag indicating whether to inherit default_c from :attr:`~linked_with`
    inherit_default_c = BoolProperty(
        default=False, text="Inh. default length c",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed",
        mix_with=(SignalMixin,)
    )

    #: Flag indicating whether to inherit delta_c from :attr:`~linked_with`
    inherit_delta_c = BoolProperty(
        default=False, text="Inh. c length dev.",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed",
        mix_with=(SignalMixin,)
    )

    #: Flag indicating whether to inherit layer_atoms from :attr:`~linked_with`
    inherit_layer_atoms = BoolProperty(
        default=False, text="Inh. layer atoms",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed",
        mix_with=(SignalMixin,)
    )

    #: Flag indicating whether to inherit interlayer_atoms from :attr:`~linked_with`
    inherit_interlayer_atoms = BoolProperty(
        default=False, text="Inh. interlayer atoms",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed",
        mix_with=(SignalMixin,)
    )

    #: Flag indicating whether to inherit atom_relations from :attr:`~linked_with`
    inherit_atom_relations = BoolProperty(
        default=False, text="Inh. atom relations",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed",
        mix_with=(SignalMixin,)
    )

    _linked_with_index = None
    _linked_with_uuid = None

    #: The :class:`~Component` this component is linked with
    linked_with = LabeledProperty(
        default=None, text="Linked with",
        visible=True, persistent=True,
        signal_name="data_changed",
        mix_with=(SignalMixin,)
    )
    @linked_with.setter
    def linked_with(self, value):
        old = type(self).linked_with._get(self)
        if old != value:
            if old is not None:
                self.relieve_model(old)
            type(self).linked_with._set(self, value)
            if value is not None:
                self.observe_model(value)
            else:
                for prop in self.Meta.get_inheritable_properties():
                    setattr(self, prop.inherit_flag, False)

    #: The silicate lattice's c length
    lattice_d = FloatProperty(
        default=0.0, text="Lattice c length [nm]",
        visible=False, persistent=True,
        signal_name="data_changed"
    )

    ucp_a = LabeledProperty(
        default=None, text="Cell length a [nm]",
        visible=True, persistent=True, tabular=True, refinable=True,
        inheritable=True, inherit_flag="inherit_ucp_a", inherit_from="linked_with.ucp_a",
        signal_name="data_changed",
        mix_with=(SignalMixin, InheritableMixin, ObserveMixin, RefinableMixin)
    )

    ucp_b = LabeledProperty(
        default=None, text="Cell length b [nm]",
        visible=True, persistent=True, tabular=True, refinable=True,
        inheritable=True, inherit_flag="inherit_ucp_b", inherit_from="linked_with.ucp_b",
        signal_name="data_changed",
        mix_with=(SignalMixin, InheritableMixin, ObserveMixin, RefinableMixin)
    )

    d001 = FloatProperty(
        default=1.0, text="Cell length c [nm]", minimum=0.0, maximum=5.0,
        visible=True, persistent=True, tabular=True, refinable=True,
        inheritable=True, inherit_flag="inherit_default_c", inherit_from="linked_with.d001",
        signal_name="data_changed",
        mix_with=(SignalMixin, InheritableMixin, RefinableMixin)
    )

    default_c = FloatProperty(
        default=1.0, text="Default c length [nm]", minimum=0.0, maximum=5.0,
        visible=True, persistent=True, tabular=True,
        inheritable=True, inherit_flag="inherit_default_c", inherit_from="linked_with.default_c",
        signal_name="data_changed",
        mix_with=(SignalMixin, InheritableMixin)
    )

    delta_c = FloatProperty(
        default=0.0, text="C length dev. [nm]", minimum=0.0, maximum=0.05,
        visible=True, persistent=True, tabular=True,
        inheritable=True, inherit_flag="inherit_delta_c", inherit_from="linked_with.delta_c",
        signal_name="data_changed",
        mix_with=(SignalMixin, InheritableMixin, RefinableMixin)
    )

    layer_atoms = ListProperty(
        default=None, text="Layer atoms",
        visible=True, persistent=True, tabular=True, widget_type="custom",
        inheritable=True, inherit_flag="inherit_layer_atoms", inherit_from="linked_with.layer_atoms",
        signal_name="data_changed", data_type=Atom,
        mix_with=(SignalMixin, InheritableMixin)
    )

    interlayer_atoms = ListProperty(
        default=None, text="Interlayer atoms",
        visible=True, persistent=True, tabular=True, widget_type="custom",
        inheritable=True, inherit_flag="inherit_interlayer_atoms", inherit_from="linked_with.interlayer_atoms",
        signal_name="data_changed", data_type=Atom,
        mix_with=(SignalMixin, InheritableMixin)
    )

    atom_relations = ListProperty(
        default=None, text="Atom relations", widget_type="custom",
        visible=True, persistent=True, tabular=True, refinable=True,
        inheritable=True, inherit_flag="inherit_atom_relations", inherit_from="linked_with.atom_relations",
        signal_name="data_changed", data_type=AtomRelation,
        mix_with=(SignalMixin, InheritableMixin, RefinableMixin)
    )

    # Instance flag indicating whether or not linked_with & inherit flags should be saved
    save_links = True
    # Class flag indicating whether or not atom types in the component should be
    # exported using their name rather then their project-uuid.
    export_atom_types = False

    # REFINEMENT GROUP IMPLEMENTATION:
    @property
    def refine_title(self):
        return self.name

    @property
    def refine_descriptor_data(self):
        return dict(
            phase_name=self.phase.refine_title,
            component_name=self.refine_title
        )

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, **kwargs):
        """
        Valid keyword arguments for a Component are:
        *ucp_a*: unit cell property along a axis
        *ucp_b*: unit cell property along b axis
        *d001*: unit cell length c (aka d001)
        *default_c*: default c-value
        *delta_c*: the variation in basal spacing due to defects
        *layer_atoms*: ObjectListStore of layer Atoms
        *interlayer_atoms*: ObjectListStore of interlayer Atoms
        *atom_relations*: ObjectListStore of AtomRelations
        *inherit_ucp_a*: whether or not to inherit the ucp_a property from
         the linked component (if linked)
        *inherit_ucp_b*: whether or not to inherit the ucp_b property from
         the linked component (if linked)
        *inherit_d001*: whether or not to inherit the d001 property from
         the linked component (if linked)
        *inherit_default_c*: whether or not to inherit the default_c 
         property from the linked component (if linked)
        *inherit_delta_c*: whether or not to inherit the delta_c 
         property from the linked component (if linked)
        *inherit_layer_atoms*: whether or not to inherit the layer_atoms 
         property from the linked component (if linked)
        *inherit_interlayer_atoms*: whether or not to inherit the
         interlayer_atoms property from the linked component (if linked)
        *inherit_atom_relations*: whether or not to inherit the 
         atom_relations property from the linked component (if linked)
        *linked_with_uuid*: the UUID for the component this one is linked
         with
    Deprecated, but still supported:
        *linked_with_index*: the index of the component this one is 
         linked with in the ObjectListStore of the parent based on phase.
        """

        my_kwargs = self.pop_kwargs(kwargs,
            "data_name", "data_layer_atoms", "data_interlayer_atoms", "data_atom_relations",
            "data_atom_ratios", "data_d001", "data_default_c", "data_delta_c", "lattice_d",
            "data_cell_a", "data_ucp_a", "data_cell_b", "data_ucp_b",
            "linked_with_uuid", "linked_with_index", "inherit_cell_a", "inherit_cell_b",
            *[prop.label for prop in Component.Meta.get_local_persistent_properties()]
        )
        super(Component, self).__init__(**kwargs)
        kwargs = my_kwargs

        # Set up data object
        self._data_object = ComponentData(
            d001=0.0,
            delta_c=0.0
        )

        # Set attributes:
        self.name = self.get_kwarg(kwargs, "", "name", "data_name")

        # Load lists:
        self.layer_atoms = self.get_list(kwargs, [], "layer_atoms", "data_layer_atoms", parent=self)
        self.interlayer_atoms = self.get_list(kwargs, [], "interlayer_atoms", "data_interlayer_atoms", parent=self)
        self.atom_relations = self.get_list(kwargs, [], "atom_relations", "data_atom_relations", parent=self)

        # Add all atom ratios to the AtomRelation list
        for atom_ratio in self.get_list(kwargs, [], "atom_ratios", "data_atom_ratios", parent=self):
            self.atom_relations.append(atom_ratio)

        # Observe the inter-layer atoms, and make sure they get stretched
        for atom in self.interlayer_atoms:
            atom.stretch_values = True
            self.observe_model(atom)

        # Observe the layer atoms
        for atom in self.layer_atoms:
            self.observe_model(atom)

        # Resolve their relations and observe the atom relations
        for relation in self.atom_relations:
            relation.resolve_relations()
            self.observe_model(relation)

        # Connect signals to lists and dicts:
        self._layer_atoms_observer = ListObserver(
            self._on_layer_atom_inserted,
            self._on_layer_atom_removed,
            prop_name="layer_atoms",
            model=self
        )
        self._interlayer_atoms_observer = ListObserver(
            self._on_interlayer_atom_inserted,
            self._on_interlayer_atom_removed,
            prop_name="interlayer_atoms",
            model=self
        )
        self._atom_relations_observer = ListObserver(
            self._on_atom_relation_inserted,
            self._on_atom_relation_removed,
            prop_name="atom_relations",
            model=self
        )

        # Update lattice values:
        self.d001 = self.get_kwarg(kwargs, self.d001, "d001", "data_d001")
        self._default_c = float(self.get_kwarg(kwargs, self.d001, "default_c", "data_default_c"))
        self.delta_c = float(self.get_kwarg(kwargs, self.delta_c, "delta_c", "data_delta_c"))
        self.update_lattice_d()

        # Set/Create & observe unit cell properties:
        ucp_a = self.get_kwarg(kwargs, None, "ucp_a", "data_ucp_a", "data_cell_a")
        if isinstance(ucp_a, float):
            ucp_a = UnitCellProperty(name="cell length a", value=ucp_a, parent=self)
        ucp_a = self.parse_init_arg(
            ucp_a, UnitCellProperty, child=True,
            default_is_class=True, name="Cell length a [nm]", parent=self
        )
        type(self).ucp_a._set(self, ucp_a)
        self.observe_model(ucp_a)

        ucp_b = self.get_kwarg(kwargs, None, "ucp_b", "data_ucp_b", "data_cell_b")
        if isinstance(ucp_b, float):
            ucp_b = UnitCellProperty(name="cell length b", value=ucp_b, parent=self)
        ucp_b = self.parse_init_arg(
            ucp_b, UnitCellProperty, child=True,
            default_is_class=True, name="Cell length b [nm]", parent=self
        )
        type(self).ucp_b._set(self, ucp_b)
        self.observe_model(ucp_b)

        # Set links:
        self._linked_with_uuid = self.get_kwarg(kwargs, "", "linked_with_uuid")
        self._linked_with_index = self.get_kwarg(kwargs, -1, "linked_with_index")

        # Set inherit flags:
        self.inherit_d001 = self.get_kwarg(kwargs, False, "inherit_d001")
        self.inherit_ucp_a = self.get_kwarg(kwargs, False, "inherit_ucp_a", "inherit_cell_a")
        self.inherit_ucp_b = self.get_kwarg(kwargs, False, "inherit_ucp_b", "inherit_cell_b")
        self.inherit_default_c = self.get_kwarg(kwargs, False, "inherit_default_c")
        self.inherit_delta_c = self.get_kwarg(kwargs, False, "inherit_delta_c")
        self.inherit_layer_atoms = self.get_kwarg(kwargs, False, "inherit_layer_atoms")
        self.inherit_interlayer_atoms = self.get_kwarg(kwargs, False, "inherit_interlayer_atoms")
        self.inherit_atom_relations = self.get_kwarg(kwargs, False, "inherit_atom_relations")

    def __repr__(self):
        return "Component(name='%s', linked_with=%r)" % (self.name, self.linked_with)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @DataModel.observe("data_changed", signal=True)
    def _on_data_model_changed(self, model, prop_name, info):
        # Check whether the changed model is an AtomRelation or Atom, if so
        # re-apply the atom_relations.
        with self.data_changed.hold():
            if isinstance(model, AtomRelation) or isinstance(model, Atom):
                self._apply_atom_relations()
                self._update_ucp_values()
            if isinstance(model, UnitCellProperty):
                self.data_changed.emit() # propagate signal

    @DataModel.observe("removed", signal=True)
    def _on_data_model_removed(self, model, prop_name, info):
        # Check whether the removed component is linked with this one, if so
        # clears the link and emits the data_changed signal.
        if model != self and self.linked_with is not None and self.linked_with == model:
            with self.data_changed.hold_and_emit():
                self.linked_with = None

    def _on_layer_atom_inserted(self, atom):
        """Sets the atoms parent and stretch_values property,
        updates the components lattice d-value, and emits a data_changed signal"""
        with self.data_changed.hold_and_emit():
            with self.atoms_changed.hold_and_emit():
                atom.parent = self
                atom.stretch_values = False
                self.observe_model(atom)
                self.update_lattice_d()

    def _on_layer_atom_removed(self, atom):
        """Clears the atoms parent, updates the components lattice d-value, and
        emits a data_changed signal"""
        with self.data_changed.hold_and_emit():
            with self.atoms_changed.hold_and_emit():
                self.relieve_model(atom)
                atom.parent = None
                self.update_lattice_d()

    def _on_interlayer_atom_inserted(self, atom):
        """Sets the atoms parent and stretch_values property, 
        and emits a data_changed signal"""
        with self.data_changed.hold_and_emit():
            with self.atoms_changed.hold_and_emit():
                atom.stretch_values = True
                atom.parent = self
    def _on_interlayer_atom_removed(self, atom):
        """Clears the atoms parent property, 
        and emits a data_changed signal"""
        with self.data_changed.hold_and_emit():
            with self.atoms_changed.hold_and_emit():
                atom.parent = None

    def _on_atom_relation_inserted(self, item):
        item.parent = self
        self.observe_model(item)
        self._apply_atom_relations()

    def _on_atom_relation_removed(self, item):
        self.relieve_model(item)
        item.parent = None
        self._apply_atom_relations()

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def resolve_json_references(self):
        for atom in type(self).layer_atoms._get(self):
            atom.resolve_json_references()
        for atom in type(self).interlayer_atoms._get(self):
            atom.resolve_json_references()

        type(self).ucp_a._get(self).resolve_json_references()
        type(self).ucp_a._get(self).update_value()
        type(self).ucp_b._get(self).resolve_json_references()
        type(self).ucp_b._get(self).update_value()

        if getattr(self, "_linked_with_uuid", None):
            self.linked_with = type(type(self)).object_pool.get_object(self._linked_with_uuid)
            del self._linked_with_uuid
        elif getattr(self, "_linked_with_index", None) and self._linked_with_index != -1:
            warn("The use of object indeces is deprected since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
            self.linked_with = self.parent.based_on.components.get_user_from_index(self._linked_with_index)
            del self._linked_with_index

    @classmethod
    def save_components(cls, components, filename):
        """
            Saves multiple components to a single file.
        """
        Component.export_atom_types = True
        for comp in components:
            comp.save_links = False
        with zipfile.ZipFile(filename, 'w', compression=COMPRESSION) as zfile:
            for component in components:
                zfile.writestr(component.uuid, component.dump_object())
        for comp in components:
            comp.save_links = True
        Component.export_atom_types = False

        # After export we change all the UUID's
        # This way, we're sure that we're not going to import objects with
        # duplicate UUID's!
        type(cls).object_pool.change_all_uuids()

    @classmethod
    def load_components(cls, filename, parent=None):
        """
            Returns multiple components loaded from a single file.
        """
        # Before import, we change all the UUID's
        # This way we're sure that we're not going to import objects
        # with duplicate UUID's!
        type(cls).object_pool.change_all_uuids()
        if zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename, 'r') as zfile:
                for uuid in zfile.namelist():
                    obj = JSONParser.parse(zfile.open(uuid))
                    obj.parent = parent
                    yield obj
        else:
            obj = JSONParser.parse(filename)
            obj.parent = parent
            yield obj

    def json_properties(self):
        if self.phase == None or not self.save_links:
            retval = Storable.json_properties(self)
            for prop in self.Meta.all_properties:
                if getattr(prop, "inherit_flag", False):
                    retval[prop.inherit_flag] = False
        else:
            retval = Storable.json_properties(self)
            retval["linked_with_uuid"] = self.linked_with.uuid if self.linked_with is not None else ""
        return retval

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_factors(self, range_stl):
        """
        Get the structure factor for the given range of sin(theta)/lambda values.
        :param range_stl: A 1D numpy ndarray
        """
        return get_factors(range_stl, self.data_object)

    def get_interlayer_stretch_factors(self):
        z_factor = (self.cell_c - self.lattice_d) / (self.default_c - self.lattice_d)
        return self.lattice_d, z_factor

    def update_lattice_d(self):
        """
            Updates the lattice_d attribute for this :class:`~.Component`. 
            Should normally not be called from outside the component.
        """
        for atom in self.layer_atoms:
            self.lattice_d = float(max(self.lattice_d, atom.default_z))

    def _apply_atom_relations(self):
        """
        Applies the :class:`~..atom_relations.AtomRelation` objects
        in this component. Should normally not be called from outside the component.
        """
        with self.data_changed.hold_and_emit():
            for relation in self.atom_relations:
                # Clear the 'driven by' flags:
                relation.driven_by_other = False
            for relation in self.atom_relations:
                # Apply the relations, will also take care of flag setting:
                relation.apply_relation()

    def _update_ucp_values(self):
        """
        Updates the :class:`~..unit_cell_prop.UnitCellProperty` objects in this
        component. Should normally not be called from outside the component.
        """
        with self.data_changed.hold():
            for ucp in [self._ucp_a, self._ucp_b]:
                ucp.update_value()

    def get_volume(self):
        """
        Get the volume for this :class:`~.Component`.
        Will always return a value >= 1e-25, to prevent division-by-zero
        errors in calculation code.  
        """
        return max(self.cell_a * self.cell_b * self.cell_c, 1e-25)

    def get_weight(self):
        """
        Get the total atomic weight for this 
        :class:`~.Component`. 
        """
        weight = 0
        for atom in (self.layer_atoms + self.interlayer_atoms):
            weight += atom.weight
        return weight

    # ------------------------------------------------------------
    #      AtomRelation list related
    # ------------------------------------------------------------
    def move_atom_relation_up(self, relation):
        """
        Move the passed :class:`~..atom_relations.AtomRelation`
        up one slot
        """
        index = self.atom_relations.index(relation)
        del self.atom_relations[index]
        self.atom_relations.insert(max(index - 1, 0), relation)

    def move_atom_relation_down(self, relation):
        """
        Move the passed :class:`~..atom_relations.AtomRelation`
        down one slot
        """
        index = self.atom_relations.index(relation)
        del self.atom_relations[index]
        self.atom_relations.insert(min(index + 1, len(self.atom_relations)), relation)

    pass # end of class
