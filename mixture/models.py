# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from traceback import format_exc

from warnings import warn
import time
from math import pi

import gtk
import gobject
from gtkmvc.model import Model, Signal
import numpy as np
import scipy

import settings

from generic.io import storables, Storable
from generic.utils import print_timing, delayed
from generic.models import ChildModel, PropIntel, MultiProperty
from generic.models.mixins import ObjectListStoreChildMixin
from generic.models.metaclasses import pyxrd_object_pool
from generic.models.treemodels import ObjectTreeStore

from generic.refinement.mixins import _RefinementBase, RefinementValue, RefinementGroup
from generic.refinement.wrapper import RefinableWrapper

from specimen.models import Statistics

from mixture.genetics import run_genetic_algorithm


class RefineContext(ChildModel):
    __parent_alias__ = "mixture"
    
    objective_function = None
    initial_solution = None
    initial_residual = None

    last_solution = None
    last_residual = None
    
    best_solution = None
    best_residual = None
    
    ref_props = None
    values = None
    ranges = None

    def __init__(self, parent=None, **kwargs):
        super(RefineContext, self).__init__(parent=parent)
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
            
        if self.initial_solution == None:
            self.initial_solution = np.array(self.values, dtype=float)    
        if self.last_solution == None:
            self.last_solution = np.array(self.values, dtype=float)        
        if self.last_residual == None:
            self.last_residual = self.initial_residual
            
        self.status = "created"

    def apply_solution(self, solution):
        for i, ref_prop in enumerate(self.ref_props):
            if not (solution.shape==()):
                ref_prop.value = solution[i]
            else:
                ref_prop.value = solution[()]
        return self.mixture.optimizer.optimize(silent=True, method=0)

    def update(self, solution):
        residual = self.apply_solution(solution)   
        if self.best_residual==None or self.best_residual > residual:
            self.best_residual = residual
            self.best_solution = solution
            
    def apply_best_solution(self):
        self.apply_solution(self.best_solution)

    def apply_last_solution(self):
        self.apply_solution(self.last_solution)

    def apply_initial_solution(self):
        self.apply_solution(self.initial_solution)
            
    pass #end of class

def refine_lbfgsb_run(context):
    context.last_solution, context.last_residual, d = scipy.optimize.fmin_l_bfgs_b(
        context.objective_function,
        context.initial_solution,
        approx_grad=True, 
        bounds=context.ranges, 
        args=[],
        factr=1e6,
        iprint=-1
    )

class Refiner(ChildModel):
    __parent_alias__ = "mixture"

    refine_methods = [
        (0, "L BFGS B algorithm", "refine_lbfgsb_run"), 
        (1, "Genetic algorithm", ""), #FIXME TODO
        (100, "Brute force algorithm", ""), #FIXME TODO
    ]

    def get_context(self):
        ref_props = []
        values = []
        ranges = tuple()
    
        for ref_prop in self.mixture.refinables.iter_objects():
            if ref_prop.refine and ref_prop.refinable:
                ref_props.append(ref_prop)
                values.append(ref_prop.value)
                ranges = ranges + ((ref_prop.value_min, ref_prop.value_max),)
        initial_residual = self.mixture.optimizer.get_current_residual()

        return RefineContext(
            parent=self.parent,
            ref_props = ref_props,
            values = values,
            ranges = ranges,
            initial_residual = initial_residual
        )

    refine_lock = False
    def refine(self, params):
        """
            This refines the selected properties using the selected algorithm.
            This should be run asynchronously to keep the GUI from blocking.
        """
        if not self.refine_lock:
            # Set lock
            self.refine_lock = True            
        
            # Suppres updates:
            self.mixture.project.freeze_updates()
                       
            # Extract the info we need from our mixture, and create a context:
            if getattr(self, "context", None) != None:
                self.context.parent = None
                del self.context
            self.context = self.get_context()
              
            # If something has been selected: continue...                      
            if len(self.context.ref_props) > 0:
                self.context.best_residual, self.context.best_solution = None, None
                
                # The objective function:
                # needs to be declared inline as it needs acces to the params
                # dict.
                def get_residual_from_solution(solution):
                    if not (params["kill"] or params["stop"]):
                        self.context.update(solution)
                        time.sleep(0.05)
                        return self.context.last_residual
                    elif params["kill"]:
                        raise GeneratorExit
                    elif params["stop"]:
                        raise StopIteration
    
                self.context.objective_function = get_residual_from_solution
                       
                #Run until it ends or it raises an exception:     
                try:
                    if self.mixture.refine_method==0: #L BFGS B
                        refine_lbfgsb_run(self.context)
                    elif self.mixture.refine_method==1: #GENETIC ALGORITHM
                        run_genetic_algorithm(self.context) #FIXME TODO
                    elif self.mixture.refine_method==100: #BRUTE FORCE, only for scripting FIXME TODO
                        last_solution, last_residual, val_grid, residual_grid  = scipy.optimize.brute(
                            get_residual_from_solution,
                            ranges,
                            Ns=10,
                            full_output=1,
                            finish=None
                        )
                except StopIteration:
                    self.context.last_solution, self.context.last_residual = self.best_solution, self.best_residual
                    self.context.status = "stopped"
                except GeneratorExit:
                    pass #no action needed
                    self.context.status = "finished"
                except any as error:
                    print "Handling run-time error: %s" % error
                    print format_exc()
                    self.context.status = "error"
            else: #nothing selected for refinement
                self.context.status = "error"
                
            #Unluck the GUI & this method
            self.refine_lock = False
            self.mixture.project.thaw_updates()
                
            #Return the context to whatever called this
            return self.context

    pass #end of class

