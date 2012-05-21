# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk
import gobject
import time

from math import pi

#from pygtkhelpers.ui.objectlist import ObjectTree, Column

from gtkmvc.model import Model, Signal
import numpy as np
import scipy
#from scipy.optimize import minimize

import settings

from phases.models import Phase, Component
from probabilities.models import _AbstractProbability
from specimen.models import Statistics
from generic.io import Storable
from generic.utils import print_timing, delayed
from generic.models import ChildModel, ObjectListStoreChildMixin, Storable, add_cbb_props
from generic.treemodels import IndexListStore

from mixture.genetics import run_genetic_algorithm

class Mixture(ChildModel, ObjectListStoreChildMixin, Storable):
    #MODEL INTEL:
    __observables__ = ["has_changed", "needs_reset", "data_name", "data_refineables", "auto_run", "data_refine_method"]
    __have_no_widget__ = ChildModel.__have_no_widget__ + ["has_changed", "needs_reset"]
    __storables__ = [prop for prop in __observables__ if not prop in ["parent", "has_changed", "needs_reset"] ]
    __columns__ = [
        ('data_name', str),
        ('data_refineables', object),
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

    data_refineables = None

    _data_refine_method = 0
    _data_refine_methods = { 0: "L BFGS B algorithm", 1: "Genetic algorithm" }
    add_cbb_props(("data_refine_method", int, None))

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name="New Mixture", auto_run=False, phase_indeces=None, specimen_indeces=None, data_phases=None, data_scales=None, data_bgshifts=None, data_fractions=None, data_refineables=None, data_refine_method=None, parent=None):
        ChildModel.__init__(self, parent=parent)
        self.has_changed = Signal()
        self.needs_reset = Signal()
        self.data_name = data_name or self.data_name
        self.auto_run = auto_run or self.auto_run
        
        #2D matrix, rows match specimens, columns match mixture 'phases'; contains the actual phase objects
        if phase_indeces and self.parent != None:
            self.data_phase_matrix = np.array([[self.parent.data_phases.get_user_data_from_index(index) if index!=-1 else None for index in row] for row in phase_indeces], dtype=np.object_)
        else:
            self.data_phase_matrix = np.empty(shape=(0,0), dtype=np.object_)
            
        #list with actual specimens, indexes match with rows in phase_matrix
        if specimen_indeces != None and self.parent != None:
            self.data_specimens = [self.parent.data_specimens.get_user_data_from_index(index) if index!=-1 else None for index in specimen_indeces]
        else:
            self.data_specimens = list()
        
        self.data_scales = data_scales or list()         #list with scale values, indexes match with rows in phase_matrix
        self.data_bgshifts = data_bgshifts or [0.0]*len(self.data_scales)    #list with specimen background shift values, indexes match with rows in phase_matrix        
        self.data_phases = data_phases or list()        #list with mixture phase names, indexes match with cols in phase_matrix
        self.data_fractions = data_fractions or [0.0]*len(self.data_phases)  #list with phase fractions, indexes match with cols in phase_matrix
        
        self.data_refineables = data_refineables or IndexListStore(RefineableProperty) 
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
        
        if self.parent==None:
            raise ValueError, "Cannot get JSON properties of a mixture with no parent!"

        retval["phase_indeces"] = [[self.parent.data_phases.index(item) if item else -1 for item in row] for row in map(list, self.data_phase_matrix)]
        retval["specimen_indeces"] = [self.parent.data_specimens.index(specimen) if specimen else -1 for specimen in self.data_specimens]
        retval["data_phases"] = self.data_phases
        retval["data_fractions"] = self.data_fractions
        retval["data_bgshifts"] = self.data_bgshifts
        retval["data_scales"] = self.data_scales
        
        return retval
    
    @staticmethod          
    def from_json(**kwargs):
        sargs = dict()
        for key in ("data_refineables",):
            if key in kwargs:
                sargs[key] = kwargs[key]
                del kwargs[key]
            else:
                sargs[key] = None
             
        mixture = Mixture(**kwargs)
        data_refineables = IndexListStore.from_json(parent=mixture, **sargs["data_refineables"]['properties'])
        for refineable in data_refineables._model_data:
            mixture.data_refineables.append(refineable)
        del data_refineables
                
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
        self.data_phases.append(phase_name)
        self.data_fractions.append(fraction)
        n, m = self.data_phase_matrix.shape
        self.data_phase_matrix = np.concatenate([self.data_phase_matrix.copy(), [[None,] for n in range(n)]], axis=1)        
        self.update_refinement_treestore()
        self.has_changed.emit()
        return m

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
    
    def _get_x0(self):
        return np.array(self.data_fractions + self.data_scales + self.data_bgshifts)
    
    def _parse_x(self, x, n, m): #returns: fractions | scales | bgshifts
        return x[:m][:,np.newaxis], x[m:m+n], x[-n:]
    
    #@print_timing
    def optimize(self, silent=False):
        
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
            experimental[i] = specimen.data_experimental_pattern.xy_data._model_data_y.copy()
            selectors[i] = specimen.get_exclusion_selector(theta_range*todeg)
                
                
        #2 optimize the fractions
        def calculate_total_R2(x, *args):
            tot_Rp = 0.0
            fractions, scales, bgshifts = self._parse_x(x, n, m)
            for i in range(n):
                calc = (scales[i] * np.sum(calculated[i]*fractions, axis=0)) + bgshifts[i]
                exp = experimental[i][selectors[i]]
                cal = calc[selectors[i]]
                tot_Rp += Statistics._calc_Rp(exp, cal)
            return tot_Rp
        
        x0 = self._get_x0()
        bounds = [(0,None) for el in x0]
        method = 2
        lastx, lastR2 = None, None
        if method == 0: #L BFGS B
            iprint = -1 # if not settings.DEBUG else 0
            lastx, lastR2, info = scipy.optimize.fmin_l_bfgs_b(calculate_total_R2, x0, approx_grad=True, bounds=bounds, iprint=iprint)
        elif method == 1: #SIMPLEX
            disp = 0
            lastx = scipy.optimize.fmin(calculate_total_R2, x0, disp=disp)
        elif method == 2: #L BFGS B: FAST WIDE + SLOW NARROW
            lastx, lastR2 = Mixture.mod_l_bfgs_b(calculate_total_R2, x0, bounds)
       
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
       
    def update_refinement_treestore(self): #TODO add different CSDS distributions!
        unique_phases = np.unique(self.data_phase_matrix.flatten())
        
        new_store = IndexListStore(RefineableProperty) 
        def add_property(parent_itr, obj, prop, inh_prop=""): #TODO parents!!
            if inh_prop=="":
                inh_prop = prop.replace("data_", "inherit_", 1)
            else:
                inh_prop==""
                
            index = (obj, prop)
            rp = None        
            if self.data_refineables.index_in_model(index):
                rp = self.data_refineables.get_item_by_index(index)
            else:
                rp = RefineableProperty(obj, prop, inh_prop, sensitivity=0, refine=False, parent=self)
            if not new_store.index_in_model(index):
                return new_store.append(rp)
            
        for phase in unique_phases:
            if phase:
                #phase_itr = new_store.append(None, row=(phase, "", "", 0, False))
                phase_itr = add_property(None, phase, "", None)
                for prop in phase.__refineables__: add_property(phase_itr, phase, prop)
                for comp in phase.data_components._model_data:
                    comp_itr = add_property(None, comp, "", None)
                    for prop in comp.__refineables__:  add_property(comp_itr, comp, prop)
                if phase.data_G > 1:
                    prob = phase.data_probabilities
                    prob_itr = add_property(None, prob, "", None)
                    for prop in prob.__refineables__:  add_property(prob_itr, prob, prop, None)
        self.data_refineables = new_store
    
    def update_sensitivities(self):
        if self.data_refineables!=None:
            t1 = time.time()
            for ref_prop in self.data_refineables._model_data:
                item = ref_prop.obj
                prop = ref_prop.prop
                inh_prop = ref_prop.inh_prop
                if ref_prop.refineable:
                    original_value = ref_prop.value
                    #try:
                    ref_prop.value = original_value*0.95
                    R1 = self.optimize(silent=True)
                    ref_prop.value = original_value*1.05
                    R2 = self.optimize(silent=True)
                    ref_prop.sensitivity = (R2-R1) / (0.1*original_value)
                    #except:
                    #    pass
                    #finally:
                    ref_prop.value = original_value
                    self.optimize(silent=True)
                t2 = time.time()
                if (t2-t1) > 0.5:
                    t1 = time.time()
                    while gtk.events_pending():
                        gtk.main_iteration(False)
    
    refine_lock = False
    def refine(self, gui_callback):
        if not self.refine_lock:
            self.refine_lock = True            
            ref_props = []
            values = []
            ranges = tuple()
        
            self.parent.freeze_updates()
            
            for ref_prop in self.data_refineables._model_data:
                if ref_prop.refine and ref_prop.refineable:
                    ref_props.append(ref_prop)
                    values.append(ref_prop.value)
                    ranges = ranges + ((ref_prop.value_min, ref_prop.value_max),)
                   
            original_vals = values
            x0 = np.array(values, dtype=float)
            
            def fitness_func(new_values):
                for i, ref_prop in enumerate(ref_props):
                    if not (new_values.shape==()):
                        ref_prop.value = new_values[i]
                    else:
                        ref_prop.value = new_values[()]
                return self.optimize(silent=True)
            
            if self.data_refine_method==0: #L BFGS B
            
                global count
                count = 0        
                def gui_refine_func(new_values, gui_callback):
                    R = fitness_func(new_values)
                    global count
                    count = count + 1
                    if count>=5:
                        count = 0
                        if gui_callback!=None: gui_callback(R)
                        while gtk.events_pending():
                            gtk.main_iteration(False)
                    return R
                    
                lastx, lastR2 = Mixture.mod_l_bfgs_b(gui_refine_func, x0, ranges, args=[gui_callback,], f2=1e6)
                fitness_func(lastx) #apply last one                
        
            elif self.data_refine_method==1: #GENETIC ALGORITHM
                lastx = run_genetic_algorithm(ref_props, x0, ranges, fitness_func, gui_callback)
                fitness_func(lastx) #apply last one
                    
            self.refine_lock = False
            self.parent.thaw_updates()
            
        
                    
    def apply_result(self):
        for i, specimen in enumerate(self.data_specimens):
            specimen.data_phases.clear()
            specimen.data_abs_scale = self.data_scales[i]
            specimen.data_bg_shift = self.data_bgshifts[i]
            for j, phase in enumerate(self.data_phases):
                phase_obj = self.data_phase_matrix[i,j]
                if phase_obj: specimen.data_phases[phase_obj] = self.data_fractions[j]
                
    pass #end of class
    
