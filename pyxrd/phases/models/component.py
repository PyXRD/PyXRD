# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import zipfile
from warnings import warn

from mvc import PropIntel
from mvc.observers import ListObserver

from pyxrd.generic.io import storables, Storable, COMPRESSION
from pyxrd.generic.models import DataModel, HoldableSignal

from pyxrd.calculations.components import get_factors
from pyxrd.calculations.data_objects import ComponentData

from pyxrd.refinement.refinables.mixins import RefinementGroup
from pyxrd.refinement.refinables.metaclasses import PyXRDRefinableMeta

from pyxrd.atoms.models import Atom

from pyxrd.file_parsers.json_parser import JSONParser

from .atom_relations import AtomRelation
from .unit_cell_prop import UnitCellProperty

@storables.register()
class Component(RefinementGroup, DataModel, Storable):

    # MODEL INTEL:
    __metaclass__ = PyXRDRefinableMeta
    class Meta(DataModel.Meta):
        properties = [
            PropIntel(name="name", data_type=unicode, label="Name", is_column=True, has_widget=True, storable=True),
            PropIntel(name="linked_with", data_type=object, label="Linked with", widget_type='custom', is_column=True, has_widget=True),
            PropIntel(name="d001", data_type=float, label="Cell length c [nm]", is_column=True, has_widget=True, storable=True, refinable=True, minimum=0.0, maximum=5.0, inh_name="inherit_d001", stor_name="_d001", inh_from="linked_with"),
            PropIntel(name="lattice_d", data_type=float, label="Lattice c length [nm]"),
            PropIntel(name="default_c", data_type=float, label="Default c length [nm]", is_column=True, has_widget=True, storable=True, minimum=0.0, maximum=5.0, inh_name="inherit_default_c", stor_name="_default_c", inh_from="linked_with"),
            PropIntel(name="delta_c", data_type=float, label="C length dev. [nm]", is_column=True, has_widget=True, storable=True, refinable=True, minimum=0.0, maximum=0.05, inh_name="inherit_delta_c", stor_name="_delta_c", inh_from="linked_with"),
            PropIntel(name="ucp_a", data_type=object, label="Cell length a [nm]", is_column=True, has_widget=True, storable=True, refinable=True, inh_name="inherit_ucp_a", stor_name="_ucp_a", inh_from="linked_with"),
            PropIntel(name="ucp_b", data_type=object, label="Cell length b [nm]", is_column=True, has_widget=True, storable=True, refinable=True, inh_name="inherit_ucp_b", stor_name="_ucp_b", inh_from="linked_with"),
            PropIntel(name="inherit_d001", data_type=bool, label="Inh. cell length c", is_column=True, has_widget=True, storable=True),
            PropIntel(name="inherit_ucp_b", data_type=bool, label="Inh. cell length b", is_column=True, has_widget=True, storable=True),
            PropIntel(name="inherit_ucp_a", data_type=bool, label="Inh. cell length a", is_column=True, has_widget=True, storable=True),
            PropIntel(name="inherit_default_c", data_type=bool, label="Inh. default length c", is_column=True, has_widget=True, storable=True),
            PropIntel(name="inherit_delta_c", data_type=bool, label="Inh. c length dev.", is_column=True, has_widget=True, storable=True),
            PropIntel(name="inherit_layer_atoms", data_type=bool, label="Inh. layer atoms", is_column=True, has_widget=True, storable=True),
            PropIntel(name="inherit_interlayer_atoms", data_type=bool, label="Inh. interlayer atoms", is_column=True, has_widget=True, storable=True),
            PropIntel(name="inherit_atom_relations", data_type=bool, label="Inh. atom relations", is_column=True, has_widget=True, storable=True),
            PropIntel(name="atom_relations", data_type=object, label="Atom relations", is_column=True, has_widget=True, storable=True, widget_type="custom", refinable=True, inh_name="inherit_atom_relations", stor_name="_atom_relations", inh_from="linked_with", class_type=AtomRelation),
            PropIntel(name="layer_atoms", data_type=object, label="Layer atoms", is_column=True, has_widget=True, storable=True, widget_type="custom", inh_name="inherit_layer_atoms", stor_name="_layer_atoms", inh_from="linked_with", class_type=Atom),
            PropIntel(name="interlayer_atoms", data_type=object, label="Interlayer atoms", is_column=True, has_widget=True, storable=True, widget_type="custom", inh_name="inherit_interlayer_atoms", stor_name="_interlayer_atoms", inh_from="linked_with", class_type=Atom),
            PropIntel(name="atoms_changed", data_type=object, is_column=False, storable=False, has_widget=False)
        ]
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
        self._data_object.lattice_d = self._lattice_d

        return self._data_object

    phase = property(DataModel.parent.fget, DataModel.parent.fset)

    # SIGNALS:
    atoms_changed = None

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
    _name = ""
    def get_name(self): return self._name
    def set_name(self, value):
        self._name = value
        self.visuals_changed.emit()

    def get_inherit_ucp_a(self):
        return self._ucp_a.inherited
    def set_inherit_ucp_a(self, value):
        self._ucp_a.inherited = value

    def get_inherit_ucp_b(self):
        return self._ucp_b.inherited
    def set_inherit_ucp_b(self, value):
        self._ucp_b.inherited = value

    def _set_float_data_property(self, name, value):
        try: value = float(value)
        except ValueError: return # ignore faulty values
        setattr(self._data_object, name, value)
        self.data_changed.emit()

    def _set_bool_property(self, name, value):
        try: value = bool(value)
        except ValueError: return # ignore faulty values
        if getattr(self, "_%s" % name) != value:
            with self.data_changed.hold_and_emit():
                setattr(self, "_%s" % name, value)

    _inherit_d001 = False
    def get_inherit_d001(self): return self._inherit_d001
    def set_inherit_d001(self, value): self._set_bool_property("inherit_d001", value)

    _inherit_default_c = False
    def get_inherit_default_c(self): return self._inherit_default_c
    def set_inherit_default_c(self, value): self._set_bool_property("inherit_default_c", value)

    _inherit_delta_c = False
    def get_inherit_delta_c(self): return self._inherit_delta_c
    def set_inherit_delta_c(self, value): self._set_bool_property("inherit_delta_c", value)

    _inherit_layer_atoms = False
    def get_inherit_layer_atoms(self): return self._inherit_layer_atoms
    def set_inherit_layer_atoms(self, value): self._set_bool_property("inherit_layer_atoms", value)

    _inherit_interlayer_atoms = False
    def get_inherit_interlayer_atoms(self): return self._inherit_interlayer_atoms
    def set_inherit_interlayer_atoms(self, value): self._set_bool_property("inherit_interlayer_atoms", value)

    _inherit_atom_relations = False
    def get_inherit_atom_relations(self): return self._inherit_atom_relations
    def set_inherit_atom_relations(self, value): self._set_bool_property("inherit_atom_relations", value)

    _linked_with = None
    _linked_with_index = None
    _linked_with_uuid = None
    def get_linked_with(self): return self._linked_with
    def set_linked_with(self, value):
        if value != self._linked_with:
            if self._linked_with is not None:
                self.relieve_model(self._linked_with)
            self._linked_with = value
            if self._linked_with is not None:
                self.observe_model(self._linked_with)
            else:
                for prop in self.Meta.get_inheritable_properties():
                    setattr(self, "inherit_%s" % prop, False)
            self.data_changed.emit()

    # Lattice d-value
    __lattice_d = 0.0
    @property
    def _lattice_d(self):
        return self.__lattice_d;
    @_lattice_d.setter
    def _lattice_d(self, value):
        try: value = float(value)
        except ValueError: return # ignore faulty values
        if self.__lattice_d != value:
            self.__lattice_d = value
            self.data_changed.emit()

    def get_lattice_d(self): return self._lattice_d


    # INHERITABLE PROPERTIES:
    def _set_inheritable_property_value(self, name, value):
        current = getattr(self, "_%s" % name)
        if current != value:
            with self.data_changed.hold_and_emit():
                if name.startswith("ucp_"):
                    if current is not None:
                        self.relieve_model(current)
                setattr(self, "_%s" % name, value)
                if name.startswith("ucp_"):
                    if value is not None:
                        self.observe_model(value)

    _ucp_a = None
    def get_ucp_a(self): return self._get_inheritable_property_value("ucp_a")
    def set_ucp_a(self, value): self._set_inheritable_property_value("ucp_a", value)

    _ucp_b = None
    def get_ucp_b(self): return self._get_inheritable_property_value("ucp_b")
    def set_ucp_b(self, value): self._set_inheritable_property_value("ucp_b", value)

    _d001 = 1.0
    def get_d001(self): return self._get_inheritable_property_value("d001")
    def set_d001(self, value): self._set_inheritable_property_value("d001", float(value))

    _default_c = 1.0
    def get_default_c(self): return self._get_inheritable_property_value("default_c")
    def set_default_c(self, value): self._set_inheritable_property_value("default_c", float(value))

    _delta_c = 0.0
    def get_delta_c(self): return self._get_inheritable_property_value("delta_c")
    def set_delta_c(self, value): self._set_inheritable_property_value("delta_c", float(value))

    _layer_atoms = []
    def get_layer_atoms(self): return self._get_inheritable_property_value("layer_atoms")
    def set_layer_atoms(self, value):
        with self.data_changed.hold_and_emit():
            self._layer_atoms = value

    _interlayer_atoms = []
    def get_interlayer_atoms(self): return self._get_inheritable_property_value("interlayer_atoms")
    def set_interlayer_atoms(self, value):
        with self.data_changed.hold_and_emit():
            self._interlayer_atoms = value

    _atom_relations = []
    def get_atom_relations(self): return self._get_inheritable_property_value("atom_relations")
    def set_atom_relations(self, value):
        with self.data_changed.hold_and_emit():
            self._atom_relations = value

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
            "data_atom_ratios", "data_d001", "data_default_c", "data_delta_c",
            "data_cell_a", "data_ucp_a", "data_cell_b", "data_ucp_b",
            "linked_with_uuid", "linked_with_index", "inherit_cell_a", "inherit_cell_b",
            *[names[0] for names in type(self).Meta.get_local_storable_properties()]
        )
        super(Component, self).__init__(**kwargs)
        kwargs = my_kwargs

        # Setup signals:
        self.atoms_changed = HoldableSignal()

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
        self.d001 = self.get_kwarg(kwargs, self._d001, "d001", "data_d001")
        self._default_c = float(self.get_kwarg(kwargs, self._d001, "default_c", "data_default_c"))
        self.delta_c = float(self.get_kwarg(kwargs, self._delta_c, "delta_c", "data_delta_c"))
        self.update_lattice_d()

        # Set/Create & observe unit cell properties:
        ucp_a = self.get_kwarg(kwargs, None, "ucp_a", "data_ucp_a", "data_cell_a")
        if isinstance(ucp_a, float):
            ucp_a = UnitCellProperty(name="cell length a", value=ucp_a, parent=self)
        self._ucp_a = self.parse_init_arg(
            ucp_a, UnitCellProperty, child=True,
            default_is_class=True, name="Cell length a [nm]", parent=self
        )
        self.observe_model(self._ucp_a)

        ucp_b = self.get_kwarg(kwargs, None, "ucp_b", "data_ucp_b", "data_cell_b")
        if isinstance(ucp_b, float):
            ucp_b = UnitCellProperty(name="cell length b", value=ucp_b, parent=self)
        self._ucp_b = self.parse_init_arg(
            ucp_b, UnitCellProperty, child=True,
            default_is_class=True, name="Cell length b [nm]", parent=self
        )
        self.observe_model(self._ucp_b)

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
        for atom in self.layer_atoms:
            atom.resolve_json_references()
        for atom in self.interlayer_atoms:
            atom.resolve_json_references()

        self._ucp_a.resolve_json_references()
        self._ucp_a.update_value()
        self._ucp_b.resolve_json_references()
        self._ucp_b.update_value()

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
                if prop.inh_name:
                    retval[prop.inh_name] = False
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
            self._lattice_d = float(max(self.lattice_d, atom.default_z))

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
