# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

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

from generic.io import Storable
from generic.utils import print_timing, delayed
from generic.models import ChildModel, PropIntel, MultiProperty
from generic.models.mixins import ObjectListStoreChildMixin
from generic.models.metaclasses import pyxrd_object_pool
from generic.models.treemodels import ObjectTreeStore

from specimen.models import Statistics

from mixture.genetics import run_genetic_algorithm
from mixture.refinement import _RefinementBase, RefinementValue, RefinementGroup

class Mixture(ChildModel, ObjectListStoreChildMixin, Storable):
    #MODEL INTEL:
    __parent_alias__ = "project"
    __model_intel__ = [ #TODO add labels
        PropIntel(name="name",             label="Name",    data_type=str,      is_column=True, storable=True, has_widget=True),
        PropIntel(name="refinables",       label="",        data_type=object,   is_column=True, has_widget=True),
        PropIntel(name="auto_run",         label="",        data_type=bool,     is_column=True, storable=True,  has_widget=True),
        PropIntel(name="refine_method",    label="",        data_type=int,      storable=True,  has_widget=True),
        PropIntel(name="has_changed",      label="",        data_type=object),
        PropIntel(name="needs_reset",      label="",        data_type=object,   storable=False,),
    ]

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
    
    auto_run = False
    
    phase_matrix = None
    
    specimens = None
    scales = None
    bgshifts = None
    
    phases = None
    fractions = None

    refinables = None

    refine_method = MultiProperty(0, int, None, 
        { 0: "L BFGS B algorithm", 1: "Genetic algorithm", 100: "Brute force algorithm" })

    @property
    def current_rp(self):
        return self._calculate_total_rp(self._get_x0(), *self._get_rp_statics())

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
        
        self.refinables = refinables or self.get_depr(kwargs, ObjectTreeStore(RefinableProperty), "data_refinables")
        self.refine_method = refine_method or self.get_depr(kwargs, self.refine_method, "data_refine_method")
        
        #sanity check:
        n, m = self.phase_matrix.shape
        if len(self.scales) != n or len(self.specimens) != n or len(self.bgshifts) != n:
            raise IndexError, "Shape mismatch: scales, background shifts or specimens lists do not match with row count of phase matrix"
        if len(self.phases) != m or len(self.fractions) != m:
            raise IndexError, "Shape mismatch: fractions or phases lists do not match with column count of phase matrix"
    
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
        print "UNSET PHASE"
        shape = self.phase_matrix.shape
        for i in range(shape[0]):
            for j in range(shape[1]):
                if self.phase_matrix[i,j] == phase:
                    self.phase_matrix[i,j] = None
        self.update_refinement_treestore()
        self.has_changed.emit()
    
    def unset_specimen(self, specimen):
        for i, spec in enumerate(self.specimens):
            if spec==specimen:
                self.specimens[i] = None
        self.has_changed.emit()
    
    def add_phase(self, phase_name, fraction):
        print "ADD PHASE"
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
        del self.phases[index]
        del self.fractions[index]
        self.phase_matrix = np.delete(self.phase_matrix, index, axis=1)
        self.update_refinement_treestore()
        self.needs_reset.emit()

    def del_phase(self, phase_name):
        self._del_phase_by_index(self.phases.index(phase_name))
    
    def add_specimen(self, specimen, scale, bgs):
        index = len(self.specimens)
        self.specimens.append(specimen)
        self.scales.append(scale)
        self.bgshifts.append(bgs)
        n, m = self.phase_matrix.shape
        self.phase_matrix = np.concatenate([self.phase_matrix.copy(), [[None]*m] ], axis=0)
        self.phase_matrix[n,:] = None
        self.has_changed.emit()
        return n

    def _del_specimen_by_index(self, index): #FIXME
        del self.specimens[index]
        del self.scales[index]
        del self.bgshifts[index]
        self.phase_matrix = np.delete(self.phase_matrix, index, axis=0)
        self.needs_reset.emit()

    def del_specimen(self, specimen):
        try:
            self._del_specimen_by_index(self.specimens.index(specimen))
        except ValueError, msg:
            print "Caught a ValueError when deleting a specimen from mixture '%s': %s" % (self.name, msg)
    
    # ------------------------------------------------------------
    #      Refinement stuff:
    # ------------------------------------------------------------ 
    def _get_x0(self):
        return np.array(self.fractions + self.scales + self.bgshifts)
    
    def _parse_x(self, x, n, m): #returns: fractions | scales | bgshifts
        return x[:m][:,np.newaxis], x[m:m+n], x[-n:] if settings.BGSHIFT else np.zeros(shape=(n,))
   
    def _get_rp_statics(self):
        #1 get the different intensities for each phase for each specimen 
        #  -> each specimen gets a 2D np-array of size m,t with:
        #         m the number of phases        
        #         t the number of data points for that specimen
        n, m = self.phase_matrix.shape
        calculated = [None]*n
        experimental = [None]*n
        selectors = [None]*n
        todeg = 360.0 / pi
        for i in range(n):
            phases = self.phase_matrix[i]
            specimen = self.specimens[i]
            if specimen!=None:
                theta_range, calc = specimen.get_phase_intensities(phases, self.parent.goniometer.get_lorentz_polarisation_factor)
                calculated[i] = calc.copy()
                experimental[i] = specimen.experimental_pattern.xy_store.get_raw_model_data()[1].copy()
                selectors[i] = specimen.get_exclusion_selector(theta_range*todeg)
        return n, m, calculated, experimental, selectors
   
    def _calculate_total_rp(self, x, n, m, calculated, experimental, selectors):
        tot_rp = 0.0
        fractions, scales, bgshifts = self._parse_x(x, n, m)
        for i in range(n):
            if calculated[i]!=None:
                calc = (scales[i] * np.sum(calculated[i]*fractions, axis=0)) 
                if settings.BGSHIFT:
                    calc += bgshifts[i]
                exp = experimental[i][selectors[i]]
                cal = calc[selectors[i]]
                tot_rp += Statistics._calc_Rp(exp, cal)
        return tot_rp
    
    #@print_timing
    def optimize(self, silent=False, method=0):
        """
            Optimizes the current mixture fractions, scales and bg shifts.
        """
        #1. get stuff that doesn't change:
        n, m, calculated, experimental, selectors = self._get_rp_statics()

        #2. define the objective function:
        def calculate_total_R2(x, *args):
            return self._calculate_total_rp(x, n, m, calculated, experimental, selectors)
            
        #3. optimize the fractions:         
        x0 = self._get_x0()
        bounds = [(0,None) for el in x0]
        lastx, lastR2 = None, None
        if method == 0: #L BFGS B
            iprint = -1 # if not settings.DEBUG else 0
            lastx, lastR2, info = scipy.optimize.fmin_l_bfgs_b(calculate_total_R2, x0, approx_grad=True, factr=1000, bounds=bounds, iprint=iprint)
        elif method == 1: #SIMPLEX
            disp = 0
            lastx, lastR2, itr, funcalls, warnflag = scipy.optimize.fmin(calculate_total_R2, x0, disp=disp, full_output=True)
        elif method == 2: #L BFGS B: FAST WIDE + SLOW NARROW
            lastx, lastR2 = Mixture.mod_l_bfgs_b(calculate_total_R2, x0, bounds)
        elif method == 3: #truncated Newton algorithm
             disp = 0
             lastx, nfeval, rc = scipy.optimize.fmin_tnc(calculate_total_R2, x0, approx_grad=True, epsilon=0.05, bounds=bounds, disp=disp)
            
       
        #rescale scales and fractions so they fit into [0-1] range, and round them to have 6 digits max:
        fractions, scales, bgshifts = self._parse_x(lastx, n, m)
        fractions = fractions.flatten()
        scales = scales.round(6)
        if settings.BGSHIFT:
            bgshifts = bgshifts.round(6)
        
        sum_frac = np.sum(fractions)
        fractions = np.around((fractions / sum_frac), 6)
        scales *= sum_frac
        
        #set model properties:
        self.fractions = list(fractions)
        self.scales = list(scales)
        self.bgshifts = list(bgshifts) if settings.BGSHIFT else [0]*n
        
        if not silent: self.has_changed.emit()
        
        return lastR2
       
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
        from itertools import chain
        from collections import OrderedDict
        import csv
        
        # create an atom nr -> (atom name, conversion) mapping
        # this is used to transform most of the elements into their oxides
        atom_conv = OrderedDict()
        with open(settings.get_def_file("COMPOSITION_CONV"), 'r') as f:
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
                

       
    @staticmethod
    def mod_l_bfgs_b(func, x0, init_bounds, args=[], f1=1e12, f2=10):
        """
            Dual L BFGS B method. First a loose target is set with the bounds given by the user.
            Then a slower, but more constrained run is made with the previously found solution.
        """
        iprint = -1
        lastx, lastR2, info = scipy.optimize.fmin_l_bfgs_b(func, x0, approx_grad=True, factr=f1, bounds=init_bounds, args=args, iprint=iprint)
        lastx = np.array(lastx)        
        lowerx = lastx*0.95
        upperx = lastx*1.05
        bounds = np.zeros(shape=lowerx.shape + (2,))
        for i, (minx, maxx) in enumerate(init_bounds):
            maxx = maxx if maxx!=None else upperx[i]
            minx = minx if minx!=None else lowerx[i]
            bounds[i, 0] = max(lowerx[i], minx)
            bounds[i, 1] = min(upperx[i], maxx)
        lastx, lastR2, info = scipy.optimize.fmin_l_bfgs_b(func, lastx, approx_grad=True, factr=f2, args=args, bounds=bounds, iprint=iprint)
        return lastx, lastR2
       
    def update_refinement_treestore(self):
        """
            Called whenever the refinement view is opened, this creates a tree
            store with the refinable properties and their minimum, maximum and
            current value.
        """
        unique_phases = np.unique(self.phase_matrix.flatten())
        
        self.refinables.clear()
         
        def add_property(parent_itr, obj, prop):            
            rp = RefinableProperty(obj, prop, sensitivity=0, refine=False, parent=self)
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
    
    last_refine_rp = 0.0
        
    def auto_restrict(self):
        """
            Convenience function that restricts the selected properties 
            automatically by setting their minimum and maximum values.
        """
        for ref_prop in self.refinables.iter_objects():
            if ref_prop.refine and ref_prop.refinable:
                ref_prop.value_min = ref_prop.value * 0.95
                ref_prop.value_max = ref_prop.value * 1.05
        return
        
    refine_lock = False
    def refine(self, params): #, gui_callback):
        """
            This refines the selected properties using the selected algorithm.
            The method can be passes a callback to periodically update the gui.
            This should be run asynchronously...
        """
        if not self.refine_lock:
            self.refine_lock = True            
            ref_props = []
            values = []
            ranges = tuple()
        
            self.parent.freeze_updates()
                       
            for ref_prop in self.refinables.iter_objects():
                if ref_prop.refine and ref_prop.refinable:
                    ref_props.append(ref_prop)
                    values.append(ref_prop.value)
                    ranges = ranges + ((ref_prop.value_min, ref_prop.value_max),)
            x0 = np.array(values, dtype=float)
            initialR2 = self.current_rp
            
            lastx = np.array(values, dtype=float)
            lastR2 = initialR2            
                        
            if len(ref_props) > 0:      
                self.best_rp, self.best_x = None, None
                
                def apply_solution(new_values):
                    for i, ref_prop in enumerate(ref_props):
                        if not (new_values.shape==()):
                            ref_prop.value = new_values[i]
                        else:
                            ref_prop.value = new_values[()]
                    self.last_refine_rp = self.optimize(silent=True, method=0)
                
                def fitness_func(new_values):
                    if not (params["kill"] or params["stop"]):
                        apply_solution(new_values)
                        time.sleep(0.05)
                        if self.best_rp==None or self.best_rp > self.last_refine_rp:
                            self.best_rp = self.last_refine_rp
                            self.best_x = new_values
                        return self.last_refine_rp
                    elif params["kill"]:                
                        raise GeneratorExit
                    elif params["stop"]:
                        print self.best_x, self.best_rp
                        raise StopIteration
                        
                try:
                    if self.refine_method==0: #L BFGS B                                           
                        lastx, lastR2 = Mixture.mod_l_bfgs_b(fitness_func, x0, ranges, args=[], f2=1e6)
                    elif self.refine_method==1: #GENETIC ALGORITHM
                        lastx, lastR2 = run_genetic_algorithm(ref_props, x0, ranges, fitness_func)
                    elif self.refine_method==100: #BRUTE FORCE, only for scripting
                        lastx, lastR2, val_grid, rp_grid  = scipy.optimize.brute(fitness_func, ranges, Ns=10, full_output=1, finish=None)
                except StopIteration:
                    lastx, lastR2 = self.best_x, self.best_rp
                    print lastx, lastR2
                except GeneratorExit:
                    pass #no action needed
                except any as error:
                    print "Handling run-time error: %s" % error
                    print format_exc()
                finally:
                    del self.best_x
                    del self.best_rp
            self.refine_lock = False
            self.parent.thaw_updates()
            if self.refine_method != 100:
                return x0, initialR2, lastx, lastR2, apply_solution
            else:
                return x0, initialR2, lastx, lastR2, apply_solution, val_grid, rp_grid
                                    
    def apply_result(self):
        if self.auto_run: self.optimize()
        for i, specimen in enumerate(self.specimens):
            if specimen!=None:
                specimen.abs_scale = self.scales[i]
                specimen.bg_shift = self.bgshifts[i]
                specimen.update_pattern(self.phase_matrix[i,:], self.fractions, self.project.goniometer.get_lorentz_polarisation_factor)
                
    pass #end of class
    
