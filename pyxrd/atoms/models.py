# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from functools import partial
from warnings import warn
import zipfile

from pyxrd.mvc import Observer, PropIntel

import numpy as np

from pyxrd.generic.io import storables, Storable, get_case_insensitive_glob
from pyxrd.generic.models import DataModel
from pyxrd.generic.models.mixins import CSVMixin
from pyxrd.generic.calculations.data_objects import AtomTypeData, AtomData
from pyxrd.generic.calculations.atoms import get_atomic_scattering_factor, get_structure_factor

@storables.register()
class AtomType(DataModel, Storable, CSVMixin):
    """
        AtomType models contain all physical & chemical information for one element 
        in a certain state (e.g. Fe3+ & Fe2+ are two different AtomTypes)
        
        AtomTypes have built-in support for `generic.models.treemodels.ObjectIndexStore`
        
        Attributes:
            atom_nr: integer, the atomic number or a unique number if a compound
            name: string, the atom type name (e.g. Al3+)
            charge: integer, the charge of the 'atom' (eg. 3 for Al3+)
            weight: float, the atomic weight
            debye: float, Debye-Waller scattering factor
            par_aN, par_bN and par_c: the atomic scattering factor parameters with N=[0:5]
            data_object: the internal data object that is used in the
                calculations framework (see `generic.calculations.atoms`) 
    """

    # MODEL METADATA:
    class Meta(DataModel.Meta):
        store_id = "AtomType"
        properties = [
            PropIntel(name="atom_nr", label="Atom Nr", data_type=int, widget_type="entry", **PropIntel.ST_WID_COL),
            PropIntel(name="name", label="Name", data_type=unicode, **PropIntel.ST_WID_COL),
            PropIntel(name="charge", label="Charge", data_type=float, widget_type="float_entry", **PropIntel.ST_WID_COL),
            PropIntel(name="weight", label="Atomic weight", data_type=float, widget_type="float_entry", **PropIntel.ST_WID_COL),
            PropIntel(name="debye", label="Debye-Waller factor", data_type=float, widget_type="float_entry", **PropIntel.ST_WID_COL),
            PropIntel(name="par_c", label="c", data_type=float, widget_type="float_entry", **PropIntel.ST_WID_COL),
        ] + [
            PropIntel(name="par_a%d" % i, label="a%d" % i, data_type=float, widget_type="float_entry", **PropIntel.ST_WID_COL) for i in xrange(1, 6)
        ] + [
            PropIntel(name="par_b%d" % i, label="b%d" % i, data_type=float, widget_type="float_entry", **PropIntel.ST_WID_COL) for i in xrange(1, 6)
        ]
        csv_storables = [(prop.name, prop.name) for prop in properties if prop.storable]

        file_filters = [
            ("Atom types CSV file", get_case_insensitive_glob("*.atl")),
            ("Atom types JSON file", get_case_insensitive_glob("*.ztl"))
        ]

    project = property(DataModel.parent.fget, DataModel.parent.fset)

    # SIGNALS:
    data_changed = None
    visuals_changed = None

    # PROPERTIES:
    _name = ""
    @property
    def name(self):
        return getattr(self, "_name")
    @name.setter
    def name(self, value):
        self._name = value
        self.visuals_changed.emit()

    atom_nr = 0

    _data_object = None
    @property
    def data_object(self):
        return self._data_object

    def __get_par_a(self, index):
        return self._data_object.par_a[index]

    def __set_par_a(self, value, index):
        assert (index >= 0 and index < 5)
        try: value = float(value)
        except ValueError: return # ignore faulty values
        self._data_object.par_a[index] = value
        self.data_changed.emit()

    def __get_par_b(self, index):
        return self._data_object.par_b[index]

    def __set_par_b(self, value, index):
        assert (index >= 0 and index < 5)
        try: value = float(value)
        except ValueError: return # ignore faulty values
        self._data_object.par_b[index] = value
        self.data_changed.emit()

    def _set_float_data_property(self, value, name):
        try: value = float(value)
        except ValueError: raise # ignore faulty values
        setattr(self._data_object, name, value)
        self.data_changed.emit()

    par_a1 = property(fget=partial(__get_par_a, index=0), fset=partial(__set_par_a, index=0))
    par_a2 = property(fget=partial(__get_par_a, index=1), fset=partial(__set_par_a, index=1))
    par_a3 = property(fget=partial(__get_par_a, index=2), fset=partial(__set_par_a, index=2))
    par_a4 = property(fget=partial(__get_par_a, index=3), fset=partial(__set_par_a, index=3))
    par_a5 = property(fget=partial(__get_par_a, index=4), fset=partial(__set_par_a, index=4))

    par_b1 = property(fget=partial(__get_par_b, index=0), fset=partial(__set_par_b, index=0))
    par_b2 = property(fget=partial(__get_par_b, index=1), fset=partial(__set_par_b, index=1))
    par_b3 = property(fget=partial(__get_par_b, index=2), fset=partial(__set_par_b, index=2))
    par_b4 = property(fget=partial(__get_par_b, index=3), fset=partial(__set_par_b, index=3))
    par_b5 = property(fget=partial(__get_par_b, index=4), fset=partial(__set_par_b, index=4))

    @property
    def par_c(self): return self._data_object.par_c
    @par_c.setter
    def par_c(self, value): self._set_float_data_property(value, "par_c")

    @property
    def debye(self): return self._data_object.debye
    @debye.setter
    def debye(self, value): self._set_float_data_property(value, "debye")

    @property
    def charge(self): return self._data_object.charge
    @charge.setter
    def charge(self, value): self._set_float_data_property(value, "charge")

    @property
    def weight(self): return self._data_object.weight
    @weight.setter
    def weight(self, value): self._set_float_data_property(value, "weight")

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):

        keys = [ "data_%s" % names[0] for names in type(self).Meta.get_local_storable_properties()]
        keys.extend([ names[0] for names in type(self).Meta.get_local_storable_properties()])
        my_kwargs = self.pop_kwargs(kwargs, * keys)
        super(AtomType, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        # Set up data object
        self._data_object = AtomTypeData(
            par_a=np.zeros(shape=(5,), dtype=float),
            par_b=np.zeros(shape=(5,), dtype=float),
            par_c=0.0,
            debye=0.0,
            charge=0.0,
            weight=0.0
        )

        # Set attributes:
        self.name = str(self.get_kwarg(kwargs, "", "name", "data_name"))
        self.atom_nr = int(self.get_kwarg(kwargs, 0, "atom_nr", "data_atom_nr"))
        self.weight = float(self.get_kwarg(kwargs, 0, "weight", "data_weight"))
        self.charge = float(self.get_kwarg(kwargs, 0, "charge", "data_charge"))
        self.debye = float(self.get_kwarg(kwargs, 0, "debye", "data_debye"))

        for kw in ["par_a%d" % i for i in xrange(1, 6)] + ["par_b%d" % i for i in xrange(1, 6)] + ["par_c"]:
            setattr(
                self, kw, self.get_kwarg(kwargs, 0.0, kw, "data_%s" % kw)
            )

    def __str__(self):
        return "<AtomType %s (%s)>" % (self.name, id(self))

    def get_atomic_scattering_factors(self, stl_range):
        angstrom_range = ((stl_range * 0.05) ** 2)
        return get_atomic_scattering_factor(angstrom_range, self.data_object)

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    @classmethod
    def load_atom_types(cls, filename, parent=None):
        """
            Returns multiple AtomTypes loaded from a single (JSON) file.
        """
        type(cls).object_pool.change_all_uuids()

        if zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename, 'r') as zfile:
                for name in zfile.namelist():
                    yield cls.load_object(zfile.open(name), parent=parent)
        else:
            yield cls.load_object(filename, parent=parent)

    @classmethod
    def save_atom_types(cls, atom_types, filename):
        """
            Saves multiple AtomTypes to a single (JSON) file.
        """
        type(cls).object_pool.change_all_uuids()

        with zipfile.ZipFile(filename, 'w') as zfile:
            for i, atom_type in enumerate(atom_types):
                zfile.writestr("%d###%s" % (i, atom_type.uuid), atom_type.dump_object())

    pass # end of class

