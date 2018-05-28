# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import csv
from warnings import warn
from itertools import chain
from collections import OrderedDict
from contextlib import contextmanager
import logging

import numpy as np

from mvc.models.properties import (
    SignalProperty, LabeledProperty, SignalMixin, StringProperty,
    BoolProperty, IntegerProperty
)
logger = logging.getLogger(__name__)

from pyxrd.data import settings

from pyxrd.generic.io import storables, Storable
from pyxrd.generic.models import DataModel

from pyxrd.refinement.refinement import Refinement

from pyxrd.calculations.data_objects import MixtureData
from pyxrd.phases.models import Phase

from .optimizers import Optimizer

@storables.register()
class Mixture(DataModel, Storable):
    """
        The base model for optimization and refinement of calculated data
        and experimental data. This is the main model you want to interact with,
        lower-level classes' functionality (mainly 
        :class:`~pyxrd.mixture.models.optimizers.Optimizer` and 
        :class:`~pyxrd.mixture.models.refiner.Refinement`) are integrated into this
        class. 
        
        The Mixture is responsible for managing the phases and specimens lists
        and combination-matrix and for delegating any optimization, calculation
        or refinement calls to the appropriate helper class.
    """
    # MODEL INTEL:
    class Meta(DataModel.Meta):
        store_id = "Mixture"

    _data_object = None
    @property
    def data_object(self):
        self._data_object.parsed = False
        self._data_object.optimized = False
        self._data_object.calculated = False
        self._data_object.specimens = [None] * len(self.specimens)
                
        self._data_object.n = len(self.specimens)
        self._data_object.m = len(self.phases)
               
        self._data_object.scales_mask = np.ones_like(self.scales)
        if self.auto_scales:
            self._data_object.scales_mask = np.ones_like(self.bgshifts)
        else:
            self._data_object.scales_mask = np.zeros_like(self.bgshifts)
            
        if self.auto_bg:
            self._data_object.bgshifts_mask = np.ones_like(self.bgshifts)
        else:
            self._data_object.bgshifts_mask = np.zeros_like(self.bgshifts)
        
        for i, specimen in enumerate(self.specimens):
            if specimen is not None:
                data_object = specimen.data_object
                data_object.phases = [[None] * self._data_object.m for _ in data_object.z_list]
                for z_index in range(len(specimen.get_z_list())):
                    for phase_index in range(self.phase_matrix.shape[1]):
                        data_object.phases[z_index][phase_index] = self.get_phase_data_object(i, z_index, phase_index)
                self._data_object.specimens[i] = data_object
            else:
                self._data_object.specimens[i] = None
        return self._data_object

    def get_phase_data_object(self, specimen_index, z_index, phase_index):
        phase = self.phase_matrix[specimen_index, ...].flatten()[phase_index]
        return phase.data_object if phase is not None else None

    project = property(DataModel.parent.fget, DataModel.parent.fset)

    # SIGNALS:
    #: Signal, emitted when the # of phases or specimens changes
    needs_reset = SignalProperty()
    #: Signal, emitted when the patterns of the specimens need an update
    needs_update = SignalProperty()

    #: The name of this Mixture
    name = StringProperty(
        default="", text="Name",
        visible=True, persistent=True, tabular=True,
        signal_name="visuals_changed",
        mix_with=(SignalMixin,)
    )

    #: Flag, True if the mixture will automatically adjust phase fractions and scales
    auto_run = BoolProperty(
        default=False, text="Auto Run",
        visible=True, persistent=True, tabular=True
    )

    #: Flag, True if the mixture is allowed to also update the background level
    auto_bg = BoolProperty(
        default=False, text="Auto Bg",
        visible=True, persistent=True, tabular=True
    )

    #: Flag, True if the mixture is allowed to also update the background level
    auto_scales = BoolProperty(
        default=True, text="Auto Scales",
        visible=True, persistent=True, tabular=True
    )

    #: The tree of refinable properties
    @LabeledProperty(
        default=None, text="",
        visible=True, persistent=False, tabular=True,
        data_type=object,
    )
    def refinables(self):
        return self.refinement.refinables

    #: An integer describing which method to use for the refinement (see
    #: mixture.models.methods.get_all_refine_methods)
    @IntegerProperty(
        default=0, text="Refinement method index",
        visible=False, persistent=True,
    )
    def refine_method_index(self):
        return self.refinement.refine_method_index

    #: A dict containing the current refinement options
    @LabeledProperty(
        default=None, text="Current refinement method options",
        visible=False, persistent=True, tabular=False,
        data_type=object, store_private="all_refine_options"
    )
    def refine_options(self):
        return  self.refinement.refine_options

    #: A dict containing all refinement options
    @LabeledProperty(
        default=None, text="All refinement methods options",
        visible=False, persistent=False, tabular=False,
        data_type=object
    )
    def all_refine_options(self):
        return self.refinement.all_refine_options

    # Lists and matrices:
    #: A 2D numpy object array containing the combination matrix
    phase_matrix = None
    #: The list of specimen objects
    specimens = None
    #: The list of phase names
    phases = None

    @property
    def scales(self):
        """ A list of floats containing the absolute scales for the calculated patterns """
        return self._data_object.scales
    @scales.setter
    def scales(self, value):
        self._data_object.scales = value

    @property
    def bgshifts(self):
        """ A list of background shifts for the calculated patterns """
        return self._data_object.bgshifts
    @bgshifts.setter
    def bgshifts(self, value):
        self._data_object.bgshifts = value

    @property
    def fractions(self):
        """ A list of phase fractions for this mixture """
        return self._data_object.fractions
    @fractions.setter
    def fractions(self, value):
        self._data_object.fractions = value

    @property
    def fractions_mask(self):
        """ A mask indicating which fractions are to be optimized """
        return self._data_object.fractions_mask
    @fractions_mask.setter
    def fractions_mask(self, value):
        self._data_object.fractions_mask = value

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Constructor takes any of its properties as a keyword argument.
            It also support two UUID list keyword arguments:
                - phase_uuids: a list of UUID's for the phases in the mixture
                - specimen_uuids: a list of UUID's for the specimens in the mixture
            These should be *instead* of the phases and specimens keywords.
            
            In addition to the above, the constructor still supports the 
            following deprecated keywords, mapping to a current keyword:
                - phase_indeces: a list of project indices for the phases in the mixture
                - specimen_indeces: a list of project indices for the specimens in the mixture
                
            Any other arguments or keywords are passed to the base class.
        """

        my_kwargs = self.pop_kwargs(kwargs,
            "data_name", "phase_uuids", "phase_indeces", "specimen_uuids",
            "specimen_indeces", "data_phases", "data_scales", "data_bgshifts",
            "data_fractions", "refine_method", "data_refine_method",
            "fractions", "fractions_mask", "bgshifts", "scales", "phases",
            *[prop.label for prop in Mixture.Meta.get_local_persistent_properties()]
        )
        super(Mixture, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.data_changed.hold():

            self._data_object = MixtureData()

            self.name = self.get_kwarg(kwargs, "New Mixture", "name", "data_name")
            self.auto_run = self.get_kwarg(kwargs, False, "auto_run")
            self.auto_bg = self.get_kwarg(kwargs, True, "auto_bg")
            self.auto_scales = self.get_kwarg(kwargs, True, "auto_scales")

            # 2D matrix, rows match specimens, columns match mixture 'phases'; contains the actual phase objects
            phase_uuids = self.get_kwarg(kwargs, None, "phase_uuids")
            phase_indeces = self.get_kwarg(kwargs, None, "phase_indeces")
            if phase_uuids is not None:
                self.phase_matrix = np.array([[type(type(self)).object_pool.get_object(uuid) if uuid else None for uuid in row] for row in phase_uuids], dtype=np.object_)
            elif phase_indeces and self.parent is not None:
                warn("The use of object indices is deprecated since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
                self.phase_matrix = np.array([[self.parent.phases[index] if index != -1 else None for index in row] for row in phase_indeces], dtype=np.object_)
            else:
                self.phase_matrix = np.empty(shape=(0, 0), dtype=np.object_)

            # list with actual specimens, indexes match with rows in phase_matrix
            specimen_uuids = self.get_kwarg(kwargs, None, "specimen_uuids")
            specimen_indeces = self.get_kwarg(kwargs, None, "specimen_indeces")
            if specimen_uuids:
                self.specimens = [type(type(self)).object_pool.get_object(uuid) if uuid else None for uuid in specimen_uuids]
            elif specimen_indeces and self.parent is not None:
                warn("The use of object indices is deprecated since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
                self.specimens = [self.parent.specimens[index] if index != -1 else None for index in specimen_indeces]
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
            # list with phase fractions mask, indexes match with cols in phase_matrix (=phases)
            self.fractions_mask = np.asarray(self.get_kwarg(kwargs, [1] * len(self.phases), "fractions_mask"))

            # sanity check:
            n, m = self.phase_matrix.shape if self.phase_matrix.ndim == 2 else (0, 0)
            if len(self.scales) != n or len(self.specimens) != n or len(self.bgshifts) != n:
                raise IndexError("Shape mismatch: scales (%d), background shifts (%d) or specimens (%d) list lengths do not match with row count (%d) of phase matrix" % (len(self.scales), len(self.specimens), len(self.bgshifts), n))
            if len(self.phases) != m or len(self.fractions) != m:
                raise IndexError("Shape mismatch: fractions (%s) or phases (%d) lists do not match with column count of phase matrix (%d)" % (len(self.fractions), len(self.phases), m))

            self._observe_specimens()
            self._observe_phases()

            self.optimizer = Optimizer(parent=self)
            self.refinement = Refinement(
                refine_method_index=self.get_kwarg(kwargs, 0, "refine_method_index", "refine_method", "data_refine_method"),
                refine_options=self.get_kwarg(kwargs, dict(), "refine_options"),
                parent=self)

            self.update()

            self.observe_model(self)

            pass # end hold data_changed

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @DataModel.observe("removed", signal=True)
    def notify_removed(self, model, prop_name, info):
        if model == self:
            self._relieve_phases()
            self._relieve_specimens()

    @DataModel.observe("needs_update", signal=True)
    def notify_needs_update(self, model, prop_name, info):
        with self.data_changed.hold():
            self.update()

    @DataModel.observe("data_changed", signal=True)
    def notify_data_changed(self, model, prop_name, info):
        if not model == self and not (
            info.arg == "based_on" and model.based_on is not None and
            model.based_on in self.phase_matrix):
                self.needs_update.emit()

    @DataModel.observe("visuals_changed", signal=True)
    def notify_visuals_changed(self, model, prop_name, info):
        if isinstance(model, Phase) and \
           not (info.arg == "based_on" and model.based_on is not None and model.based_on in self.phase_matrix):
            for i, specimen in enumerate(self.specimens):
                if specimen is not None:
                    specimen.update_visuals(self.phase_matrix[i, :])

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def json_properties(self):
        self.refinement.update_refinement_treestore()
        retval = Storable.json_properties(self)

        retval["phase_uuids"] = [[item.uuid if item else "" for item in row] for row in map(list, self.phase_matrix)]
        retval["specimen_uuids"] = [specimen.uuid if specimen else "" for specimen in self.specimens]
        retval["phases"] = self.phases
        retval["fractions"] = self.fractions.tolist()
        retval["fractions_mask"] = self.fractions_mask.tolist()
        retval["bgshifts"] = self.bgshifts.tolist()
        retval["scales"] = self.scales.tolist()

        return retval

    @staticmethod
    def from_json(**kwargs):
        # Remove this deprecated kwarg:
        if "refinables" in kwargs:
            del kwargs["refinables"]
        return Mixture(**kwargs)

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def unset_phase(self, phase):
        """ Clears a phase slot in the phase matrix """
        with self.needs_update.hold_and_emit():
            with self.data_changed.hold():
                shape = self.phase_matrix.shape
                with self._relieve_and_observe_phases():
                    for i in range(shape[0]):
                        for j in range(shape[1]):
                            if self.phase_matrix[i, j] == phase:
                                self.phase_matrix[i, j] = None
                self.refinement.update_refinement_treestore()

    def unset_specimen(self, specimen):
        """ Clears a specimen slot in the specimen list """
        with self.needs_update.hold_and_emit():
            with self.data_changed.hold():
                with self._relieve_and_observe_specimens():
                    for i, spec in enumerate(self.specimens):
                        if spec == specimen:
                            self.specimens[i] = None

    def get_phase(self, specimen_slot, phase_slot):
        """Returns the phase at the given slot positions or None if not set"""
        return self.phase_matrix[specimen_slot, phase_slot]

    def set_phase(self, specimen_slot, phase_slot, phase):
        """Sets the phase at the given slot positions"""
        if self.parent is not None: #no parent = no valid phases
            with self.needs_update.hold_and_emit():
                with self.data_changed.hold():
                    with self._relieve_and_observe_phases():
                        if phase is not None and not phase in self.parent.phases:
                            raise RuntimeError("Cannot add a phase to a Mixture which is not inside the project!")
                        self.phase_matrix[specimen_slot, phase_slot] = phase
                    self.refinement.update_refinement_treestore()

    def get_specimen(self, specimen_slot):
        """Returns the specimen at the given slot position or None if not set"""
        return self.specimens[specimen_slot]

    def set_specimen(self, specimen_slot, specimen):
        """Sets the specimen at the given slot position"""
        if self.parent is not None: #no parent = no valid specimens
            with self.needs_update.hold_and_emit():
                with self.data_changed.hold():
                    with self._relieve_and_observe_specimens():
                        if specimen is not None and not specimen in self.parent.specimens:
                            raise RuntimeError("Cannot add a specimen to a Mixture which is not inside the project!")
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
        with self.needs_update.hold_and_emit():
            with self.data_changed.hold():
                self.phases.append(phase_name)
                self.fractions = np.append(self.fractions, fraction)
                self.fractions_mask = np.append(self.fractions_mask, 1)
                n, m = self.phase_matrix.shape if self.phase_matrix.ndim == 2 else (0, 0)
                if self.phase_matrix.size == 0:
                    self.phase_matrix = np.resize(self.phase_matrix.copy(), (n, m + 1))
                    self.phase_matrix[:] = None
                else:
                    self.phase_matrix = np.concatenate([self.phase_matrix.copy(), [[None]] * n ], axis=1)
                    self.phase_matrix[:, m] = None
                self.refinement.update_refinement_treestore()
        return m

    def del_phase_slot(self, phase_slot):
        """ Deletes a phase column using its index """
        with self.needs_update.hold_and_emit():
            with self.data_changed.hold():
                with self._relieve_and_observe_phases():
                    # Remove the corresponding phase name, fraction & references:
                    del self.phases[phase_slot]
                    self.fractions = np.delete(self.fractions, phase_slot)
                    self.fractions_mask = np.delete(self.fractions_mask, phase_slot)
                    self.phase_matrix = np.delete(self.phase_matrix, phase_slot, axis=1)
                # Update our refinement tree store to reflect current state
                self.refinement.update_refinement_treestore()
        # Inform any interested party they need to update their representation
        self.needs_reset.emit()

    def del_phase_slot_by_name(self, phase_name):
        """ Deletes a phase slot using its name """
        self.del_phase_slot(self.phases.index(phase_name))

    def add_specimen_slot(self, specimen, scale, bgs):
        """ Adds a new specimen to the phase matrix (a row) and specimen list """
        with self.needs_update.hold_and_emit():
            with self.data_changed.hold():
                self.specimens.append(None)
                self.scales = np.append(self.scales, scale)
                self.bgshifts = np.append(self.bgshifts, bgs)
                n, m = self.phase_matrix.shape if self.phase_matrix.ndim == 2 else (0, 0)
                if self.phase_matrix.size == 0:
                    self.phase_matrix = np.resize(self.phase_matrix.copy(), (n + 1, m))
                    self.phase_matrix[:] = None
                else:
                    self.phase_matrix = np.concatenate([self.phase_matrix.copy(), [[None] * m] ], axis=0)
                    self.phase_matrix[n, :] = None
                if specimen is not None:
                    self.set_specimen(n, specimen)
        return n

    def del_specimen_slot(self, specimen_slot):
        """ Deletes a specimen slot using its slot index """
        with self.needs_update.hold_and_emit():
            with self.data_changed.hold():
                # Remove the corresponding specimen name, scale, bg-shift & phases:
                with self._relieve_and_observe_specimens():
                    del self.specimens[specimen_slot]
                    self.scales = np.delete(self.scales, specimen_slot)
                    self.bgshifts = np.delete(self.bgshifts, specimen_slot)
                    self.phase_matrix = np.delete(self.phase_matrix, specimen_slot, axis=0)
                # Update our refinement tree store to reflect current state
                self.refinement.update_refinement_treestore()
        # Inform any interested party they need to update their representation
        self.needs_reset.emit()

    def del_specimen_slot_by_object(self, specimen):
        """ Deletes a specimen slot using the actual object """
        try:
            self.del_specimen_slot(self.specimens.index(specimen))
        except ValueError:
            logger.exception("Caught a ValueError when deleting a specimen from  mixture '%s'" % self.name)

    # ------------------------------------------------------------
    #      Refinement stuff:
    # ------------------------------------------------------------
    def set_data_object(self, mixture, calculate=False):
        """
            Sets the fractions, scales and bgshifts of this mixture.
        """
        if mixture is not None:
            with self.needs_update.ignore():
                with self.data_changed.hold_and_emit():
                    self.fractions[:] = list(mixture.fractions)
                    self.scales[:] = list(mixture.scales)
                    self.bgshifts[:] = list(mixture.bgshifts)

                    # reset flag when needed:
                    mixture.calculated = mixture.calculated and not calculate
                    mixture = self.optimizer.calculate(mixture)

                    for i, (specimen_data, specimen) in enumerate(zip(mixture.specimens, self.specimens)):
                        if specimen is not None:
                            with specimen.data_changed.ignore():
                                specimen.update_pattern(
                                    specimen_data.total_intensity,
                                    specimen_data.scaled_phase_intensities,
                                    self.phase_matrix[i, :]
                                )

    def optimize(self):
        """
            Optimize the current solution (fractions, scales, bg shifts & calculate
            phase intensities)
        """
        with self.needs_update.ignore():
            with self.data_changed.hold():
                # no need to re-calculate, is already done by the optimization
                self.set_data_object(self.optimizer.optimize())

    def apply_current_data_object(self):
        """
            Recalculates the intensities using the current fractions, scales
            and bg shifts without optimization
        """
        with self.needs_update.ignore():
            with self.data_changed.hold():
                self.set_data_object(self.data_object, calculate=True)

    # @print_timing
    def update(self):
        """
            Optimizes or re-applies the current mixture 'solution'.
            Effectively re-calculates the entire patterns.
        """
        with self.needs_update.ignore():
            with self.data_changed.hold():
                if self.auto_run:
                    self.optimize()
                else:
                    self.apply_current_data_object()

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
            next(reader) # skip header
            for row in reader:
                nr, name, fact = row
                atom_conv[int(nr)] = (name, float(fact))

        comps = list()
        for i, row in enumerate(self.phase_matrix):
            comp = dict()
            for j, phase in enumerate(row):
                phase_fract = self.fractions[j]
                for k, component in enumerate(phase.components):
                    comp_fract = phase.probabilities.mW[k] * phase_fract
                    for atom in chain(component.layer_atoms,
                            component.interlayer_atoms):
                        nr = atom.atom_type.atom_nr
                        if nr in atom_conv:
                            wt = atom.pn * atom.atom_type.weight * comp_fract * atom_conv[nr][1]
                            comp[nr] = comp.get(nr, 0.0) + wt
            comps.append(comp)

        final_comps = np.zeros(shape=(len(atom_conv) + 1, len(comps) + 1), dtype='a15')
        final_comps[0, 0] = " "*8
        for j, comp in enumerate(comps):
            fact = 100.0 / sum(comp.values())
            for i, (nr, (oxide_name, conv)) in enumerate(atom_conv.items()):
                wt = comp.get(nr, 0.0) * fact
                # set relevant cells:
                if i == 0:
                    final_comps[i, j + 1] = self.specimens[j].name.ljust(15)[:15]
                if j == 0:
                    final_comps[i + 1, j] = ("%s  " % oxide_name).rjust(8)[:8]
                final_comps[i + 1, j + 1] = ("%.1f" % wt).ljust(15)[:15]

        return final_comps

    pass # end of class