class Optimizer(ChildModel):
    __parent_alias__ = "mixture"
    
    def get_current_residual(self):
        return self.get_residual(
            self.mixture.get_current_solution(), 
            self.get_residual_parts()
        )
        
    def get_residual_parts(self):
        """
            Returns a tuple containing:
             - current number of phases `n`
             - current number of specimens `m`
             - a list of `m` numpy arrays containing `n` calculated phase patterns
             - a list of `m`experimental patterns
             - a list of `m` selectors (based on exclusion ranges)
            Using this information, it is possible to calculate the residual for
            any bg_shift or scales value.
        """
        #1 get the different intensities for each phase for each specimen 
        #  -> each specimen gets a 2D np-array of size m,t with:
        #         m the number of phases        
        #         t the number of data points for that specimen
        n, m = self.mixture.phase_matrix.shape
        calculated = [None]*n
        experimental = [None]*n
        selectors = [None]*n
        todeg = 360.0 / pi
        for i in range(n):
            phases = self.mixture.phase_matrix[i]
            specimen = self.mixture.specimens[i]
            if specimen!=None:
                theta_range, calc = specimen.get_phase_intensities(phases, self.mixture.project.goniometer.get_lorentz_polarisation_factor)
                calculated[i] = calc.copy()
                experimental[i] = specimen.experimental_pattern.xy_store.get_raw_model_data()[1].copy()
                selectors[i] = specimen.get_exclusion_selector(theta_range*todeg)
        return n, m, calculated, experimental, selectors
    
    def get_residual(self, solution, residual_parts=None):
        """
            Calculates the residual for the given solution in combination with
            the given residual parts. If residual_parts is None,
            the method calls get_residual_parts.
        """
        tot_rp = 0.0
        n, m, calculated, experimental, selectors = residual_parts if residual_parts else self.get_residual_parts()
        fractions, scales, bgshifts = self.mixture.parse_solution(solution, n, m)
        for i in range(n):
            if calculated[i]!=None and experimental[i].size > 0:
                calc = (scales[i] * np.sum(calculated[i]*fractions, axis=0)) 
                if settings.BGSHIFT:
                    calc += bgshifts[i]
                exp = experimental[i][selectors[i]]
                cal = calc[selectors[i]]
                tot_rp += Statistics._calc_Rp(exp, cal)
        return tot_rp

    def optimize(self, silent=False, method=0):
        """
            Optimizes the mixture fractions, scales and bg shifts.
        """
        #1. get stuff that doesn't change:
        residual_parts = self.get_residual_parts()
        n, m, calculated, experimental, selectors = residual_parts

        #2. define the objective function:
        def get_residual_from_solution(solution, *args):
            return self.get_residual(solution, residual_parts)
            
        #3. optimize the fractions:         
        x0 = self.mixture.get_current_solution()
        bounds = [(0,None) for el in x0]
        lastx, lastR2 = None, None
        if method == 0: #L BFGS B
            iprint = -1 # if not settings.DEBUG else 0
            lastx, lastR2, info = scipy.optimize.fmin_l_bfgs_b(get_residual_from_solution, x0, approx_grad=True, factr=1000, bounds=bounds, iprint=iprint)
        elif method == 1: #SIMPLEX
            disp = 0
            lastx, lastR2, itr, funcalls, warnflag = scipy.optimize.fmin(get_residual_from_solution, x0, disp=disp, full_output=True)
        elif method == 3: #truncated Newton algorithm
             disp = 0
             lastx, nfeval, rc = scipy.optimize.fmin_tnc(get_residual_from_solution, x0, approx_grad=True, epsilon=0.05, bounds=bounds, disp=disp)
       
        #rescale scales and fractions so they fit into [0-1] range, and round them to have 6 digits max:
        fractions, scales, bgshifts = self.mixture.parse_solution(lastx, n, m)
        fractions = fractions.flatten()
        scales = scales.round(6)
        if settings.BGSHIFT:
            bgshifts = bgshifts.round(6)
        
        sum_frac = np.sum(fractions)
        fractions = np.around((fractions / sum_frac), 6)
        scales *= sum_frac

        #set model properties:        
        self.mixture.set_solution(fractions, scales, bgshifts)
                
        return lastR2

    pass #end of class


