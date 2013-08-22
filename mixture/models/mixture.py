# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import csv, copy
import random
from warnings import warn
from itertools import chain, izip
from collections import OrderedDict

from gtkmvc.model import Signal
import numpy as np

import settings

from generic.io import storables, Storable
from generic.models import ChildModel, PropIntel, MultiProperty
from generic.models.mixins import ObjectListStoreChildMixin
from generic.models.metaclasses import pyxrd_object_pool
from generic.models.treemodels import ObjectTreeStore

from generic.refinement.mixins import RefinementValue, RefinementGroup
from generic.refinement.wrapper import RefinableWrapper
from generic.calculations.data_objects import MixtureData

from .methods import get_all_refine_methods
from .optimizers import Optimizer


@storables.register()
class Mixture(ChildModel, ObjectListStoreChildMixin, Storable):
    """
        The base model for optimization and refinement of calculated data
        and experimental data. It uses two helper models to achieve this;
        the Optimize and Refiner. This model is responsible for storing
        any information worthy of storage and keeping the lists of phases and
        specimens aligned.
    """
    #MODEL INTEL:
    __parent_alias__ = "project"
    __model_intel__ = [ #TODO add labels
        PropIntel(name="name",             label="Name",    data_type=unicode,  is_column=True, storable=True, has_widget=True),
        PropIntel(name="refinables",       label="",        data_type=object,   is_column=True, has_widget=True),
        PropIntel(name="auto_run",         label="",        data_type=bool,     is_column=True, storable=True,  has_widget=True),
        PropIntel(name="refine_method",    label="",        data_type=int,      storable=True,  has_widget=True),
        PropIntel(name="has_changed",      label="",        data_type=object),
        PropIntel(name="needs_reset",      label="",        data_type=object,   storable=False,),
    ]
    __store_id__ = "Mixture"

    _data_object = None
    @property
    def data_object(self):
        self._data_object.specimens = [None] * len(self.specimens)
        for i, specimen in enumerate(self.specimens):
            if specimen!=None:
                data_object = specimen.data_object
                data_object.phases = [None] * len(self.phases)
                for j, phase in enumerate(self.phase_matrix[i,...].flatten()):
                    data_object.phases[j] = phase.data_object if phase!=None else None
                self._data_object.specimens[i] = data_object
            else:
                self._data_object.specimens[i] = None
        return self._data_object

    #SIGNALS:
    has_changed = None
    needs_reset = None

    #INTERNALS:
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
    refine_options = None #TODO make this storable!
    
    #Lists and matrices:
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
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, name="New Mixture", auto_run=False, 
            phase_indeces=None, phase_uuids=None, 
            specimen_indeces=None, specimen_uuids=None, phases=None,
            scales=None, bgshifts=None, fractions=None, 
            refinables=None, refine_method=None, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        
        self._data_object = MixtureData()
        
        self.has_changed = Signal()
        self.needs_reset = Signal()
        self.name = name or self.get_depr(kwargs, "", "data_name")
        self.auto_run = auto_run or self.auto_run
        
        #2D matrix, rows match specimens, columns match mixture 'phases'; contains the actual phase objects
        if phase_uuids:
            self.phase_matrix = np.array([[pyxrd_object_pool.get_object(uuid) if uuid else None for uuid in row] for row in phase_uuids], dtype=np.object_)
        elif phase_indeces and self.parent != None:
            warn("The use of object indeces is deprected since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
            self.phase_matrix = np.array([[self.parent.phases.get_user_data_from_index(index) if index!=-1 else None for index in row] for row in phase_indeces], dtype=np.object_)
        else:
            self.phase_matrix = np.empty(shape=(0,0), dtype=np.object_)
            
        #list with actual specimens, indexes match with rows in phase_matrix
        if phase_uuids:
            self.specimens = [pyxrd_object_pool.get_object(uuid) if uuid else None for uuid in specimen_uuids]            
        elif specimen_indeces != None and self.parent != None:
            warn("The use of object indeces is deprected since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
            self.specimens = [self.parent.specimens.get_user_data_from_index(index) if index!=-1 else None for index in specimen_indeces]
        else:
            self.specimens = list()

        #list with mixture phase names, indexes match with cols in phase_matrix
        self.phases = phases or self.get_depr(kwargs, list(), "data_phases")
                
        #list with scale values, indexes match with rows in phase_matrix (= specimens)
        self.scales = np.asarray(scales or self.get_depr(kwargs, [1.0]*len(self.specimens), "data_scales"))
        #list with specimen background shift values, indexes match with rows in phase_matrix (=specimens)
        self.bgshifts = np.asarray(bgshifts or self.get_depr(kwargs, [0.0]*len(self.specimens), "data_bgshifts"))
        #list with phase fractions, indexes match with cols in phase_matrix (=phases)
        self.fractions = np.asarray(fractions or self.get_depr(kwargs, [0.0]*len(self.phases), "data_fractions"))
                
        self.refinables = refinables or self.get_depr(kwargs, ObjectTreeStore(RefinableWrapper), "data_refinables")
        try:
            self.refine_method = refine_method or self.get_depr(kwargs, self.refine_method, "data_refine_method")
        except ValueError:
            self.refine_method = self.refine_method
            pass #ignore faulty values, these indeces change from time to time.
        
        #sanity check:
        n,m = self.phase_matrix.shape
        if len(self.scales) != n or len(self.specimens) != n or len(self.bgshifts) != n:
            raise IndexError, "Shape mismatch: scales (%d), background shifts (%d) or specimens (%d) list lengths do not match with row count (%d) of phase matrix" % (len(self.scales), len(self.specimens), len(self.bgshifts), n)
        if len(self.phases) != m or len(self.fractions) != m:
            raise IndexError, "Shape mismatch: fractions or phases lists do not match with column count of phase matrix"
    
        self.optimizer = Optimizer(parent=self)
        from refiner import Refiner
        self.refiner = Refiner(parent=self)
    
        self.update_refinement_treestore()
    
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
        shape = self.phase_matrix.shape
        for i in range(shape[0]):
            for j in range(shape[1]):
                if self.phase_matrix[i,j] == phase:
                    self.phase_matrix[i,j] = None
        self.update_refinement_treestore()
        self.has_changed.emit()
    
    def unset_specimen(self, specimen):
        """ Clears a specimen slot in the specimen list """
        for i, spec in enumerate(self.specimens):
            if spec==specimen:
                self.specimens[i] = None
        self.has_changed.emit()
    
    def add_phase(self, phase_name, fraction):
        """ Adds a new phase column to the phase matrix """
        n, m = self.phase_matrix.shape
        if n > 0:
            self.phases.append(phase_name)
            self.fractions = np.append(self.fractions, fraction)
            self.phase_matrix = np.concatenate([self.phase_matrix.copy(), [[None,] for n in range(n)]], axis=1)        
            self.update_refinement_treestore()
            self.has_changed.emit()
            return m
        else:
            return -1

    def _del_phase_by_index(self, index):
        """ Deletes a phase column using its index """
        del self.phases[index]
        self.fractions = np.delete(self.fractions, index)
        self.phase_matrix = np.delete(self.phase_matrix, index, axis=1)
        self.update_refinement_treestore()
        self.needs_reset.emit()

    def del_phase(self, phase_name):
        """ Deletes a phase column using its name """
        self._del_phase_by_index(self.phases.index(phase_name))
    
    def add_specimen(self, specimen, scale, bgs):
        """ Adds a new specimen to the phase matrix (a row) and specimen list """
        index = len(self.specimens)
        self.specimens.append(specimen)
        self.scales = np.append(self.scales, scale)
        self.bgshifts = np.append(self.bgshifts, bgs)
        n, m = self.phase_matrix.shape
        self.phase_matrix = np.concatenate([self.phase_matrix.copy(), [[None]*m] ], axis=0)
        self.phase_matrix[n,:] = None
        self.has_changed.emit()
        return n

    def _del_specimen_by_index(self, index):
        """ Deletes a specimen row using its index """
        del self.specimens[index]
        self.scales = np.delete(self.scales, index)
        self.bgshifts = np.delete(self.bgshifts, index)
        self.phase_matrix = np.delete(self.phase_matrix, index, axis=0)
        self.needs_reset.emit()

    def del_specimen(self, specimen):
        """ Deletes a specimen row using the actual object """
        try:
            self._del_specimen_by_index(self.specimens.index(specimen))
        except ValueError, msg:
            print "Caught a ValueError when deleting a specimen from mixture '%s': %s" % (self.name, msg)
    
    # ------------------------------------------------------------
    #      Refinement stuff:
    # ------------------------------------------------------------        
    def set_data_object(self, mixture, calculate=False, apply=True, silent=False):
        """
            Sets the fractions, scales and bgshifts of this mixture and emits
            a signal indicating they have changed.
        """
        self.fractions[:] = list(mixture.fractions)
        self.scales[:] = list(mixture.scales)
        self.bgshifts[:] = list(mixture.bgshifts)

        if calculate: #(re-)calculate if requested:
            mixture = self.optimizer.calculate(mixture)
        
        if apply:
            for i, (specimen_data, specimen) in enumerate(izip(mixture.specimens, self.specimens)):
                if specimen!=None:
                    specimen.update_pattern(
                        specimen_data.total_intensity,
                        specimen_data.phase_intensities,
                        self.phase_matrix[i,:]
                    )
            
        if not silent:
            self.has_changed.emit()
        
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
            reader.next() #skip header
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
               
        final_comps = np.zeros(shape=(len(atom_conv)+1, len(comps)+1), dtype='a15')
        final_comps[0,0] = " "*8
        for j, comp in enumerate(comps):
            fact = 100.0 / sum(comp.values())        
            for i, (nr, (oxide_name, conv)) in enumerate(atom_conv.iteritems()):
                wt = comp.get(nr, 0.0) * fact
                # set relevant cells:
                if i==0:
                    final_comps[i,j+1] = self.specimens[j].name.ljust(15)[:15]
                if j==0:
                    final_comps[i+1,j] = ("%s  " % oxide_name).rjust(8)[:8]
                final_comps[i+1,j+1] = ("%.1f" % wt).ljust(15)[:15]
                    
        return final_comps
       
    def update_refinement_treestore(self):
        """
            Called whenever the refinement view is opened, this creates a tree
            store with the refinable properties and their minimum, maximum and
            current value.
        """
        
        unique_phases = np.unique(self.phase_matrix.flatten())
        
        self.refinables.clear()
         
        def add_property(parent_itr, obj, prop):            
            rp = RefinableWrapper(obj, prop, sensitivity=0, refine=False, parent=self)
            return self.refinables.append(parent_itr, rp)
            
        def parse_attribute(obj, attr, root_itr):
            """
                obj: the object
                attr: the attribute of obj or None if obj is the attribute
                root_itr: the iter new iters should be put under
            """
            if attr!=None:
                if hasattr(obj, "get_base_value"):
                    value = obj.get_base_value(attr)
                else:
                    value = getattr(obj, attr) 
            else:
                value = obj
            
            if isinstance(value, RefinementValue): #Atom Ratios and UnitCellProperties
                new_itr = add_property(root_itr, value, None)
            elif hasattr(value, "iter_objects"): #object list store or similar
                for new_obj in value.iter_objects(): parse_attribute(new_obj, None, root_itr)
            elif isinstance(value, RefinementGroup): #Phases, Components, Probabilities
                if len(value.refinables) > 0:
                    new_itr = add_property(root_itr, value, None)
                    for new_attr in value.refinables: parse_attribute(value, new_attr, new_itr)
            else: #regular values
                new_itr = add_property(root_itr, obj, attr)
                    
        for phase in self.parent.phases.iter_objects():
            if phase in self.phase_matrix: 
                parse_attribute(phase, None, None)
        
    def auto_restrict(self): #TODO set a restrict range attribute on the PropIntels, so we can use custom ranges for each property
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
    
    pass #end of class