@storables.register()
class Atom(DataModel, Storable):
    """
        Atoms have an atom type plus structural parameters (position and proportion)
    """

    # MODEL METADATA:
    class Meta(DataModel.Meta):
        store_id = "Atom"
        properties = [ # TODO add labels
            PropIntel(name="name", data_type=unicode, **PropIntel.ST_WID_COL),
            PropIntel(name="default_z", data_type=float, **PropIntel.ST_WID_COL),
            PropIntel(name="z", data_type=float, **PropIntel.WID_COL),
            PropIntel(name="pn", data_type=float, **PropIntel.ST_WID_COL),
            PropIntel(name="atom_type", data_type=object, **PropIntel.WID_COL),
            PropIntel(name="stretch_values", data_type=bool),
        ]
        layer_filters = [
            ("Layer file", get_case_insensitive_glob("*.lyr")),
        ]

    _data_object = None
    @property
    def data_object(self):
        if self.atom_type is not None:
            self._data_object.atom_type = self.atom_type.data_object
        return self._data_object

    component = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:
    _name = ""
    @property
    def name(self): return self._name
    @name.setter
    def name(self, value):
        self._name = value
        self.visuals_changed.emit()

    _sf_array = None
    _atom_array = None

    _default_z = None
    def get_default_z(self):
        return self._data_object.default_z
    def set_default_z(self, value):
        try: value = float(value)
        except ValueError: return
        if value != self._data_object.default_z:
            self._data_object.default_z = value
            self.data_changed.emit()

    _stretch_z = False
    def get_stretch_values(self): return bool(self._stretch_z)
    def set_stretch_values(self, value):
        try: value = bool(value)
        except ValueError: return
        if value != self._stretch_z:
            self._stretch_z = value
            self.data_changed.emit()

    @property
    def z(self):
        if self.stretch_values and self.component is not None:
            lattice_d, factor = self.component.get_interlayer_stretch_factors()
            return float(lattice_d + (self.default_z - lattice_d) * factor)
        return self.default_z
    @z.setter
    def z(self, value):
        warn("The z property can not be set!", DeprecationWarning)

    _pn = None
    def get_pn(self): return self._data_object.pn
    def set_pn(self, value):
        try: value = float(value)
        except ValueError: return
        if value != self._data_object.pn:
            self._data_object.pn = value
            self.data_changed.emit()

    @property
    def weight(self):
        if self.atom_type is not None:
            return self.pn * self.atom_type.weight
        else:
            return 0.0

    _atom_type_index = None
    _atom_type_uuid = None
    _atom_type = None
    _atom_type_name = None
    def get_atom_type(self): return self._atom_type
    def set_atom_type(self, value):
        if self._atom_type != value: # prevent spurious events
            with self.data_changed.hold_and_emit():
                if self._atom_type is not None:
                    self.relieve_model(self._atom_type)
                self._atom_type = value
                if self._atom_type is not None:
                    self.observe_model(self._atom_type)

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        my_kwargs = self.pop_kwargs(kwargs,
            "data_name", "data_z", "z", "data_pn", "data_atom_type",
            "atom_type_uuid", "atom_type_name", "atom_type_index",
            *[names[0] for names in type(self).Meta.get_local_storable_properties()]
        )
        super(Atom, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        # Set up data object
        self._data_object = AtomData(
            default_z=0.0,
            pn=0.0
        )

        # Set attributes
        self.name = str(self.get_kwarg(kwargs, "", "name", "data_name"))

        self.stretch_values = bool(self.get_kwarg(kwargs, False, "stretch_values"))
        self.default_z = float(self.get_kwarg(kwargs, 0.0, "default_z", "data_z", "z"))
        self.pn = float(self.get_kwarg(kwargs, 0.0, "pn", "data_pn"))

        self.atom_type = self.get_kwarg(kwargs, None, "atom_type", "data_atom_type")
        self._atom_type_uuid = self.get_kwarg(kwargs, None, "atom_type_uuid")
        self._atom_type_name = self.get_kwarg(kwargs, None, "atom_type_name")
        self._atom_type_index = self.get_kwarg(kwargs, None, "atom_type_index")

    def __str__(self):
        return "<Atom %s(%s)>" % (self.name, repr(self))

    def _unattach_parent(self):
        self.atom_type = None
        super(Atom, self)._unattach_parent()

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Observer.observe("removed", signal=True)
    def on_removed(self, model, prop_name, info):
        """
            This method observes the Atom types 'removed' signal,
            as such, if the AtomType gets removed from the parent project,
            it is also cleared from this Atom
        """
        if model == self.atom_type:
            self.atom_type = None

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def get_structure_factors(self, stl_range):
        if self.atom_type is not None:
            return float(get_structure_factor(stl_range, self.data_object))
        else:
            return 0.0

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def resolve_json_references(self):
        if getattr(self, "_atom_type_uuid", None) is not None:
            self.atom_type = type(type(self)).object_pool.get_object(self._atom_type_uuid)
        if self.atom_type is None and \
                getattr(self, "_atom_type_name", None) is not None or \
                getattr(self, "_atom_type_index", None) is not None:
            assert(self.component is not None)
            assert(self.component.phase is not None)
            assert(self.component.phase.project is not None)
            if getattr(self, "_atom_type_name", None) is not None:
                for atom_type in self.component.phase.project.atom_types:
                    if atom_type.name == self._atom_type_name:
                        self.atom_type = atom_type
            else:
                warn("The use of object indeces is deprected since version 0.4. \
                    Please switch to using object UUIDs.", DeprecationWarning)
                self.atom_type = self.component.phase.project.atom_types.get_user_data_from_path((self._atom_type_index,))
        self._atom_type_uuid = None
        self._atom_type_name = None
        self._atom_type_index = None

    def json_properties(self):
        retval = super(Atom, self).json_properties()
        if self.component is None or self.component.export_atom_types:
            retval["atom_type_name"] = self.atom_type.name if self.atom_type is not None else ""
        else:
            retval["atom_type_uuid"] = self.atom_type.uuid if self.atom_type is not None else ""
        return retval

    @staticmethod
    def get_from_csv(filename, callback=None, parent=None):
        import csv
        atl_reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"') # TODO create csv dialect!
        header = True
        atoms = []

        types = dict()
        if parent is not None:
            for atom_type in parent.phase.project.atom_types._data:
                if not atom_type.name in types:
                    types[atom_type.name] = atom_type

        for row in atl_reader:
            if not header and len(row) >= 4:
                if len(row) == 5:
                    name, z, def_z, pn, atom_type = row[0], float(row[1]), float(row[2]), float(row[3]), types[row[4]] if parent is not None else None
                else:
                    name, z, pn, atom_type = row[0], float(row[1]), float(row[2]), types[row[3]] if parent is not None else None
                    def_z = z

                if atom_type in types:
                    atom_type = types[atom_type]

                new_atom = Atom(name=name, z=z, default_z=def_z, pn=pn, atom_type=atom_type, parent=parent)
                atoms.append(new_atom)
                if callback is not None and callable(callback):
                    callback(new_atom)
                del new_atom

            header = False
        return atoms

    @staticmethod
    def save_as_csv(filename, atoms):
        import csv
        atl_writer = csv.writer(open(filename, 'wb'), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        atl_writer.writerow(["Atom", "z", "def_z", "pn", "Element"])
        for item in atoms:
            if item is not None and item.atom_type is not None:
                atl_writer.writerow([item.name, item.z, item.default_z, item.pn, item.atom_type.name])

    pass # end of class