@storables.register()
class Mixture(ChildModel, ObjectListStoreChildMixin, Storable):
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
    refine_method = MultiProperty(0, int, None, { value: name for value, name, func in Refiner.refine_methods })
    
    #Lists and matrices:
    phase_matrix = None
    
    specimens = None
    scales = None
    bgshifts = None
    
    phases = None
    fractions = None

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, name="New Mixture", auto_run=False, 
            phase_indeces=None, phase_uuids=None, 
            specimen_indeces=None, specimen_uuids=None, phases=None,
            scales=None, bgshifts=None, fractions=None, 
            refinables=None, refine_method=None, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
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
        
        #list with scale values, indexes match with rows in phase_matrix
        self.scales = scales or self.get_depr(kwargs, list(), "data_scales")
        #list with specimen background shift values, indexes match with rows in phase_matrix        
        self.bgshifts = bgshifts or self.get_depr(kwargs, [0.0]*len(self.scales), "data_bgshifts")
        #list with mixture phase names, indexes match with cols in phase_matrix
        self.phases = phases or self.get_depr(kwargs, list(), "data_phases")
        #list with phase fractions, indexes match with cols in phase_matrix
        self.fractions = fractions or self.get_depr(kwargs, [0.0]*len(self.phases), "data_fractions")
        
        self.refinables = refinables or self.get_depr(kwargs, ObjectTreeStore(RefinableWrapper), "data_refinables")
        self.refine_method = refine_method or self.get_depr(kwargs, self.refine_method, "data_refine_method")
        
        #sanity check:
        n, m = self.phase_matrix.shape
        if len(self.scales) != n or len(self.specimens) != n or len(self.bgshifts) != n:
            raise IndexError, "Shape mismatch: scales, background shifts or specimens lists do not match with row count of phase matrix"
        if len(self.phases) != m or len(self.fractions) != m:
            raise IndexError, "Shape mismatch: fractions or phases lists do not match with column count of phase matrix"
    
        self.optimizer = Optimizer(parent=self)
        self.refiner = Refiner(parent=self)
    
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------   
    def json_properties(self):
        self.update_refinement_treestore()
        retval = Storable.json_properties(self)

        retval["phase_uuids"] = [[item.uuid if item else "" for item in row] for row in map(list, self.phase_matrix)]            
        retval["specimen_uuids"] = [specimen.uuid if specimen else "" for specimen in self.specimens]
        retval["phases"] = self.phases
        retval["fractions"] = self.fractions
        retval["bgshifts"] = self.bgshifts
        retval["scales"] = self.scales
        
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
            self.fractions.append(fraction)
            self.phase_matrix = np.concatenate([self.phase_matrix.copy(), [[None,] for n in range(n)]], axis=1)        
            self.update_refinement_treestore()
            self.has_changed.emit()
            return m
        else:
            return -1

    def _del_phase_by_index(self, index):
        """ Deletes a phase column using its index """
        del self.phases[index]
        del self.fractions[index]
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
        self.scales.append(scale)
        self.bgshifts.append(bgs)
        n, m = self.phase_matrix.shape
        self.phase_matrix = np.concatenate([self.phase_matrix.copy(), [[None]*m] ], axis=0)
        self.phase_matrix[n,:] = None
        self.has_changed.emit()
        return n

    def _del_specimen_by_index(self, index):
        """ Deletes a specimen row using its index """
        del self.specimens[index]
        del self.scales[index]
        del self.bgshifts[index]
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
    def get_current_solution(self):
        """ 
            Compiles an initial solution (x0) using the current fractions, 
            scales and background shifts.
        """
        return np.array(self.fractions + self.scales + self.bgshifts)

    def parse_solution(self, solution, n, m):
        """ 
            Decompiles a solution into m fractions, n scales and n bgshifts,
            m and n being the number of phases and specimens respectively.
        """
        fractions =  solution[:m][:,np.newaxis]
        scales = solution[m:m+n]
        bgshifts = solution[-n:] if settings.BGSHIFT else np.zeros(shape=(n,))
        return fractions, scales, bgshifts
    
    def set_solution(self, fractions=None, scales=None, bgshifts=None, solution=None, m=None, n=None, apply=True):
        """
            Sets the fractions, scales and bgshifts of this mixture and emits
            a signal indicating they have changed.
            You can choose to pass either the fractions, scales and bgshifts as
            separate lists or to pass a solution array with the m and n values.
        """
        if solution!=None:
            assert m!=None, "If you pass the solution keyword, you need to pass the m keyword argument as well!"
            assert n!=None, "If you pass the solution keyword, you need to pass the n keyword argument as well!"
            fractions, scales, bgshifts = self.parse_solution(solution, m, n)
        
        self.fractions = list(fractions)
        self.scales = list(scales)
        self.bgshifts = list(bgshifts) if settings.BGSHIFT else [0]*n
        
        if apply:
            self.apply_current_solution()
        
        self.has_changed.emit()
       
    def apply_current_solution(self):
        for i, specimen in enumerate(self.specimens):
            if specimen!=None:
                specimen.abs_scale = self.scales[i]
                specimen.bg_shift = self.bgshifts[i]
                specimen.update_pattern(
                    self.phase_matrix[i,:],
                    self.fractions
                )
       
    def get_result_description(self):
        n, m = self.phase_matrix.shape
        
        res  = "---------------------------------------------------------\n"        
        res += "%s mixture results\n" % self.name
        res += "---------------------------------------------------------\n"
        res += "\n   %d specimens:\n" % n
        for i in range(n):
            res += "       - %s   bgr: %5.2f   scl: %5.2f\n" % (self.specimens[i].name.ljust(15), self.bgshifts[i], self.scales[i])
        res += "    (bgr=background shift, scl=absolute scale factor)\n"
        res += "\n   %d phases:\n" % m
       
        phase_props = [
            "name",
            "wt%",
            "sigma_star",
            "T_mean",
            "probs",
        ]
        comp_props = [
            "name",
            "wt%",
            "d-spacing",
            "relations",
        ]
        
        phases = np.unique(self.phase_matrix)
        max_G = 1
        for phase in phases:
            max_G = max(phase.G, max_G)
      
        num_rows = len(phase_props) + len(comp_props) * max_G
        num_cols = phases.size + 1
        
        text_matrix = np.zeros(shape=(num_rows, num_cols), dtype=object)
        text_matrix[:] = ""
        i = 1
        for phase_index in range(m):
            phases = np.unique(self.phase_matrix[:,phase_index])
            for phase in phases:
                j = 0
                for prop in phase_props:
                    text_matrix[j,0] = prop
                    text = ""         
                    if prop=="name":
                        text = "%s" % phase.name
                    elif prop=="wt%":
                        text = "%.1f" % (self.fractions[phase_index]*100.0)
                    elif prop=="sigma_star":
                        text = "%.1f" % phase.sigma_star
                    elif prop=="T_mean":
                        text = "%.1f" % phase.CSDS_distribution.average
                    elif prop=="probs":
                        text += "\""
                        for descr in phase.probabilities.get_prob_descriptions():
                            text += "%s\n" % descr
                        text += "\""
                    text_matrix[j,i] = text
                    j += 1
                for k, component in enumerate(phase.components.iter_objects()):
                    for prop in comp_props:
                        text_matrix[j,0] = prop
                        text = ""
                        if prop=="name":
                            text = "%s" % component.name                        
                        elif prop=="wt%":
                            text = "%.1f" % (phase.probabilities.mW[k]*100)
                        elif prop=="d-spacing":
                            text = "%.3f" % component.cell_c
                            if component.delta_c != 0:
                                text += " +/- %s" % component.delta_c
                        elif prop=="relations":
                            text += "\""
                            for relation in component.atom_relations.iter_objects():
                                text += "%s: %.3f\n" % (relation.name, relation.value)
                            text += "\""
                        text_matrix[j,i] = text
                        j += 1
                i += 1           
        return text_matrix
            
    def get_composition_matrix(self):
        """
            Returns a matrix containing the oxide composition for each specimen 
            in this mixture. It uses the COMPOSITION_CONV file for this purpose
            to convert element weights into their oxide weight equivalent.
        """
        from itertools import chain
        from collections import OrderedDict
        import csv
        
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
            if phase in self.phase_matrix: parse_attribute(phase, None, None)
        
    def auto_restrict(self): #TODO FIXME
        """
            Convenience function that restricts the selected properties 
            automatically by setting their minimum and maximum values.
        """
        for ref_prop in self.refinables.iter_objects():
            if ref_prop.refine and ref_prop.refinable:
                ref_prop.value_min = ref_prop.value * 0.95
                ref_prop.value_max = ref_prop.value * 1.05
        return
                
    pass #end of class
    

