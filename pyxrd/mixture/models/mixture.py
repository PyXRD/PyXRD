# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import csv
import random
from warnings import warn
from itertools import chain, izip
from collections import OrderedDict
from contextlib import contextmanager

from pyxrd.gtkmvc.model import Signal
import numpy as np

from pyxrd.data import settings

from pyxrd.generic.io import storables, Storable
from pyxrd.generic.utils import print_timing
from pyxrd.generic.models import DataModel, PropIntel, MultiProperty
from pyxrd.generic.models.mixins import ObjectListStoreChildMixin
from pyxrd.generic.models.metaclasses import pyxrd_object_pool
from pyxrd.generic.models.treemodels import ObjectTreeStore

from pyxrd.generic.refinement.mixins import RefinementValue, RefinementGroup
from pyxrd.generic.refinement.wrapper import RefinableWrapper
from pyxrd.generic.calculations.data_objects import MixtureData

from .methods import get_all_refine_methods
from .optimizers import Optimizer
from .refiner import Refiner


@storables.register()
class Mixture(DataModel, ObjectListStoreChildMixin, Storable):
    """
        The base model for optimization and refinement of calculated data
        and experimental data. It uses two helper models to achieve this;
        the Optimizer and Refiner. This model is responsible for storing
        any information worthy of storage and keeping the lists of phases and
        specimens aligned.
    """
    # MODEL INTEL:
    __parent_alias__ = "project"
    __model_intel__ = [ # TODO add labels
        PropIntel(name="name", label="Name", data_type=unicode, is_column=True, storable=True, has_widget=True),
        PropIntel(name="refinables", label="", data_type=object, is_column=True, has_widget=True, widget_type="tree_view"),
        PropIntel(name="auto_run", label="", data_type=bool, is_column=True, storable=True, has_widget=True),
        PropIntel(name="refine_method", label="", data_type=int, storable=True, has_widget=True, widget_type="combo"),
        PropIntel(name="needs_reset", label="", data_type=object, storable=False,), # Signal used to indicate the mixture matrix needs to be re-built...
    ]
    __store_id__ = "Mixture"

    _data_object = None
    @property
    def data_object(self):
        self._data_object.specimens = [None] * len(self.specimens)
        for i, specimen in enumerate(self.specimens):
            if specimen is not None:
                data_object = specimen.data_object
                data_object.phases = [None] * len(self.phases)
                for j, phase in enumerate(self.phase_matrix[i, ...].flatten()):
                    data_object.phases[j] = phase.data_object if phase is not None else None
                self._data_object.specimens[i] = data_object
            else:
                self._data_object.specimens[i] = None
        return self._data_object

    # SIGNALS:
    needs_reset = None

    # INTERNALS:
    _name = ""
    def get_name_value(self):
        return self._name
    def set_name_value(self, value):
        self._name = value
        self.liststore_item_changed()

    refinables = None
    auto_run = False
    all_refine_methods = get_all_refine_methods()
    refine_method = MultiProperty(0, int, None, { key: method.name for key, method in all_refine_methods.iteritems() })
    refine_options = None # TODO make this storable!

    # Lists and matrices:
    phase_matrix = None
    specimens = None
    phases = None

    @property
    def scales(self):
        return self._data_object.scales
    @scales.setter
    def scales(self, value):
        self._data_object.scales = value

    @property
    def bgshifts(self):
        return self._data_object.bgshifts
    @bgshifts.setter
    def bgshifts(self, value):
        self._data_object.bgshifts = value

    @property
    def fractions(self):
        return self._data_object.fractions
    @fractions.setter
    def fractions(self, value):
        self._data_object.fractions = value

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, **kwargs):
        """
            Valid keyword arguments for a Mixture are:
                name: the name of this mixture
                auto_run: a flag indicating whether or not this Mixture should
                 change the fractions, bg_shifts and scales when a specimen or
                 a phase has emitted a data_changed signal
                phase_uuids: a list containing the UUID's for the phases in the
                 mixture
                specimen_uuids: a list containing the UUID's for the specimens
                 in the mixture
                phases: a list containing the names for each 'phase row'
                scales: a list containing the absolute scales for each of the
                 specimens
                bg_shifts: a list containing the background shifts for each of
                 the specimens
                fractions: a list containing the fractions for each phase
                refinables: an ObjectTreeStore containing the refinable 
                 properties in this mixture
                refine_method: which method to use for the refinement (see 
                 mixture.models.methods.get_all_refine_methods) 
                
            Deprecated, but still supported, keyword arguments:
                phase_indeces: a list containing the indices of the phases in
                 the ObjectListStore at the project level
                specimen_indeces: a list containing the indices of the specimens
                 in the ObjectListStore at the project level
        """
        super(Mixture, self).__init__(**kwargs)

        with self.data_changed.hold():

            self._data_object = MixtureData()

            self.needs_reset = Signal()
            self.name = self.get_kwarg(kwargs, "New Mixture", "name", "data_name")
            self.auto_run = self.get_kwarg(kwargs, False, "auto_run")

            # 2D matrix, rows match specimens, columns match mixture 'phases'; contains the actual phase objects
            phase_uuids = self.get_kwarg(kwargs, None, "phase_uuids")
            phase_indeces = self.get_kwarg(kwargs, None, "phase_indeces")
            if phase_uuids is not None:
                self.phase_matrix = np.array([[pyxrd_object_pool.get_object(uuid) if uuid else None for uuid in row] for row in phase_uuids], dtype=np.object_)
            elif phase_indeces and self.parent is not None:
                warn("The use of object indices is deprecated since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
                self.phase_matrix = np.array([[self.parent.phases.get_user_data_from_index(index) if index != -1 else None for index in row] for row in phase_indeces], dtype=np.object_)
            else:
                self.phase_matrix = np.empty(shape=(0, 0), dtype=np.object_)

            # list with actual specimens, indexes match with rows in phase_matrix
            specimen_uuids = self.get_kwarg(kwargs, None, "specimen_uuids")
            specimen_indeces = self.get_kwarg(kwargs, None, "specimen_indeces")
            if specimen_uuids:
                self.specimens = [pyxrd_object_pool.get_object(uuid) if uuid else None for uuid in specimen_uuids]
            elif specimen_indeces and self.parent is not None:
                warn("The use of object indices is deprecated since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
                self.specimens = [self.parent.specimens.get_user_data_from_index(index) if index != -1 else None for index in specimen_indeces]
            else:
                self.specimens = list()

            # list with mixture phase names, indexes match with cols in phase_matrix
            self.phases = self.get_kwarg(kwargs, list(), "phases", "data_phases")

            # list with scale values, indexes match with rows in phase_matrix (= specimens)
            self.scales = np.asarray(self.get_kwarg(kwargs, [1.0] * len(self.specimens), "scales", "data_scales"))
            # list with specimen background shift values, indexes match with rows in phase_matrix (=specimens)
            self.bgshifts = np.asarray(self.get_kwarg(kwargs, [0.0] * len(self.specimens), "bgshifts", "data_bgshifts"))
            # list with phase fractions, indexes match with cols in phase_matrix (=phases)
            self.fractions = np.asarray(self.get_kwarg(kwargs, [0.0] * len(self.phases), "fractions", "data_fractions"))

            self.refinables = self.get_kwarg(kwargs, ObjectTreeStore(RefinableWrapper), "refinables", "data_refinables")
            try:
                self.refine_method = int(self.get_kwarg(kwargs, self.refine_method, "refine_method", "data_refine_method"))
            except ValueError:
                self.refine_method = self.refine_method
                pass # ignore faulty values, these indices change from time to time.

            # sanity check:
            n, m = self.phase_matrix.shape
            if len(self.scales) != n or len(self.specimens) != n or len(self.bgshifts) != n:
                raise IndexError, "Shape mismatch: scales (%d), background shifts (%d) or specimens (%d) list lengths do not match with row count (%d) of phase matrix" % (len(self.scales), len(self.specimens), len(self.bgshifts), n)
            if len(self.phases) != m or len(self.fractions) != m:
                raise IndexError, "Shape mismatch: fractions or phases lists do not match with column count of phase matrix"

            self.optimizer = Optimizer(parent=self)
            self.refiner = Refiner(parent=self)

            self._observe_specimens()
            self._observe_phases()
            self.update_refinement_treestore()

            pass # end hold data_changed

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @DataModel.observe("data_changed", signal=True)
    def notify_data_changed(self, model, prop_name, info):
        if not (info.arg == "based_on" and model.based_on is not None and model.based_on in self.phase_matrix):
            self.data_changed.emit() # Propagate the signal

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def json_properties(self):
        self.update_refinement_treestore()
        retval = Storable.json_properties(self)

        retval["phase_uuids"] = [[item.uuid if item else "" for item in row] for row in map(list, self.phase_matrix)]
        retval["specimen_uuids"] = [specimen.uuid if specimen else "" for specimen in self.specimens]
        retval["phases"] = self.phases
        retval["fractions"] = self.fractions.tolist()
        retval["bgshifts"] = self.bgshifts.tolist()
        retval["scales"] = self.scales.tolist()

        return retval

    @staticmethod
    def from_json(**kwargs):
        sargs = dict()
        for key in ("refinables",):
            if key in kwargs:
                sargs[key] = kwargs[key]
                del kwargs[key]
            else:
                sargs[key] = None

        mixture = Mixture(**kwargs)

        return mixture

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def unset_phase(self, phase):
        """ Clears a phase slot in the phase matrix """
        with self.data_changed.hold_and_emit():
            shape = self.phase_matrix.shape
            with self._relieve_and_observe_phases():
                for i in range(shape[0]):
                    for j in range(shape[1]):
                        if self.phase_matrix[i, j] == phase:
                            self.phase_matrix[i, j] = None
            self.update_refinement_treestore()

    def unset_specimen(self, specimen):
        """ Clears a specimen slot in the specimen list """
        with self.data_changed.hold_and_emit():
            with self._relieve_and_observe_specimens():
                for i, spec in enumerate(self.specimens):
                    if spec == specimen:
                        self.specimens[i] = None

    def set_phase(self, specimen_slot, phase_slot, phase):
        """Sets the phase at the given slot positions"""
        with self._relieve_and_observe_phases():
            self.phase_matrix[specimen_slot, phase_slot] = phase

    def set_specimen(self, specimen_slot, specimen):
        """Sets the specimen at the given slot position"""
        with self._relieve_and_observe_specimens():
            self.specimens[specimen_slot] = specimen

    @contextmanager
    def _relieve_and_observe_specimens(self):
        self._relieve_specimens()
        yield
        self._observe_specimens()

    def _observe_specimens(self):
        """ Starts observing specimens in the specimens list"""
        for specimen in self.specimens:
            if specimen is not None:
                self.observe_model(specimen)

    def _relieve_specimens(self):
        """ Relieves specimens observer calls """
        for specimen in self.specimens:
            if specimen is not None:
                self.relieve_model(specimen)

    @contextmanager
    def _relieve_and_observe_phases(self):
        self._relieve_phases()
        yield
        self._observe_phases()

    def _observe_phases(self):
        """ Starts observing phases in the phase matrix"""
        for phase in self.phase_matrix.flat:
            if phase is not None:
                self.observe_model(phase)

    def _relieve_phases(self):
        """ Relieves phase observer calls """
        for phase in self.phase_matrix.flat:
            if phase is not None:
                self.relieve_model(phase)

    def add_phase_slot(self, phase_name, fraction):
        """ Adds a new phase column to the phase matrix """
        with self.data_changed.hold_and_emit():
            self.phases.append(phase_name)
            self.fractions = np.append(self.fractions, fraction)
            n, m = self.phase_matrix.shape # @UnusedVariable
            if self.phase_matrix.size == 0:
                self.phase_matrix = np.resize(self.phase_matrix.copy(), (n, m + 1))
                self.phase_matrix[:] = None
            else:
                self.phase_matrix = np.concatenate([self.phase_matrix.copy(), [[None]] * n ], axis=1)
                self.phase_matrix[:, m] = None
            self.update_refinement_treestore()
        return m

    def del_phase_slot(self, phase_slot):
        """ Deletes a phase column using its index """
        with self.data_changed.hold_and_emit():
            with self._relieve_and_observe_phases():
                # Remove the corresponding phase name, fraction & references:
                del self.phases[phase_slot]
                self.fractions = np.delete(self.fractions, phase_slot)
                self.phase_matrix = np.delete(self.phase_matrix, phase_slot, axis=1)
            # Update our refinement tree store to reflect current state
            self.update_refinement_treestore()
        # Inform any interested party they need to update their representation
        self.needs_reset.emit()

    def del_phase_slot_by_name(self, phase_name):
        """ Deletes a phase slot using its name """
        self.del_phase_slot(self.phases.index(phase_name))

    def add_specimen_slot(self, specimen, scale, bgs):
        """ Adds a new specimen to the phase matrix (a row) and specimen list """
        with self.data_changed.hold_and_emit():
            self.specimens.append(specimen)
            self.scales = np.append(self.scales, scale)
            self.bgshifts = np.append(self.bgshifts, bgs)
            n, m = self.phase_matrix.shape
            if self.phase_matrix.size == 0:
                self.phase_matrix = np.resize(self.phase_matrix.copy(), (n + 1, m))
                self.phase_matrix[:] = None
            else:
                self.phase_matrix = np.concatenate([self.phase_matrix.copy(), [[None] * m] ], axis=0)
                self.phase_matrix[n, :] = None
        return n

    def del_specimen_slot(self, specimen_slot):
        """ Deletes a specimen slot using its slot index """
        with self.data_changed.hold_and_emit():
            # Remove the corresponding specimen name, scale, bg-shift & phases:
            with self._relieve_and_observe_specimens():
                del self.specimens[specimen_slot]
                self.scales = np.delete(self.scales, specimen_slot)
                self.bgshifts = np.delete(self.bgshifts, specimen_slot)
                self.phase_matrix = np.delete(self.phase_matrix, specimen_slot, axis=0)
            # Update our refinement tree store to reflect current state
            self.update_refinement_treestore()
        # Inform any interested party they need to update their representation
        self.needs_reset.emit()

    def del_specimen_slot_by_object(self, specimen):
        """ Deletes a specimen slot using the actual object """
        try:
            self.del_specimen_slot(self.specimens.index(specimen))
        except ValueError, msg:
            print "Caught a ValueError when deleting a specimen from  mixture '%s': %s" % (self.name, msg)

    # ------------------------------------------------------------
    #      Refinement stuff:
    # ------------------------------------------------------------
    def set_data_object(self, mixture, calculate=False):
        """
            Sets the fractions, scales and bgshifts of this mixture.
        """
        with self.data_changed.hold():
            self.fractions[:] = list(mixture.fractions)
            self.scales[:] = list(mixture.scales)
            self.bgshifts[:] = list(mixture.bgshifts)

            if calculate: # (re-)calculate if requested:
                mixture = self.optimizer.calculate(mixture)

            for i, (specimen_data, specimen) in enumerate(izip(mixture.specimens, self.specimens)):
                if specimen is not None:
                    specimen.update_pattern(
                        specimen_data.total_intensity,
                        specimen_data.phase_intensities * self.fractions[:, np.newaxis] * self.scales[i],
                        self.phase_matrix[i, :]
                    )

    def optimize(self):
        """
            Optimize the current solution (fractions, scales, bg shifts & calculate
            phase intensities)
        """
        self.set_data_object(self.optimizer.optimize())

    def apply_current_data_object(self):
        """
            Recalculates the intensities using the current fractions, scales
            and bg shifts without optimization
        """
        self.set_data_object(self.data_object, calculate=True)

    # @print_timing
    def update(self):
        """
            Optimizes or re-applies the current mixture 'solution'.
            Effectively re-calculates the entire patterns.
        """
        with self.data_changed.hold_and_emit():
            if self.auto_run:
                self.optimize()
            else:
                self.apply_current_data_object()

    def update_refinement_treestore(self):
        """
            Called whenever the refinement view is opened, this creates a tree
            store with the refinable properties and their minimum, maximum and
            current value.
        """

        self.refinables.clear()

        def add_property(parent_itr, obj, prop):
            rp = RefinableWrapper(obj=obj, prop=prop, sensitivity=0, refine=False, parent=self)
            return self.refinables.append(parent_itr, rp)

        def parse_attribute(obj, attr, root_itr):
            """
                obj: the object
                attr: the attribute of obj or None if obj is the attribute
                root_itr: the iter new iters should be put under
            """
            if attr is not None:
                if hasattr(obj, "get_base_value"):
                    value = obj.get_base_value(attr)
                else:
                    value = getattr(obj, attr)
            else:
                value = obj

            if isinstance(value, RefinementValue): # Atom Ratios and UnitCellProperties
                new_itr = add_property(root_itr, value, None)
            elif hasattr(value, "iter_objects"): # object list store or similar
                for new_obj in value.iter_objects(): parse_attribute(new_obj, None, root_itr)
            elif isinstance(value, RefinementGroup): # Phases, Components, Probabilities
                if len(value.refinables) > 0:
                    new_itr = add_property(root_itr, value, None)
                    for new_attr in value.refinables: parse_attribute(value, new_attr, new_itr)
            else: # regular values
                new_itr = add_property(root_itr, obj, attr)

        for phase in self.parent.phases.iter_objects():
            if phase in self.phase_matrix:
                parse_attribute(phase, None, None)

    def auto_restrict(self): # TODO set a restrict range attribute on the PropIntels, so we can use custom ranges for each property
        """
            Convenience function that restricts the selected properties 
            automatically by setting their minimum and maximum values.
        """
        for ref_prop in self.refinables.iter_objects():
            if ref_prop.refine and ref_prop.refinable:
                ref_prop.value_min = ref_prop.value * 0.8
                ref_prop.value_max = ref_prop.value * 1.2
        return

    def randomize(self):
        """
            Convenience function that randomize the selected properties.
            Respects the current minimum and maximum values.
            Executes an optimization after the randomization.
        """
        with self.data_changed.hold():
            for ref_prop in self.refinables.iter_objects():
                if ref_prop.refine and ref_prop.refinable:
                    ref_prop.value = random.uniform(ref_prop.value_min, ref_prop.value_max)

    def get_refine_method(self):
        return self.all_refine_methods[self.refine_method]

    def setup_refine_options(self):
        if self.refine_options == None:
            options = self.get_refine_method().options
            self.refine_options = {
                name: default for name, arg, typ, default, limits in options
            }

    # ------------------------------------------------------------
    #      Various other things:
    # ------------------------------------------------------------
    def get_composition_matrix(self):
        """
            Returns a matrix containing the oxide composition for each specimen 
            in this mixture. It uses the COMPOSITION_CONV file for this purpose
            to convert element weights into their oxide weight equivalent.
        """

        # create an atom nr -> (atom name, conversion) mapping
        # this is used to transform most of the elements into their oxides
        atom_conv = OrderedDict()
        with open(settings.DATA_REG.get_file_path("COMPOSITION_CONV"), 'r') as f:
            reader = csv.reader(f)
            reader.next() # skip header
            for row in reader:
                nr, name, fact = row
                atom_conv[int(nr)] = (name, float(fact))

        comps = list()
        for i, row in enumerate(self.phase_matrix):
            comp = dict()
            for j, phase in enumerate(row):
                phase_fract = self.fractions[j]
                for k, component in enumerate(phase.components.iter_objects()):
                    comp_fract = phase.probabilities.mW[k] * phase_fract
                    for atom in chain(component.layer_atoms.iter_objects(),
                            component.interlayer_atoms.iter_objects()):
                        nr = atom.atom_type.atom_nr
                        if nr in atom_conv:
                            wt = atom.pn * atom.atom_type.weight * comp_fract * atom_conv[nr][1]
                            comp[nr] = comp.get(nr, 0.0) + wt
            comps.append(comp)

        final_comps = np.zeros(shape=(len(atom_conv) + 1, len(comps) + 1), dtype='a15')
        final_comps[0, 0] = " "*8
        for j, comp in enumerate(comps):
            fact = 100.0 / sum(comp.values())
            for i, (nr, (oxide_name, conv)) in enumerate(atom_conv.iteritems()):
                wt = comp.get(nr, 0.0) * fact
                # set relevant cells:
                if i == 0:
                    final_comps[i, j + 1] = self.specimens[j].name.ljust(15)[:15]
                if j == 0:
                    final_comps[i + 1, j] = ("%s  " % oxide_name).rjust(8)[:8]
                final_comps[i + 1, j + 1] = ("%.1f" % wt).ljust(15)[:15]

        return final_comps

    pass # end of class
