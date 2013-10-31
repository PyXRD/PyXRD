# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import zipfile
from warnings import warn

from pyxrd.gtkmvc.model import Model, Observer

from pyxrd.generic.io import storables, Storable
from pyxrd.generic.models import DataModel, PropIntel
from pyxrd.generic.models.mixins import ObjectListStoreChildMixin, ObjectListStoreParentMixin
from pyxrd.generic.models.treemodels import ObjectListStore
from pyxrd.generic.models.metaclasses import pyxrd_object_pool
from pyxrd.generic.calculations.components import get_factors
from pyxrd.generic.calculations.data_objects import ComponentData
from pyxrd.generic.refinement.mixins import RefinementGroup

from pyxrd.atoms.models import Atom
from .atom_relations import AtomRelation, AtomRatio
from .unit_cell_prop import UnitCellProperty

@storables.register()
class Component(DataModel, Storable, ObjectListStoreChildMixin,
        ObjectListStoreParentMixin, RefinementGroup):

    # MODEL INTEL:
    __parent_alias__ = "phase"
    __model_intel__ = [
        PropIntel(name="name", data_type=unicode, label="Name", is_column=True, has_widget=True, storable=True),
        PropIntel(name="linked_with", data_type=object, label="Linked with", widget_type='custom', is_column=True, has_widget=True),
        PropIntel(name="d001", data_type=float, label="Cell length c [nm]", is_column=True, has_widget=True, storable=True, refinable=True, minimum=0.0, maximum=5.0, inh_name="inherit_d001", stor_name="_d001"),
        PropIntel(name="default_c", data_type=float, label="Default c length [nm]", is_column=True, has_widget=True, storable=True, minimum=0.0, maximum=5.0, inh_name="inherit_default_c", stor_name="_default_c"),
        PropIntel(name="delta_c", data_type=float, label="C length dev. [nm]", is_column=True, has_widget=True, storable=True, refinable=True, minimum=0.0, maximum=0.05, inh_name="inherit_delta_c", stor_name="_delta_c"),
        PropIntel(name="ucp_a", data_type=object, label="Cell length a [nm]", is_column=True, has_widget=True, storable=True, refinable=True, inh_name="inherit_ucp_a", stor_name="_ucp_a"),
        PropIntel(name="ucp_b", data_type=object, label="Cell length b [nm]", is_column=True, has_widget=True, storable=True, refinable=True, inh_name="inherit_ucp_b", stor_name="_ucp_b"),
        PropIntel(name="inherit_d001", data_type=bool, label="Inh. cell length c", is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_ucp_b", data_type=bool, label="Inh. cell length b", is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_ucp_a", data_type=bool, label="Inh. cell length a", is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_default_c", data_type=bool, label="Inh. default length c", is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_delta_c", data_type=bool, label="Inh. c length dev.", is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_layer_atoms", data_type=bool, label="Inh. layer atoms", is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_interlayer_atoms", data_type=bool, label="Inh. interlayer atoms", is_column=True, has_widget=True, storable=True),
        PropIntel(name="inherit_atom_relations", data_type=bool, label="Inh. atom relations", is_column=True, has_widget=True, storable=True),
        PropIntel(name="atom_relations", data_type=object, label="Atom relations", is_column=True, has_widget=True, storable=True, widget_type="custom", refinable=True, inh_name="inherit_atom_relations", stor_name="_atom_relations"),
        PropIntel(name="layer_atoms", data_type=object, label="Layer atoms", is_column=True, has_widget=True, storable=True, widget_type="custom", inh_name="inherit_layer_atoms", stor_name="_layer_atoms"),
        PropIntel(name="interlayer_atoms", data_type=object, label="Interlayer atoms", is_column=True, has_widget=True, storable=True, widget_type="custom", inh_name="inherit_interlayer_atoms", stor_name="_interlayer_atoms"),
    ]
    __store_id__ = "Component"

    _data_object = None
    @property
    def data_object(self):
        weight = 0.0

        self._data_object.layer_atoms = [None] * len(self.layer_atoms)
        for i, atom in enumerate(self.layer_atoms.iter_objects()):
            self._data_object.layer_atoms[i] = atom.data_object
            weight += atom.weight

        self._data_object.interlayer_atoms = [None] * len(self.interlayer_atoms)
        for i, atom in enumerate(self.interlayer_atoms.iter_objects()):
            self._data_object.interlayer_atoms[i] = atom.data_object
            weight += atom.weight

        self._data_object.volume = self.get_volume()
        self._data_object.weight = weight
        self._data_object.d001 = self.d001
        self._data_object.default_c = self.default_c
        self._data_object.delta_c = self.delta_c
        self._data_object.lattice_d = self._lattice_d

        return self._data_object

    # PROPERTIES:
    _name = ""
    def get_name_value(self): return self._name
    def set_name_value(self, value):
        self._name = value
        self.visuals_changed.emit()
        self.liststore_item_changed()

    @property
    def _inherit_ucp_a(self):
        return self._ucp_a.inherited
    @_inherit_ucp_a.setter
    def _inherit_ucp_a(self, value):
        self._ucp_a.inherited = value
    @property
    def _inherit_ucp_b(self):
        return self._ucp_b.inherited
    @_inherit_ucp_b.setter
    def _inherit_ucp_b(self, value):
        self._ucp_b.inherited = value

    _inherit_d001 = False
    _inherit_default_c = False
    _inherit_delta_c = False
    _inherit_layer_atoms = False
    _inherit_interlayer_atoms = False
    _inherit_atom_relations = False
    @Model.getter(*[prop.inh_name for prop in __model_intel__ if prop.inh_name])
    def get_inherit_prop(self, prop_name): return getattr(self, "_%s" % prop_name)
    @Model.setter(*[prop.inh_name for prop in __model_intel__ if prop.inh_name])
    def set_inherit_prop(self, prop_name, value):
        try: value = bool(value)
        except ValueError: return # ignore faulty values
        current = getattr(self, "_%s" % prop_name)
        if current != value:
            with self.data_changed.hold_and_emit():
                setattr(self, "_%s" % prop_name, value)
                self.liststore_item_changed()

    _linked_with = None
    _linked_with_index = None
    _linked_with_uuid = None
    def get_linked_with_value(self): return self._linked_with
    def set_linked_with_value(self, value):
        if value != self._linked_with:
            if self._linked_with != None:
                self.relieve_model(self._linked_with)
            self._linked_with = value
            if self._linked_with != None:
                self.observe_model(self._linked_with)
            else:
                for prop in self.__inheritables__:
                    setattr(self, "inherit_%s" % prop, False)
            self.liststore_item_changed()
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
    lattice_d = property(_lattice_d.fget, None, None, "The lattice d-value for this component")


    # INHERITABLE PROPERTIES:
    _ucp_a = None
    _ucp_b = None
    _d001 = 1.0
    _default_c = 1.0
    _delta_c = 0.0
    _layer_atoms = None
    _interlayer_atoms = None
    _atom_relations = None
    @Model.getter(*[prop.name for prop in __model_intel__ if prop.inh_name])
    def get_inheritable(self, prop_name):
        inh_name = "inherit_%s" % prop_name
        if self.linked_with != None and getattr(self, inh_name):
            return getattr(self.linked_with, prop_name)
        else:
            return getattr(self, "_%s" % prop_name)
    @Model.setter(*[prop.name for prop in __model_intel__ if prop.inh_name])
    def set_inheritable(self, prop_name, value):
        current = getattr(self, "_%s" % prop_name)
        if current != value:
            with self.data_changed.hold_and_emit():
                if prop_name.startswith("ucp_"):
                    if current != None:
                        self.relieve_model(current)
                setattr(self, "_%s" % prop_name, value)
                if prop_name.startswith("ucp_"):
                    if value != None:
                        self.observe_model(value)
                if prop_name == "default_c":
                    setattr(self, "_%s" % prop_name, float(value))
                    for atom in self.interlayer_atoms.iter_objects():
                        atom.liststore_item_changed() # default_c influences calculated Z values
                self.liststore_item_changed()

    # Instance flag indicating whether or not linked_with & inherit flags should be saved
    save_links = True
    # Class flag indicating whether or not atom types in the component should be
    # exported using their name rather then their project-uuid.
    export_atom_types = False

    # REFINEMENT GROUP IMPLEMENTATION:
    @property
    def refine_title(self):
        return self.name

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, name=None, ucp_a=None, ucp_b=None,
                 d001=None, default_c=None, delta_c=None,
                 layer_atoms=None, interlayer_atoms=None, atom_relations=None,
                 inherit_ucp_a=False, inherit_ucp_b=False, inherit_d001=False,
                 inherit_default_c=False, inherit_delta_c=False,
                 inherit_layer_atoms=False, inherit_interlayer_atoms=False, inherit_atom_relations=False,
                 linked_with_index=None, linked_with_uuid=None, parent=None, **kwargs):
        super(Component, self).__init__(parent=parent)

        # Set up data object
        self._data_object = ComponentData(
            d001=0.0,
            delta_c=0.0
        )

        # Set attributes:
        self.name = name or self.get_depr(kwargs, self.name, "data_name")

        layer_atoms = layer_atoms or self.get_depr(kwargs, None, "data_layer_atoms")
        self._layer_atoms = self.parse_liststore_arg(layer_atoms, ObjectListStore, Atom)
        interlayer_atoms = interlayer_atoms or self.get_depr(kwargs, None, "data_interlayer_atoms")
        self._interlayer_atoms = self.parse_liststore_arg(interlayer_atoms, ObjectListStore, Atom)

        atom_relations = atom_relations or self.get_depr(kwargs, None, "data_atom_relations")
        self._atom_relations = self.parse_liststore_arg(atom_relations, ObjectListStore, AtomRelation)

        atom_ratios = kwargs.get("atom_ratios", kwargs.get("data_atom_ratios", None))
        if atom_ratios != None:
            for json_ratio in atom_ratios["properties"]["model_data"]:
                props = json_ratio["properties"]

                ratio = AtomRatio(
                    name=props.get("name", props.get("data_name", "")),
                    value=props.get("ratio", props.get("data_ratio", 0.0)),
                    sum=props.get("sum", props.get("data_sum", 0.0)),
                    prop1=props.get("prop1", props.get("data_prop1", None)),
                    prop2=props.get("prop2", props.get("data_prop2", None)),
                    parent=self)
                self._atom_relations.append(ratio)

        for atom in self._interlayer_atoms.iter_objects():
            atom.stretch_values = True
            self.observe_model(atom)

        for atom in self._layer_atoms.iter_objects():
            self.observe_model(atom)

        for relation in self._atom_relations.iter_objects():
            relation.resolve_relations()
            self.observe_model(relation)

        self._layer_atoms.connect("item-inserted", self.on_layer_atom_inserted)
        self._layer_atoms.connect("item-removed", self.on_layer_atom_removed)

        self._interlayer_atoms.connect("item-inserted", self.on_interlayer_atom_inserted)
        self._interlayer_atoms.connect("item-removed", self.on_interlayer_atom_removed)

        self._atom_relations.connect("item-removed", self.on_atom_relation_removed)
        self._atom_relations.connect("item-inserted", self.on_atom_relation_inserted)

        self._d001 = d001 or self.get_depr(kwargs, self.d001, "data_d001")

        self._default_c = float(default_c or self.get_depr(kwargs, self._d001, "data_default_c"))
        self._delta_c = delta_c or self.get_depr(kwargs, self._delta_c, "data_delta_c")
        self.update_lattice_d()

        ucp_a = ucp_a or self.get_depr(kwargs, None, "data_ucp_a", "data_cell_a")
        if isinstance(ucp_a, float):
            ucp_a = UnitCellProperty(name="cell length a", value=ucp_a, parent=self)
            inherit_ucp_a = kwargs.pop("inherit_cell_a", inherit_ucp_a)
        self._ucp_a = self.parse_init_arg(ucp_a, UnitCellProperty(parent=self, name="Cell length a [nm]"), child=True, name="Cell length a [nm]")
        self.observe_model(self._ucp_a)

        ucp_b = ucp_b or self.get_depr(kwargs, None, "data_ucp_b", "data_cell_b")
        if isinstance(ucp_b, float):
            ucp_b = UnitCellProperty(name="cell length b", value=ucp_b, parent=self)
            inherit_ucp_b = kwargs.pop("inherit_cell_b", inherit_ucp_b)
        self._ucp_b = self.parse_init_arg(ucp_b, UnitCellProperty(parent=self, name="Cell length b [nm]"), child=True, name="Cell length b [nm]")
        self.observe_model(self._ucp_b)

        self._linked_with_uuid = linked_with_uuid if linked_with_uuid != None else ""
        self._linked_with_index = linked_with_index if linked_with_index > -1 else None

        self._inherit_d001 = inherit_d001
        self._inherit_ucp_a = inherit_ucp_a
        self._inherit_ucp_b = inherit_ucp_b
        self._inherit_default_c = inherit_default_c
        self._inherit_delta_c = inherit_delta_c
        self._inherit_layer_atoms = inherit_layer_atoms
        self._inherit_interlayer_atoms = inherit_interlayer_atoms
        self._inherit_atom_relations = inherit_atom_relations

    def __str__(self):
        return ("<Component %s" % self.name) + \
            (" linked with %s>" % self.linked_with if self.linked_with else ">")

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Observer.observe("data_changed", signal=True)
    def on_data_model_changed(self, model, prop_name, info):
        # Check whether the changed model is an AtomRelation or Atom, if so
        # re-apply the atom_relations.
        with self.data_changed.hold():
            if isinstance(model, AtomRelation) or isinstance(model, Atom):
                self.apply_atom_relations()
                self.update_ucp_values()
            if isinstance(model, UnitCellProperty):
                self.update_ucp_values()

    @Observer.observe("removed", signal=True)
    def on_data_model_removed(self, model, prop_name, info):
        # Check whether the removed component is linked with this one, if so
        # clears the link and emits the data_changed signal.
        if model != self and self.linked_with != None and self.linked_with == model:
            with self.data_changed.hold_and_emit():
                self.linked_with = None

    def on_layer_atom_inserted(self, model, atom):
        """Sets the atoms parent and stretch_values property,
        updates the components lattice d-value, and emits a data_changed signal"""
        with self.data_changed.hold_and_emit():
            atom.parent = self
            atom.stretch_values = False
            self.observe_model(atom)
            self.update_lattice_d()

    def on_layer_atom_removed(self, model, atom):
        """Clears the atoms parent, updates the components lattice d-value, and
        emits a data_changed signal"""
        with self.data_changed.hold_and_emit():
            self.relieve_model(atom)
            atom.parent = None
            self.update_lattice_d()

    def on_interlayer_atom_inserted(self, model, atom):
        """Sets the atoms parent and stretch_values property, 
        and emits a data_changed signal"""
        with self.data_changed.hold_and_emit():
            atom.stretch_values = True
            atom.parent = self
    def on_interlayer_atom_removed(self, model, atom):
        """Clears the atoms parent property, 
        and emits a data_changed signal"""
        with self.data_changed.hold_and_emit():
            atom.parent = None

    def on_atom_relation_inserted(self, model, item):
        item.parent = self
        self.observe_model(item)
        self.apply_atom_relations()
    def on_atom_relation_removed(self, model, item):
        self.relieve_model(item)
        item.parent = None
        self.apply_atom_relations()

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def resolve_json_references(self):
        for atom in self._layer_atoms._model_data:
            atom.resolve_json_references()
        for atom in self._interlayer_atoms._model_data:
            atom.resolve_json_references()

        self._ucp_a.resolve_json_references()
        self._ucp_a.update_value()
        self._ucp_b.resolve_json_references()
        self._ucp_b.update_value()

        if self._linked_with_uuid:
            self.linked_with = pyxrd_object_pool.get_object(self._linked_with_uuid)
        elif self._linked_with_index != None and self._linked_with_index != -1:
            warn("The use of object indeces is deprected since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
            self.linked_with = self.parent.based_on.components.get_user_from_index(self._linked_with_index)
        del self._linked_with_uuid
        del self._linked_with_index

    @classmethod
    def save_components(cls, components, filename):
        """
            Saves multiple components to a single file.
        """
        pyxrd_object_pool.change_all_uuids()
        Component.export_atom_types = True
        for comp in components:
            comp.save_links = False
        with zipfile.ZipFile(filename, 'w') as zfile:
            for component in components:
                zfile.writestr(component.uuid, component.dump_object())
        for comp in components:
            comp.save_links = True
        Component.export_atom_types = False

    @classmethod
    def load_components(cls, filename, parent=None):
        """
            Returns multiple components loaded from a single file.
        """
        pyxrd_object_pool.change_all_uuids()
        if zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename, 'r') as zfile:
                for uuid in zfile.namelist():
                    yield cls.load_object(zfile.open(uuid), parent=parent)
        else:
            yield cls.load_object(filename, parent=parent)

    def json_properties(self):
        if self.phase == None or not self.save_links:
            retval = Storable.json_properties(self)
            for prop in self.__model_intel__:
                if prop.inh_name:
                    retval[prop.inh_name] = False
        else:
            retval = Storable.json_properties(self)
            retval["linked_with_uuid"] = self.linked_with.uuid if self.linked_with != None else ""
        return retval

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_factors(self, range_stl):
        return get_factors(range_stl, self.data_object)

    def get_interlayer_stretch_factors(self):
        z_factor = (self.cell_c - self.lattice_d) / (self.default_c - self.lattice_d)
        return self.lattice_d, z_factor

    def update_lattice_d(self):
        """
            Updates the lattice_d attribute for this component. 
            Should normally not be called from outside the component.
        """
        for atom in self.layer_atoms.iter_objects():
            self._lattice_d = float(max(self.lattice_d, atom.default_z))

    def apply_atom_relations(self):
        """
            Applies the atom relation rules in this component.
            Should normally not be called from outside the component.
        """
        with self.data_changed.hold_and_emit():
            for relation in self.atom_relations.iter_objects():
                relation.apply_relation()

    def update_ucp_values(self):
        with self.data_changed.hold():
            for ucp in [self._ucp_a, self._ucp_b]:
                ucp.update_value()

    @property
    def cell_a(self):
        return self._ucp_a.value
    @property
    def cell_b(self):
        return self._ucp_b.value
    @property
    def cell_c(self):
        return self.d001

    def get_volume(self):
        return max(self.cell_a * self.cell_b * self.cell_c, 1e-25)

    def get_weight(self):
        weight = 0
        for atom in (self.layer_atoms._model_data + self.interlayer_atoms._model_data):
            weight += atom.weight
        return weight
