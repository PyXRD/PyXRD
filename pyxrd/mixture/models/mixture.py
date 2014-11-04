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
import logging
from pyxrd.generic.models.signals import HoldableSignal
logger = logging.getLogger(__name__)

from mvc import Signal, PropIntel, OptionPropIntel
from mvc.models import TreeNode

import numpy as np

from pyxrd.data import settings

from pyxrd.generic.io import storables, Storable
# from pyxrd.generic.utils import print_timing
from pyxrd.generic.models import DataModel

from pyxrd.generic.refinement.mixins import RefinementValue, RefinementGroup
from pyxrd.generic.refinement.wrapper import RefinableWrapper
from pyxrd.calculations.data_objects import MixtureData

from pyxrd.phases.models.phase import Phase

from .methods import get_all_refine_methods
from .optimizers import Optimizer
from .refiner import Refiner

@storables.register()
class Mixture(DataModel, Storable):
    """
        The base model for optimization and refinement of calculated data
        and experimental data. This is the main model you want to interact with,
        lower-level classes' functionality (mainly 
        :class:`~pyxrd.mixture.models.optimizers.Optimizer` and 
        :class:`~pyxrd.mixture.models.refiner.Refiner`) are integrated into this
        class. 
        
        The Mixture is responsible for managing the phases and specimens lists
        and combination-matrix and for delegating any optimization, calculation
        or refinement calls to the appropriate helper class.
    """
    # MODEL INTEL:
    class Meta(DataModel.Meta):
        all_refine_methods = get_all_refine_methods()
        properties = [ # TODO add labels
            PropIntel(name="name", label="Name", data_type=unicode, is_column=True, storable=True, has_widget=True),
            PropIntel(name="refinables", label="", data_type=object, is_column=True, has_widget=True, widget_type="object_tree_view", class_type=RefinableWrapper),
            PropIntel(name="make_psp_plots", label="", data_type=bool, is_colum=False, has_widget=True, storable=False),
            PropIntel(name="auto_run", label="", data_type=bool, is_column=True, storable=True, has_widget=True),
            PropIntel(name="auto_bg", label="", data_type=bool, is_column=True, storable=True, has_widget=True),
            OptionPropIntel(name="refine_method", label="Refinement method", data_type=int, storable=True, has_widget=True, options={ key: method.name for key, method in all_refine_methods.iteritems() }),
            PropIntel(name="needs_update", label="", data_type=object, storable=False), # Signal used to indicate the mixture needs an update
            PropIntel(name="needs_reset", label="", data_type=object, storable=False,), # Signal used to indicate the mixture matrix needs to be re-built...
        ]
        store_id = "Mixture"

    _data_object = None
    @property
    def data_object(self):
        self._data_object.specimens = [None] * len(self.specimens)
        self._data_object.auto_bg = self.auto_bg
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

    project = property(DataModel.parent.fget, DataModel.parent.fset)

    # SIGNALS:
    #: Signal, emitted when the # of phases or specimens changes
    needs_reset = None
    #: Signal, emitted when the patterns of the specimens need an update
    needs_update = None

    # INTERNALS:
    _name = ""
    @property
    def name(self):
        """ The name of this mixture """
        return self._name
    @name.setter
    def name(self, value):
        self._name = value
        self.visuals_changed.emit()

    #: The tree of refinable properties
    refinables = None
    #: Flag, True if after refinement plots should be generated of the parameter space
    make_psp_plots = False
    #: Flag, True if the mixture will automatically adjust phase fractions and scales
    auto_run = False
    #: Flag, True if the mixture is allowed to also update the background level
    auto_bg = True

    _refine_method = 0
    @property
    def refine_method(self):
        """ An integer describing which method to use for the refinement (see 
        mixture.models.methods.get_all_refine_methods) """
        return self._refine_method
    @refine_method.setter
    def refine_method(self, value): self._refine_method = int(value)

    #: A dict containing the refinement options
    refine_options = None # TODO make this storable!

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
            "data_fractions", "data_refine_method", "fractions",
            "bgshifts", "scales", "phases",
            *[names[0] for names in type(self).Meta.get_local_storable_properties()]
        )
        super(Mixture, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        with self.data_changed.hold():

            self._data_object = MixtureData()

            self.needs_reset = Signal()
            self.needs_update = HoldableSignal()
            self.name = self.get_kwarg(kwargs, "New Mixture", "name", "data_name")
            self.auto_run = self.get_kwarg(kwargs, False, "auto_run")
            self.auto_bg = self.get_kwarg(kwargs, True, "auto_bg")

            # 2D matrix, rows match specimens, columns match mixture 'phases'; contains the actual phase objects
            phase_uuids = self.get_kwarg(kwargs, None, "phase_uuids")
            phase_indeces = self.get_kwarg(kwargs, None, "phase_indeces")
            if phase_uuids is not None:
                self.phase_matrix = np.array([[type(type(self)).object_pool.get_object(uuid) if uuid else None for uuid in row] for row in phase_uuids], dtype=np.object_)
            elif phase_indeces and self.parent is not None:
                warn("The use of object indices is deprecated since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
                self.phase_matrix = np.array([[self.parent.phases.get_user_data_from_index(index) if index != -1 else None for index in row] for row in phase_indeces], dtype=np.object_)
            else:
                self.phase_matrix = np.empty(shape=(0, 0), dtype=np.object_)

            # list with actual specimens, indexes match with rows in phase_matrix
            specimen_uuids = self.get_kwarg(kwargs, None, "specimen_uuids")
            specimen_indeces = self.get_kwarg(kwargs, None, "specimen_indeces")
            if specimen_uuids:
                self.specimens = [type(type(self)).object_pool.get_object(uuid) if uuid else None for uuid in specimen_uuids]
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

            self.refinables = TreeNode()
            try:
                self.refine_method = int(self.get_kwarg(kwargs, self.refine_method, "refine_method", "data_refine_method"))
            except ValueError:
                self.refine_method = self.refine_method
                pass # ignore faulty values, these indices change from time to time.

            # sanity check:
            n, m = self.phase_matrix.shape if self.phase_matrix.ndim == 2 else (0, 0)
            if len(self.scales) != n or len(self.specimens) != n or len(self.bgshifts) != n:
                raise IndexError, "Shape mismatch: scales (%d), background shifts (%d) or specimens (%d) list lengths do not match with row count (%d) of phase matrix" % (len(self.scales), len(self.specimens), len(self.bgshifts), n)
            if len(self.phases) != m or len(self.fractions) != m:
                raise IndexError, "Shape mismatch: fractions or phases lists do not match with column count of phase matrix"

            self.optimizer = Optimizer(parent=self)
            self.refiner = Refiner(parent=self)

            self._observe_specimens()
            self._observe_phases()
            self.update_refinement_treestore()
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


    internal_recurs = False
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
                self.update_refinement_treestore()

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
                            raise RuntimeError, "Cannot add a phase to a Mixture which is not inside the project!"
                        self.phase_matrix[specimen_slot, phase_slot] = phase
                    self.update_refinement_treestore()

    def get_specimen(self, specimen_slot):
        """Returns the specimen at the given slot position or None if not set"""
        return self.specimens[specimen_slot]

    def set_specimen(self, specimen_slot, specimen):
        """Sets the specimen at the given slot position"""
        if self.parent is not None: #no parent = no valid specimens
            with self.needs_update.hold_and_emit():
                with self._relieve_and_observe_specimens():
                    if specimen is not None and not specimen in self.parent.specimens:
                        raise RuntimeError, "Cannot add a specimen to a Mixture which is not inside the project!"
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
                n, m = self.phase_matrix.shape if self.phase_matrix.ndim == 2 else (0, 0)
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
        with self.needs_update.hold_and_emit():
            with self.data_changed.hold():
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
                self.update_refinement_treestore()
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

                    if calculate: # (re-)calculate if requested:
                        mixture = self.optimizer.calculate(mixture)

                    for i, (specimen_data, specimen) in enumerate(izip(mixture.specimens, self.specimens)):
                        if specimen is not None:
                            with specimen.data_changed.ignore():
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

    def update_refinement_treestore(self):
        """
            Called whenever the refinement view is opened, this creates a tree
            store with the refinable properties and their minimum, maximum and
            current value.
        """
        if self.parent is not None: # not linked so no valid phases!
            self.refinables.clear()

            def add_property(parent_node, obj, prop, is_grouper):
                rp = RefinableWrapper(obj=obj, prop=prop, parent=self, is_grouper=is_grouper)
                return parent_node.append(TreeNode(rp))

            def parse_attribute(obj, prop, root_node):
                """
                    obj: the object
                    attr: the attribute of obj or None if obj contains attributes
                    root_node: the root TreeNode new iters should be put under
                """
                if prop is not None:
                    if hasattr(obj, "get_uninherited_property_value"):
                        value = obj.get_uninherited_property_value(prop)
                    else:
                        value = getattr(obj, prop.name)
                else:
                    value = obj

                if isinstance(value, RefinementValue): # AtomRelation and UnitCellProperty
                    new_node = add_property(root_node, value, prop, False)
                elif hasattr(value, "__iter__"): # List or similar
                    for new_obj in value:
                        parse_attribute(new_obj, None, root_node)
                elif isinstance(value, RefinementGroup): # Phase, Component, Probability
                    if len(value.refinables) > 0:
                        new_node = add_property(root_node, value, prop, True)
                        for prop in value.refinables:
                            parse_attribute(value, prop, new_node)
                else: # regular values
                    new_node = add_property(root_node, obj, prop, False)

            for phase in self.parent.phases:
                if phase in self.phase_matrix:
                    parse_attribute(phase, None, self.refinables)

    def auto_restrict(self): # TODO set a restrict range attribute on the PropIntels, so we can use custom ranges for each property
        """
            Convenience function that restricts the selected properties 
            automatically by setting their minimum and maximum values.
        """
        with self.needs_update.hold():
            for node in self.refinables.iter_children():
                ref_prop = node.object
                if ref_prop.refine and ref_prop.refinable:
                    ref_prop.value_min = ref_prop.value * 0.8
                    ref_prop.value_max = ref_prop.value * 1.2

    def randomize(self):
        """
            Convenience function that randomize the selected properties.
            Respects the current minimum and maximum values.
            Executes an optimization after the randomization.
        """
        with self.data_changed.hold_and_emit():
            with self.needs_update.hold_and_emit():
                for node in self.refinables.iter_children():
                    ref_prop = node.object
                    if ref_prop.refine and ref_prop.refinable:
                        ref_prop.value = random.uniform(ref_prop.value_min, ref_prop.value_max)

    def get_refinement_method(self):
        """
            Returns the actual refinement method by translating the 
            `refine_method` attribute using the `Meta.all_refine_methods` dict
        """
        return self.Meta.all_refine_methods[self.refine_method]

    def setup_refine_options(self):
        """
            Constructs a refinement options dictionary containing default settings 
        """
        if self.refine_options == None:
            options = self.get_refinement_method().options
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
