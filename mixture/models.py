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

from gtkmvc.model import Model, Signal
import numpy as np
import scipy
#from scipy.optimize import minimize

import settings

from specimen.models import Statistics
from generic.io import Storable
from generic.utils import print_timing, delayed
from generic.models import ChildModel, ObjectListStoreChildMixin, Storable

class Mixture(ChildModel, ObjectListStoreChildMixin, Storable):
    #MODEL INTEL:
    __observables__ = ["has_changed", "data_name", "data_refineables", "auto_run"]
    __have_no_widget__ = ChildModel.__have_no_widget__ + ["has_changed"]
    __storables__ = [prop for prop in __observables__ if not prop in ["parent", "has_changed", "data_refineables"] ]
    __columns__ = [
        ('data_name', str),
        ('data_refineables', object),
    ]

    #SIGNALS:
    has_changed = None

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
    
    data_phases = None
    data_fractions = None

    data_refineables = None

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name="New Mixture", auto_run=False, phase_indeces=None, specimen_indeces=None, data_phases=None, data_scales=None, data_fractions=None, parent=None):
        ChildModel.__init__(self, parent=parent)
        self.has_changed = Signal()
        self.data_name = data_name or self.data_name
        self.auto_run = auto_run or self.auto_run
        
        #2D matrix, rows match specimens, columns match mixture 'phases'; contains the actual phase objects
        if phase_indeces and self.parent != None:
            self.data_phase_matrix = np.array([[self.parent.data_phases.get_user_data_from_index(index) if index!=-1 else None for index in row] for row in phase_indeces])
        else:
            self.data_phase_matrix = np.empty(shape=(0,0), dtype=np.object_)
            
        #list with actual specimens, indexes match with rows in phase_matrix
        if specimen_indeces != None and self.parent != None:
            self.data_specimens = [self.parent.data_specimens.get_user_data_from_index(index) if index!=-1 else None for index in specimen_indeces]
        else:
            self.data_specimens = list()
        
        self.data_scales = data_scales or list()         #list with scale values, indexes match with rows in phase_matrix 
        self.data_phases = data_phases or list()        #list with mixture phase names, indexes match with cols in phase_matrix
        self.data_fractions = data_fractions or list()  #list with phase fractions, indexes match with cols in phase_matrix
        
        #sanity check:
        n, m = self.data_phase_matrix.shape
        if len(self.data_scales) != n or len(self.data_specimens) != n:
            raise IndexError, "Shape mismatch: scales or specimens lists do not match with row count of phase matrix"
        if len(self.data_phases) != m or len(self.data_fractions) != m:
            raise IndexError, "Shape mismatch: fractions or phases lists do not match with column count of phase matrix"
    
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------   
    def json_properties(self):
        retval = Storable.json_properties(self)
        
        if self.parent==None:
            raise ValueError, "Cannot get JSON properties of a mixture with no parent!"

        retval["phase_indeces"] = [[self.parent.data_phases.index(item) if item else -1 for item in row] for row in map(list, self.data_phase_matrix)]
        retval["specimen_indeces"] = [self.parent.data_specimens.index(specimen) if specimen else -1 for specimen in self.data_specimens]
        retval["data_phases"] = self.data_phases
        retval["data_scales"] = self.data_scales
        retval["data_fractions"] = self.data_fractions
        
        return retval
    
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    def add_phase(self, phase_name, fraction):
        self.data_phases.append(phase_name)
        self.data_fractions.append(fraction)
        n, m = self.data_phase_matrix.shape
        self.data_phase_matrix.resize((n,m+1))
        self.data_phase_matrix[:,m] = None
        self.has_changed.emit()
        return m

    def del_phase(self, phase_name):
        index = self.data_phases.index(phase_name)
        del self.data_phases[index]
        del self.data_fractions[index]
        self.data_phase_matrix = np.delete(self.data_phase_matrix, index, axis=1)
        self.has_changed.emit()        
    
    def add_specimen(self, specimen, scale):
        index = len(self.data_specimens)
        self.data_specimens.append(specimen)
        self.data_scales.append(scale)
        n, m = self.data_phase_matrix.shape
        self.data_phase_matrix.resize((n+1,m))
        self.data_phase_matrix[n,:] = None
        self.has_changed.emit()
        return n

    def del_specimen(self, specimen):
        index = self.data_specimens.index(phase_name)
        del self.data_specimens[index]
        del self.data_scales[index]
        self.data_phase_matrix = np.delete(self.data_phase_matrix, index, axis=0)
        self.has_changed.emit()
    
    #@print_timing
    def optimize(self, silent=False):
        
        #1 get the different intensities for each phase for each specimen 
        #  -> each specimen gets a 2D np-array of size m,t with:
        #         m the number of phases        
        #         t the number of data points for that specimen
        n, m = self.data_phase_matrix.shape
                
        #t1 = time.time()
        calculated = [None]*n
        experimental = [None]*n
        selectors = [None]*n
        todeg = 180.0 / pi
        for i in range(n):
            phases = self.data_phase_matrix[i]
            specimen = self.data_specimens[i]
            theta_range, calc = specimen.get_phase_intensities(phases, self.parent.data_goniometer.get_lorentz_polarisation_factor)
            calculated[i] = calc.copy()
            experimental[i] = specimen.data_experimental_pattern.xy_data._model_data_y.copy()
            selectors[i] = specimen.get_exclusion_selector(theta_range*todeg)
        #t2 = time.time()
        #print '%s took %0.3f ms' % ("Getting phase intensities", (t2-t1)*1000.0)
                
                
        #2 optimize the fractions
        def calculate_total_R2(fractions_and_scales):
            tot_Rp = 0.0
            tot_R2 = 0.0
            
            fractions = fractions_and_scales.copy()[:m] #first m numbers are the fractions
            scales = fractions_and_scales.copy()[-n:] #last n numbers are the scales
            fractions = fractions[:,np.newaxis]
                       
            for i in range(n):
                calc = scales[i] * np.sum(calculated[i]*fractions, axis=0)
                exp = experimental[i][selectors[i]]
                cal = calc[selectors[i]]
                #print cal.shape
                Rp = Statistics._calc_Rp(exp, cal)
                tot_Rp += Rp
            return tot_Rp
        
        x0 = np.array(self.data_fractions + self.data_scales)
        bounds = [(0,None) for el in x0]
        method = 0
        lastx, lastR2 = None, None
        if method == 0: #L BFGS B
            iprint = -1 # if not settings.DEBUG else 0
            lastx, lastR2, info = scipy.optimize.fmin_l_bfgs_b(calculate_total_R2, x0, approx_grad=True, bounds=bounds, iprint=iprint)
        elif method == 1: #SIMPLEX
            disp = 0
            lastx = scipy.optimize.fmin(calculate_total_R2, x0, disp=disp)
        
        #print info
       
        #rescale them so they fit into [0-1] range:
        fractions = np.array(lastx[:m])
        scales = np.array(lastx[-n:])
        sum_frac = np.sum(fractions)
        fractions /= sum_frac
        scales *= sum_frac
        
        #set model properties:
        self.data_fractions = list(fractions)
        self.data_scales = list(scales)
        
        if not silent: self.has_changed.emit()
        
        return lastR2
        
    pass #end of class
    
    
    def update_refinement_treestore(self): #TODO add probabilities as well as CSDS distributions!
        unique_phases = np.unique(self.data_phase_matrix.flatten())
        self.data_refineables = gtk.TreeStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING, gobject.TYPE_FLOAT, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN)
        
        def add_property(model, parent_itr, obj, prop, inh_prop="", selectable=True):
            if inh_prop=="":
                inh_prop = prop.replace("data_", "inherit_", 1)
            if inh_prop:
                selectable = selectable and not (hasattr(obj, inh_prop) and getattr(obj, inh_prop))
            model.append(parent_itr, row=(obj, prop, 0, selectable, False))
        
        for phase in unique_phases:
            if phase:
                phase_itr = self.data_refineables.append(None, row=(phase, "", 0, False, False))
                for prop in phase.__refineables__: add_property(self.data_refineables, phase_itr, phase, prop)
                for comp in phase.data_components._model_data:
                    comp_itr = self.data_refineables.append(phase_itr, row=(comp, "", 0, False, False))
                    for prop in comp.__refineables__:  add_property(self.data_refineables, comp_itr, comp, prop)
                if phase.data_G > 1:
                    prob = phase.data_probabilities
                    prob_itr = self.data_refineables.append(phase_itr, row=(prob, "", 0, False, False))
                    selectable = not getattr(phase, "inherit_probabilities")
                    for prop in prob.__refineables__:  add_property(self.data_refineables, prob_itr, prob, prop, None, selectable=selectable)
                        
    
    def update_sensitivities(self):
        if self.data_refineables!=None:
            global t1
            t1 = time.time()
            def for_each_item(model, path, itr, user_data=None):
                global t1
                item, prop, enabled, refine = model.get(itr, 0, 1, 3, 4)
                if enabled:
                    original_value = getattr(item, prop)
                    try:
                        val1 = original_value*0.95
                        setattr(item, prop, val1)
                        R1 = self.optimize(silent=True)
                        val2 = original_value*1.05
                        setattr(item, prop, val2)
                        R2 = self.optimize(silent=True)
                        model.set_value(itr, 2, (R2-R1) / (val2-val1))
                    except:
                        pass
                    finally:
                        setattr(item, prop, original_value)
                        self.optimize(silent=True)
                t2 = time.time()
                if (t2-t1) > 0.5:
                    t1 = time.time()
                    while gtk.events_pending():
                        gtk.main_iteration(False)
            self.data_refineables.foreach(for_each_item, None)
    
    def refine(self):
        items = []
        props = []
        values = []
    
        def for_each_item(model, path, itr, user_data=None):
            item, prop, enabled, refine = model.get(itr, 0, 1, 3, 4)
            refine = refine and enabled
            if refine:
                items.append(item)
                props.append(prop)
                values.append(getattr(item, prop))
        
        self.data_refineables.foreach(for_each_item, None)
        
        itemtpls = zip(items, props)
        original_vals = values
        x0 = np.array(values, dtype=float)
        
        def refine_func(new_values): #TODO add threading and some callback?
            #gtk.threads_enter()        
            for i, (item, prop) in enumerate(itemtpls):
                setattr(item, prop, new_values[i])
            return self.optimize(silent=True)
            #gtk.threads_leave()            
            
        bounds = [(0,None) for el in x0]
        iprint = -1 # if not settings.DEBUG else 0
        lastx, lastR2, info = scipy.optimize.fmin_l_bfgs_b(refine_func, x0, approx_grad=True, bounds=bounds, iprint=iprint)
        
                    
    def apply_result(self):
        for i, specimen in enumerate(self.data_specimens):
            specimen.data_phases.clear()
            specimen.data_abs_scale = self.data_scales[i]
            for j, phase in enumerate(self.data_phases):
                phase_obj = self.data_phase_matrix[i,j]
                if phase_obj: specimen.data_phases[phase_obj] = self.data_fractions[j]
