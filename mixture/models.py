# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from warnings import warn
import time
from math import pi

import gtk
import gobject
from gtkmvc.model import Model, Signal
import numpy as np
import scipy

import settings

from generic.metaclasses import pyxrd_object_pool
from generic.io import Storable
from generic.utils import print_timing, delayed
from generic.model_mixins import ObjectListStoreChildMixin
from generic.models import ChildModel, Storable, PropIntel, MultiProperty
from generic.treemodels import ObjectTreeStore, _BaseObjectListStore

from phases.models import Phase, Component, UnitCellProperty, ComponentRatioFunction
from probabilities.base_models import _AbstractProbability
from specimen.models import Statistics

from mixture.genetics import run_genetic_algorithm
from mixture.refinement import _RefinementBase, RefinementValue, RefinementGroup

class Mixture(ChildModel, ObjectListStoreChildMixin, Storable):
    #MODEL INTEL:
    __parent_alias__ = "project"
    __model_intel__ = [ #TODO add labels
        PropIntel(name="data_name",             inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_refinables",      inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=False,  observable=True,  has_widget=True), #FIXME
        PropIntel(name="auto_run",              inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="data_refine_method",    inh_name=None,         label="", minimum=None,  maximum=None,  is_column=False, ctype=int,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="has_changed",           inh_name=None,         label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="needs_reset",           inh_name=None,         label="", minimum=None,  maximum=None,  is_column=False, ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
    ]

    #SIGNALS:
    has_changed = None
    needs_reset = None

    #INTERNALS:
    _data_name = ""
    def get_data_name_value(self):
        return self._data_name
    def set_data_name_value(self, value):
        self._data_name = value
        self.liststore_item_changed()
    
    auto_run = False
    
    data_phase_matrix = None
    
    data_specimens = None
    data_scales = None
    data_bgshifts = None
    
    data_phases = None
    data_fractions = None

    data_refinables = None

    data_refine_method = MultiProperty(0, int, None, 
        { 0: "L BFGS B algorithm", 1: "Genetic algorithm" })

    @property
    def current_rp(self):
        return self._calculate_total_rp(self._get_x0(), *self._get_rp_statics())

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name="New Mixture", auto_run=False, 
            phase_indeces=None, phase_uuids=None, 
            specimen_indeces=None, specimen_uuids=None, data_phases=None,
            data_scales=None, data_bgshifts=None, data_fractions=None, 
            data_refinables=None, data_refine_method=None, parent=None):
        ChildModel.__init__(self, parent=parent)
        self.has_changed = Signal()
        self.needs_reset = Signal()
        self.data_name = data_name or self.data_name
        self.auto_run = auto_run or self.auto_run
        
        #2D matrix, rows match specimens, columns match mixture 'phases'; contains the actual phase objects
        if phase_uuids:
            self.data_phase_matrix = np.array([[pyxrd_object_pool.get_object(uuid) if uuid else None for uuid in row] for row in phase_uuids], dtype=np.object_)
        elif phase_indeces and self.parent != None:
            warn("The use of object indeces is deprected since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
            self.data_phase_matrix = np.array([[self.parent.data_phases.get_user_data_from_index(index) if index!=-1 else None for index in row] for row in phase_indeces], dtype=np.object_)
        else:
            self.data_phase_matrix = np.empty(shape=(0,0), dtype=np.object_)
            
        #list with actual specimens, indexes match with rows in phase_matrix
        if phase_uuids:
            self.data_specimens = [pyxrd_object_pool.get_object(uuid) if uuid else None for uuid in specimen_uuids]            
        elif specimen_indeces != None and self.parent != None:
            warn("The use of object indeces is deprected since version 0.4. Please switch to using object UUIDs.", DeprecationWarning)
            self.data_specimens = [self.parent.data_specimens.get_user_data_from_index(index) if index!=-1 else None for index in specimen_indeces]
        else:
            self.data_specimens = list()
        
        self.data_scales = data_scales or list()         #list with scale values, indexes match with rows in phase_matrix
        self.data_bgshifts = data_bgshifts or [0.0]*len(self.data_scales)    #list with specimen background shift values, indexes match with rows in phase_matrix        
        self.data_phases = data_phases or list()        #list with mixture phase names, indexes match with cols in phase_matrix
        self.data_fractions = data_fractions or [0.0]*len(self.data_phases)  #list with phase fractions, indexes match with cols in phase_matrix
        
        self.data_refinables = data_refinables or ObjectTreeStore(RefinableProperty) 
        self.data_refine_method = data_refine_method or self.data_refine_method
        
        #sanity check:
        n, m = self.data_phase_matrix.shape
        if len(self.data_scales) != n or len(self.data_specimens) != n or len(self.data_bgshifts) != n:
            raise IndexError, "Shape mismatch: scales, background shifts or specimens lists do not match with row count of phase matrix"
        if len(self.data_phases) != m or len(self.data_fractions) != m:
            raise IndexError, "Shape mismatch: fractions or phases lists do not match with column count of phase matrix"
    
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------   
    def json_properties(self):
        self.update_refinement_treestore()
        retval = Storable.json_properties(self)

        retval["phase_uuids"] = [[item.uuid if item else "" for item in row] for row in map(list, self.data_phase_matrix)]            
        retval["specimen_uuids"] = [specimen.uuid if specimen else "" for specimen in self.data_specimens]
        retval["data_phases"] = self.data_phases
        retval["data_fractions"] = self.data_fractions
        retval["data_bgshifts"] = self.data_bgshifts
        retval["data_scales"] = self.data_scales
        
        return retval
    
    @staticmethod          
    def from_json(**kwargs):
        sargs = dict()
        for key in ("data_refinables",):
            if key in kwargs:
                sargs[key] = kwargs[key]
                del kwargs[key]
            else:
                sargs[key] = None
             
        mixture = Mixture(**kwargs)
        #data_refinables = IndexListStore.from_json(parent=mixture, **sargs["data_refinables"]['properties'])
        #for refinable in data_refinables._model_data:
        #    print refinable.obj, refinable.prop
        #    mixture.data_refinables.append(refinable)
        #del data_refinables #FIXME
        
        return mixture
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    def uncheck_phase(self, phase):
        shape = self.data_phase_matrix.shape
        for i in range(shape[0]):
            for j in range(shape[1]):
                if self.data_phase_matrix[i,j] == phase:
                    self.data_phase_matrix[i,j] = None
        self.update_refinement_treestore()
        self.needs_reset.emit()
    
    def add_phase(self, phase_name, fraction):
        n, m = self.data_phase_matrix.shape
        if n > 0:
            self.data_phases.append(phase_name)
            self.data_fractions.append(fraction)
            self.data_phase_matrix = np.concatenate([self.data_phase_matrix.copy(), [[None,] for n in range(n)]], axis=1)        
            self.update_refinement_treestore()
            self.has_changed.emit()
            return m
        else:
            return -1

    def _del_phase_by_index(self, index):
        del self.data_phases[index]
        del self.data_fractions[index]
        self.data_phase_matrix = np.delete(self.data_phase_matrix, index, axis=1)
        self.update_refinement_treestore()
        self.needs_reset.emit()

    def del_phase(self, phase_name):
        self._del_phase_by_index(self.data_phases.index(phase_name))
    
    def add_specimen(self, specimen, scale, bgs):
        index = len(self.data_specimens)
        self.data_specimens.append(specimen)
        self.data_scales.append(scale)
        self.data_bgshifts.append(bgs)
        n, m = self.data_phase_matrix.shape
        self.data_phase_matrix = np.concatenate([self.data_phase_matrix.copy(), [[None]*m] ], axis=0)
        self.data_phase_matrix[n,:] = None
        self.has_changed.emit()
        return n

    def _del_specimen_by_index(self, index):
        del self.data_specimens[index]
        del self.data_scales[index]
        del self.data_bgshifts[index]
        self.data_phase_matrix = np.delete(self.data_phase_matrix, index, axis=0)
        self.needs_reset.emit()

    def del_specimen(self, specimen):
        self._del_specimen_by_index(self.data_specimens.index(specimen))
    
    # ------------------------------------------------------------
    #      Refinement stuff:
    # ------------------------------------------------------------ 
    def _get_x0(self):
        return np.array(self.data_fractions + self.data_scales + self.data_bgshifts)
    
    def _parse_x(self, x, n, m): #returns: fractions | scales | bgshifts
        return x[:m][:,np.newaxis], x[m:m+n], x[-n:]
   
    def _get_rp_statics(self):
        #1 get the different intensities for each phase for each specimen 
        #  -> each specimen gets a 2D np-array of size m,t with:
        #         m the number of phases        
        #         t the number of data points for that specimen
        n, m = self.data_phase_matrix.shape
        calculated = [None]*n
        experimental = [None]*n
        selectors = [None]*n
        todeg = 360.0 / pi
        for i in range(n):
            phases = self.data_phase_matrix[i]
            specimen = self.data_specimens[i]
            theta_range, calc = specimen.get_phase_intensities(phases, self.parent.data_goniometer.get_lorentz_polarisation_factor)
            calculated[i] = calc.copy()
            experimental[i] = specimen.data_experimental_pattern.xy_store.get_raw_model_data()[1].copy()
            selectors[i] = specimen.get_exclusion_selector(theta_range*todeg)
        return n, m, calculated, experimental, selectors
   
    def _calculate_total_rp(self, x, n, m, calculated, experimental, selectors):
        tot_rp = 0.0
        fractions, scales, bgshifts = self._parse_x(x, n, m)
        for i in range(n):
            calc = (scales[i] * np.sum(calculated[i]*fractions, axis=0)) + bgshifts[i]
            exp = experimental[i][selectors[i]]
            cal = calc[selectors[i]]
            tot_rp += Statistics._calc_Rp(exp, cal)
        return tot_rp
    
    #@print_timing
    def optimize(self, silent=False, method=3):
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
        fractions = fractions.flatten().round(6).tolist()
        scales = scales.round(6)
        bgshifts = bgshifts.round(6)
        
        sum_frac = np.sum(fractions)
        fractions /= sum_frac
        scales *= sum_frac
        
        #set model properties:
        self.data_fractions = list(fractions)
        self.data_scales = list(scales)
        self.data_bgshifts = list(bgshifts)
        
        if not silent: self.has_changed.emit()
        
        return lastR2
       
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
        unique_phases = np.unique(self.data_phase_matrix.flatten())
        
        self.data_refinables.clear()
         
        def add_property(parent_itr, obj, prop):            
            rp = RefinableProperty(obj, prop, sensitivity=0, refine=False, parent=self)
            return self.data_refinables.append(parent_itr, rp)
            
        def parse_attribute(obj, attr, root_itr):
            """
                obj: the object
                attr: the attribute of obj or None if obj is the attribute
                root_itr: the iter new iters should be put under
            """
            value = getattr(obj, attr) if attr!=None else obj
            
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
            
        for phase in unique_phases:
            if phase: parse_attribute(phase, None, None)
    
    last_refine_rp = 0.0
        
    def auto_restrict(self):
        """
            Convenience function that restricts the selected properties 
            automatically by setting their minimum and maximum values.
        """
        for ref_prop in self.data_refinables.iter_objects():
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
                       
            for ref_prop in self.data_refinables.iter_objects():
                if ref_prop.refine and ref_prop.refinable:
                    ref_props.append(ref_prop)
                    values.append(ref_prop.value)
                    ranges = ranges + ((ref_prop.value_min, ref_prop.value_max),)
            x0 = np.array(values, dtype=float)
            initialR2 = self.current_rp
            
            lastx = np.array(values, dtype=float)
            lastR2 = initialR2            
                        
            if len(ref_props) > 0:      
                def apply_solution(new_values):
                    for i, ref_prop in enumerate(ref_props):
                        if not (new_values.shape==()):
                            ref_prop.value = new_values[i]
                        else:
                            ref_prop.value = new_values[()]
                    self.last_refine_rp = self.optimize(silent=True, method=0)
                
                def fitness_func(new_values):
                    if not params["kill"]:
                        apply_solution(new_values)
                        time.sleep(0.05)
                        return self.last_refine_rp
                    else:
                        raise GeneratorExit
                try:
                    if self.data_refine_method==0: #L BFGS B                                           
                        lastx, lastR2 = Mixture.mod_l_bfgs_b(fitness_func, x0, ranges, args=[], f2=1e6)
                    elif self.data_refine_method==1: #GENETIC ALGORITHM
                        lastx, lastR2 = run_genetic_algorithm(ref_props, x0, ranges, fitness_func)
                except GeneratorExit:
                    apply_solution(x0) #place back original result
                    pass #exit
            
            self.refine_lock = False
            self.parent.thaw_updates()
            return x0, initialR2, lastx, lastR2, apply_solution
                    
    def apply_result(self):
        if self.auto_run: self.optimize()
        for i, specimen in enumerate(self.data_specimens):
            specimen.data_abs_scale = self.data_scales[i]
            specimen.data_bg_shift = self.data_bgshifts[i]
            specimen.update_pattern(self.data_phase_matrix[i,:], self.data_fractions, self.project.data_goniometer.get_lorentz_polarisation_factor)
                
    pass #end of class
    
class RefinableProperty(ChildModel, ObjectListStoreChildMixin, Storable):
    
    #MODEL INTEL:
    __parent_alias__ = "mixture"
    __index_column__ = "index"
    __model_intel__ = [ #TODO add labels
        PropIntel(name="title",             inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=False, observable=True,  has_widget=True),
        PropIntel(name="refine",            inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="refinable",         inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=bool,   refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="prop",              inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="inh_prop",          inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=str,    refinable=False, storable=False, observable=True,  has_widget=True),        
        PropIntel(name="value",             inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="value_min",         inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="value_max",         inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=float,  refinable=False, storable=True,  observable=True,  has_widget=True),
        PropIntel(name="obj",               inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="index",             inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
        PropIntel(name="prop_intel",        inh_name=None,         label="", minimum=None,  maximum=None,  is_column=True,  ctype=object, refinable=False, storable=False, observable=True,  has_widget=False),
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
        else:
            return getattr(self.obj, self.prop)
    def set_value_value(self, value):
        value = max(min(value, self.value_max), self.value_min)
        if isinstance(self.obj, RefinementValue):
            self.obj.refine_value = value
        else:
            setattr(self.obj, self.prop, value)
    
    _refine = False
    def get_refine_value(self): return self._refine
    def set_refine_value(self, value):
        self._refine = value and self.refinable
        self.liststore_item_changed()
      
    @property
    def inherited(self):
        return self.inh_prop!=None and hasattr(self.obj, self.inh_prop) and getattr(self.obj, self.inh_prop)
        
    @property
    def refinable(self):
        if isinstance(self.obj, _RefinementBase) and self.prop_intel==None:
            return self.obj.is_refinable
        else:
            return (not self.inherited)
    
    _value_min = 0.0
    def get_value_min_value(self): return self._value_min
    def set_value_min_value(self, value):
        self._value_min = value
        self.liststore_item_changed()
    _value_max = 0.0
    def get_value_max_value(self): return self._value_max    
    def set_value_max_value(self, value):
        self._value_max = value
        self.liststore_item_changed()

    def get_index_value(self):
       return (self.obj, self.prop)

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, obj=None, prop=None, refine=None, obj_index=None, obj_uuid=None, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)

        if obj==None:
            if obj_uuid:
                obj = pyxrd_object_pool.get_object(obj_uuid)
            else:
                raise RuntimeError, "Object UUIDs are used for storage since version 0.4!"
                
        self.obj = obj
        self.prop = prop
        
        self.value_min = kwargs.get("value_min", self.prop_intel.minimum if self.prop_intel else None) or self.value_min
        self.value_max = kwargs.get("value_max", self.prop_intel.maximum if self.prop_intel else None) or self.value_max
        
        self._refine = refine or self._refine
        
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------   
    def json_properties(self):
        assert(self.parent!=None)
        retval = Storable.json_properties(self)
        retval["obj_uuid"] = self.obj.uuid
        return retval
        
    pass #end of class    