class RefineableProperty(ChildModel, ObjectListStoreChildMixin, Storable):
    
    #MODEL INTEL:
    __observables__ = ["obj", "title", "prop", "inh_prop", "sensitivity", "refine", "value", "value_min", "value_max", "index"]
    __storables__ = [prop for prop in __observables__ if not prop in ["parent", "obj", "index", "value", "title"] ]
    __columns__ = [
        ('obj', object),
        ('prop', str),
        ('inh_prop', str),
        ('sensitivity', float),
        ('refine', bool),
        ('value', float),
        ('value_min', float),
        ('value_max', float),
        ('index', str),
    ]
    __index_column__ = "index"
    
    #PROPERTIES:
    obj = None
    
    def get_title_value(self):
        fmt = "%s"
        if not isinstance(self.obj, Phase):
            fmt = "  %s"
        if self.prop:
            prop = self.prop
            if isinstance(self.obj, _AbstractProbability):
                prop = dict(self.obj.__independent_label_map__)[self.prop]
            return fmt % ("  %s" % prop)
        elif hasattr(self.obj, "data_name"):
            return fmt % self.obj.data_name
        else:
            return fmt % "" 
    prop = ""
    inh_prop = None
    def get_value_value(self):
        return getattr(self.obj, self.prop)
    def set_value_value(self, value):
        #value = max(min(value, self.value_max), self.value_min) TODO
        setattr(self.obj, self.prop, value)
    
    _sensitivity = 0
    def get_sensitivity_value(self): return self._sensitivity
    def set_sensitivity_value(self, value):
        self._sensitivity = value
        self.liststore_item_changed()
    _refine = False
    def get_refine_value(self): return self._refine
    def set_refine_value(self, value):
        self._refine = value and self.refineable
        self.liststore_item_changed()
        
    @property
    def refineable(self):
        if isinstance(self.obj, Phase) or isinstance(self.obj, Component):
            if self.inh_prop=="" or self.inh_prop==None:
                return False
            else:
                return not (hasattr(self.obj, self.inh_prop) and getattr(self.obj, self.inh_prop))
        elif isinstance(self.obj, _AbstractProbability):
            if self.prop=="" or self.prop==None:
                return False
            else:
                return not getattr(self.obj.parent, "inherit_probabilities")
        else:
            return False
    
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
    def __init__(self, obj=None, prop=None, inh_prop=None, sensitivity=None, refine=None, value_min=None, value_max=None, obj_index=None, parent=None, **kwargs):
        ChildModel.__init__(self, parent=parent, **kwargs)
        Storable.__init__(self)

        if obj==None and obj_index!=None:
            tp, index = obj_index.split("-", 1)
            project = self.parent.parent
            if tp=="phase": 
                obj = project.data_phases.get_user_data_from_index(int(index))
            elif tp=="comp":
                index1, index2 = map(int, index.split("-"))
                phase = project.data_phases.get_user_data_from_index(index1)
                obj = phase.data_components.get_user_data_from_index(index2)
            elif tp=="prob":
                obj = project.data_phases.get_user_data_from_index(int(index)).data_probabilities
        self.obj = obj
        self.prop = prop
        self.inh_prop = inh_prop or self.inh_prop
        
        if value_min==None and value_max==None and hasattr(obj, "%s_range" % prop):
            value_min, value_max = getattr(obj, "%s_range" % prop)
        
        self.value_min = value_min or self.value_min
        self.value_max = value_max or self.value_max
        
        self.sensitivity = sensitivity or self.sensitivity
        self._refine = refine or self._refine
        
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------   
    def json_properties(self):
        retval = Storable.json_properties(self)
        
        if self.parent==None:
            raise ValueError, "Cannot get JSON properties of a RefineableProperty with no parent!"
       
        project = self.parent.parent
       
        def get_index(obj):
            if isinstance(obj, Phase):
                return "phase-%d" % project.data_phases.index(obj)
            elif isinstance(obj, Component):
                return "comp-%d-%d" % (project.data_phases.index(obj.parent), obj.parent.data_components.index(obj))
            else:
                return "prob-%d" % project.data_phases.index(obj.parent)
            
        retval["obj_index"] = get_index(self.obj)
        
        return retval
        
    pass #end of class    
