# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from functools import partial
from warnings import warn

import numpy as np

from pyxrd.generic.io import storables, Storable, get_case_insensitive_glob
from pyxrd.generic.models import DataModel
from pyxrd.generic.models.mixins import CSVMixin
from pyxrd.calculations.data_objects import AtomTypeData, AtomData
from pyxrd.calculations.atoms import get_atomic_scattering_factor, get_structure_factor

from mvc import Observer
from mvc.models.properties.string_properties import StringProperty
from mvc.models.properties.signal_mixin import SignalMixin
from mvc.models.properties.float_properties import FloatProperty
from mvc.models.properties.bool_property import BoolProperty
from mvc.models.properties.read_only_mixin import ReadOnlyMixin
from mvc.models.properties.labeled_property import LabeledProperty
from mvc.models.properties.integer_properties import IntegerProperty

@storables.register()
class AtomType(CSVMixin, DataModel, Storable):
    """
    An AtomType model contains all the physical & chemical information for 
    one ion, e.g. Fe3+ & Fe2+ are two different AtomTypes.
    """

    # MODEL METADATA:
    class Meta(DataModel.Meta):
        store_id = "AtomType"

    #: The project this AtomType belongs to or None. Effectively an alias for `parent`.
    project = property(DataModel.parent.fget, DataModel.parent.fset)

    _data_object = None
    @property
    def data_object(self):
        """
        The data object that is used in the calculations framework 
        (see :mod:`pyxrd.generic.calculations.atoms`).
        Is an instance of :class:`~pyxrd.generic.calculations.data_objects.AtomTypeData`
        """

        self._data_object.par_c = self.par_c
        self._data_object.debye = self.debye
        self._data_object.charge = self.charge
        self._data_object.weight = self.weight

        return self._data_object

    #: Name of the AtomType (e.g. :math:`Fe^{2+}`)
    name = StringProperty(
        default="", text="Name",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: The atomic number, or an arbitrarily high number (+300) for compounds
    atom_nr = IntegerProperty(
        default=0, text="Atom Nr",
        visible=True, persistent=True,
        widget_type="entry"
    )

    def __get_par_a(self, index=0):
        return self._data_object.par_a[index]

    def __set_par_a(self, value, index=0):
        assert (index >= 0 and index < 5)
        self._data_object.par_a[index] = value

    def __get_par_b(self, index=0):
        return self._data_object.par_b[index]

    def __set_par_b(self, value, index=0):
        assert (index >= 0 and index < 5)
        self._data_object.par_b[index] = value

    #: Atomic scattering factor :math:`a_1`
    par_a1 = FloatProperty(
        default=0.0, text="a1",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,),
        fget=partial(__get_par_a, index=0), fset=partial(__set_par_a, index=0)
    )
    #: Atomic scattering factor :math:`a_2`
    par_a2 = FloatProperty(
        default=0.0, text="a2",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,),
        fget=partial(__get_par_a, index=1), fset=partial(__set_par_a, index=1)
    )
    #: Atomic scattering factor :math:`a_3`
    par_a3 = FloatProperty(
        default=0.0, text="a3",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,),
        fget=partial(__get_par_a, index=2), fset=partial(__set_par_a, index=2)
    )
    #: Atomic scattering factor :math:`a_4`
    par_a4 = FloatProperty(
        default=0.0, text="a4",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,),
        fget=partial(__get_par_a, index=3), fset=partial(__set_par_a, index=3)
    )
    #: Atomic scattering factor :math:`a_5`
    par_a5 = FloatProperty(
        default=0.0, text="a5",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,),
        fget=partial(__get_par_a, index=4), fset=partial(__set_par_a, index=4)
    )

    #: Atomic scattering factor :math:`b_1`
    par_b1 = FloatProperty(
        default=0.0, text="b1",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,),
        fget=partial(__get_par_b, index=0), fset=partial(__set_par_b, index=0)
    )
    #: Atomic scattering factor :math:`b_2`
    par_b2 = FloatProperty(
        default=0.0, text="b2",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,),
        fget=partial(__get_par_b, index=1), fset=partial(__set_par_b, index=1)
    )
    #: Atomic scattering factor :math:`b_3`
    par_b3 = FloatProperty(
        default=0.0, text="b3",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,),
        fget=partial(__get_par_b, index=2), fset=partial(__set_par_b, index=2)
    )
    #: Atomic scattering factor :math:`b_4`
    par_b4 = FloatProperty(
        default=0.0, text="b4",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,),
        fget=partial(__get_par_b, index=3), fset=partial(__set_par_b, index=3)
    )
    #: Atomic scattering factor :math:`b_5`
    par_b5 = FloatProperty(
        default=0.0, text="b5",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,),
        fget=partial(__get_par_b, index=4), fset=partial(__set_par_b, index=4)
    )

    #: Atomic scattering factor c
    par_c = FloatProperty(
        default=0.0, text="c",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,)
    )

    #: Debye-Waller scattering factor
    debye = FloatProperty(
        default=0.0, text="c",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,)
    )

    #: The charge of the ion (eg. 3.0 for :math:`Al^{3+}`)
    charge = FloatProperty(
        default=0.0, text="Charge",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,)
    )

    #: The atomic weight for this ion
    weight = FloatProperty(
        default=0.0, text="Weight",
        visible=True, persistent=True,
        signal_name="data_changed", widget_type="entry",
        mix_with=(SignalMixin,)
    )

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Constructor takes any of its properties as a keyword argument.
            Any other arguments or keywords are passed to the base class.
        """
        keys = [ "data_%s" % prop.label for prop in type(self).Meta.get_local_persistent_properties()]
        keys.extend([ prop.label for prop in type(self).Meta.get_local_persistent_properties()])
        my_kwargs = self.pop_kwargs(kwargs, *keys)
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

        for kw in ["par_a%d" % i for i in range(1, 6)] + ["par_b%d" % i for i in range(1, 6)] + ["par_c"]:
            setattr(
                self, kw, self.get_kwarg(kwargs, 0.0, kw, "data_%s" % kw)
            )

    def __str__(self):
        return "<AtomType %s (%s)>" % (self.name, id(self))

    def get_atomic_scattering_factors(self, stl_range):
        """
        Returns the atomic scattering factor for this `AtomType` for the given range
        of sin(theta)/lambda (`stl_range`) values. 
        """
        angstrom_range = ((stl_range * 0.05) ** 2)
        return get_atomic_scattering_factor(angstrom_range, self.data_object)

    pass # end of class

@storables.register()
class Atom(DataModel, Storable):
    """
    Atom objects combine structural information (z coordinate and proportion)
    and an AtomType. 
    """

    # MODEL METADATA:
    class Meta(DataModel.Meta):
        store_id = "Atom"
        layer_filters = [
            ("Layer file", get_case_insensitive_glob("*.lyr")),
        ]

    _data_object = None
    @property
    def data_object(self):
        """
        The data object that is used in the calculations framework 
        (see :mod:`pyxrd.generic.calculations.atoms`).
        Is an instance of :class:`~pyxrd.generic.calculations.data_objects.AtomData`  
        """
        self._data_object.default_z = self.default_z
        self._data_object.stretch_z = self.stretch_z
        self._data_object.pn = self.pn
        self._data_object.atom_type = getattr(self.atom_type, "data_object", None)
        return self._data_object

    component = property(DataModel.parent.fget, DataModel.parent.fset)

    # PROPERTIES:

    #: The name of the Atom
    name = StringProperty(
        default="", text="Name",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: Default z coordinate for this Atom. Also see :attr:`~z`
    default_z = FloatProperty(
        default=0.0, text="Default z",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed",
        mix_with=(SignalMixin,)
    )

    #: Flag indicating whether or not z coordinates should be stretched
    #: using the silicate lattice and unit cell dimensions from the Component.
    #: Should be set for interlayer atoms, so their z coordinates are adjusted
    #: when the component basal spacing is changed. Also see `z`.
    stretch_z = BoolProperty(
        default=False, text="Stretch z values",
        visible=False, persistent=True,
        signal_name="data_changed",
        mix_with=(SignalMixin,)
    )

    #: The z coordinate for this atom. If `stretch_values` is False or if
    #: this Atom's component is None, then this will return the `default_z`
    #: value. If `stretch_values` is True and a component is set on this Atom,
    #: it is calculated as::
    #:
    #:     `lattice_d + (default_z - lattice_d) * factor`
    #:
    #: where `lattice_d` and `factor` are given by calling
    #:`get_interlayer_stretch_factors` on the :class:`~pyxrd.phases.models.Component`.
    @FloatProperty(
        default=None, text="Z",
        visible=True, tabular=True,
        mix_with=(ReadOnlyMixin,)
    )
    def z(self):
        if self.stretch_values and self.component is not None:
            lattice_d, factor = self.component.get_interlayer_stretch_factors()
            return float(lattice_d + (self.default_z - lattice_d) * factor)
        return self.default_z

    #: The # of atoms (projected onto the c-axis for the considered unit cell)
    pn = FloatProperty(
        default=None, text="Multiplicity",
        visible=True, persistent=True, tabular=True,
        signal_name="data_changed",
        mix_with=(SignalMixin,)
    )

    def _get_weight(self):
        if self.atom_type is not None:
            return self.pn * self.atom_type.weight
        else:
            return 0.0

    #: The total weight for this Atom, taking `pn` into consideration.
    weight = FloatProperty(
        default=None, text="Weight", fget=_get_weight,
        visible=False, persistent=False,
        mix_with=(ReadOnlyMixin,)
    )

    _atom_type_uuid = None
    _atom_type_name = None
    def _set_atom_type(self, value):
        old = type(self).atom_type._get(self)
        if old is not None:
            self.relieve_model(old)
        type(self).atom_type._set(self, value)
        if value is not None:
            self.observe_model(value)

    #: The AtomType to be used for this Atom.
    atom_type = LabeledProperty(
        default=None, text="Atom Type",
        visible=True, persistent=False, tabular=True, data_type=AtomType,
        signal_name="data_changed",
        fset=_set_atom_type,
        mix_with=(SignalMixin,)
    )

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Constructor takes any of its properties as a keyword argument.
            
            In addition to the above, the constructor still supports the 
            following deprecated keywords, maping to a current keyword:
                - z: maps to the 'default_z' keyword.
                
            Any other arguments or keywords are passed to the base class.
        """

        my_kwargs = self.pop_kwargs(kwargs,
            "data_name", "data_z", "z", "data_pn", "data_atom_type", "stretch_z",
            "atom_type_uuid", "atom_type_name", "atom_type_index", "atom_type",
            *[prop.label for prop in type(self).Meta.get_local_persistent_properties()]
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

        self.atom_type = self.get_kwarg(kwargs, None, "atom_type")
        self._atom_type_uuid = self.get_kwarg(kwargs, None, "atom_type_uuid")
        self._atom_type_name = self.get_kwarg(kwargs, None, "atom_type_name")

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
        """
        Get the atom's structure factor for a given range of 2*sin(θ) / λ values.
        Expects λ to be in nanometers!
        """
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
        if getattr(self, "_atom_type_name", None) is not None:
            assert(self.component is not None)
            assert(self.component.phase is not None)
            assert(self.component.phase.project is not None)
            for atom_type in self.component.phase.project.atom_types:
                if atom_type.name == self._atom_type_name:
                    self.atom_type = atom_type
                    break
        self._atom_type_uuid = None
        self._atom_type_name = None

    def json_properties(self):
        retval = super(Atom, self).json_properties()
        if self.component is None or self.component.export_atom_types:
            retval["atom_type_name"] = self.atom_type.name if self.atom_type is not None else ""
        else:
            retval["atom_type_uuid"] = self.atom_type.uuid if self.atom_type is not None else ""
        return retval

    @staticmethod
    def get_from_csv(filename, callback=None, parent=None):
        """
        Returns a list of atoms fetched from the .CSV file `filename`.
        If parent is passed, this will be used to resolve AtomType references,
        and will be passed to the constructor of the Atom as a keyword.
        If callback is passes it will be called with the loaded atom as the
        first and only argument.
        """
        import csv
        atl_reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"') # TODO create csv dialect!
        header = True
        atoms = []

        types = dict()
        if parent is not None:
            for atom_type in parent.phase.project.atom_types:
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
        """
        Saves a list of atoms to the passed filename.
        """
        import csv
        atl_writer = csv.writer(open(filename, 'wb'), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        atl_writer.writerow(["Atom", "z", "def_z", "pn", "Element"])
        for item in atoms:
            if item is not None and item.atom_type is not None:
                atl_writer.writerow([item.name, item.z, item.default_z, item.pn, item.atom_type.name])

    pass # end of class