#a wrapper class:
class RefinableProperty(ChildModel, ObjectListStoreChildMixin, Storable):
    
    #MODEL INTEL:
    __parent_alias__ = "mixture"
    __index_column__ = "index"
    __model_intel__ = [ #TODO add labels
        PropIntel(name="title",             inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  data_type=str,    refinable=False, storable=False, observable=True,  has_widget=True),
        PropIntel(name="refine",            inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  data_type=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="refinable",         inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  data_type=bool,   refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="prop",              inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  data_type=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inh_prop",          inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  data_type=str,    refinable=False, storable=False, observable=True,  has_widget=True),        
        PropIntel(name="value",             inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  data_type=float,  refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="value_min",         inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  data_type=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="value_max",         inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  data_type=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="obj",               inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  data_type=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="index",             inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  data_type=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="prop_intel",        inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  data_type=object, refinable=False, storable=False, observable=True,  has_widget=False),
    ]
    
    #PROPERTIES:
    obj = None
    
    _prop = ""
    _prop_intel = None
    def get_prop_intel_value(self):
        if isinstance(self.obj, _RefinementBase) and self.prop==None:
            return None
        else:           
            if not self._prop_intel:
                self._prop_intel = self.obj.get_prop_intel_by_name(self.prop)
            return self._prop_intel
        
    def get_prop_value(self):
        return self._prop
    def set_prop_value(self, value):
        self._prop = value
    
    def get_inh_prop_value(self):
        return self.prop_intel.inh_name if self.prop_intel else None
    
    last_lbl=None
    last_pb=None
    def get_title_value(self):
        if isinstance(self.obj, _RefinementBase) and self.prop_intel==None:
            return self.obj.refine_title
        else:
            return self.prop_intel.label

    def get_value_value(self):
        if isinstance(self.obj, RefinementValue):
            return self.obj.refine_value
        elif self.prop!=None:
            return getattr(self.obj, self.prop)
        else:
            return None
    def set_value_value(self, value):
        value = max(min(value, self.value_max), self.value_min)
        if isinstance(self.obj, RefinementValue):
            self.obj.refine_value = value
        else:
            setattr(self.obj, self.prop, value)
      
    @property
    def inherited(self):
        return self.inh_prop!=None and hasattr(self.obj, self.inh_prop) and getattr(self.obj, self.inh_prop)
        
    @property
    def refinable(self):
        if isinstance(self.obj, RefinementGroup) and self.prop_intel!=None:
            return self.obj.children_refinable and not self.inherited
        if isinstance(self.obj, _RefinementBase) and self.prop_intel==None:
            return self.obj.is_refinable
        else:
            return (not self.inherited)
    
    @property
    def ref_info(self):
        name = self.prop_intel.name if self.prop_intel else self.prop
        if hasattr(self.obj, "%s_ref_info" % name):
            return getattr(self.obj, "%s_ref_info" % name)
        elif isinstance(self.obj, _RefinementBase) and self.prop_intel==None:
            return self.obj.refine_info
    
    def get_value_min_value(self):        
        return self.ref_info.minimum if self.ref_info else None
    def set_value_min_value(self, value):
        if self.ref_info:
            self.ref_info.minimum = value
            self.liststore_item_changed()
    def get_value_max_value(self):
        return self.ref_info.maximum if self.ref_info else None
    def set_value_max_value(self, value):
        if self.ref_info:
            self.ref_info.maximum = value
            self.liststore_item_changed()

    def get_refine_value(self):
        return self.ref_info.refine if self.ref_info else False
    def set_refine_value(self, value):
        if self.ref_info:
            self.ref_info.refine = value and self.refinable
            self.liststore_item_changed()

    def get_index_value(self):
       return (self.obj, self.prop)

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, obj=None, prop=None, obj_uuid=None, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)

        if obj==None:
            if obj_uuid:
                obj = pyxrd_object_pool.get_object(obj_uuid)
            else:
                raise RuntimeError, "Object UUIDs are used for storage since version 0.4!"
                
        self.obj = obj
        self.prop = prop
        
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------   
    def json_properties(self):
        assert(self.parent!=None)
        retval = Storable.json_properties(self)
        retval["obj_uuid"] = self.obj.uuid
        return retval
        
    pass #end of class    
