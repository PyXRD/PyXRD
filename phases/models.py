# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from gtkmvc.model import Model, Observer, Signal

import numpy as np
import time

from math import sin, cos, pi, sqrt, exp, radians, log

from scipy.special import erf

from generic.utils import lognormal, sqrt2pi, sqrt8, print_timing, get_md5_hash

from generic.io import Storable, PyXRDDecoder
from generic.models import ChildModel, ObjectListStoreChildMixin
from generic.treemodels import ObjectListStore
from atoms.models import Atom
from probabilities.models import get_correct_probability_model

class Component(ChildModel, ObjectListStoreChildMixin, Storable):

    #MODEL INTEL:
    __refineables__ = ("data_d001", "data_cell_a", "data_cell_b",)
    __inheritables__ = __refineables__ + ("data_layer_atoms", "data_interlayer_atoms")
    __parent_alias__ = "phase"
    __columns__ = [
        ('data_name', str),
        ('data_linked_with', object),
        ('data_cell_a', float),
        ('inherit_cell_a', bool),
        ('data_cell_b', float),
        ('inherit_cell_b', bool),
        ('data_d001', float),
        ('inherit_d001', bool),
        ('data_layer_atoms', float),
        ('inherit_layer_atoms', bool),
        ('data_interlayer_atoms', float),
        ('inherit_interlayer_atoms', bool),
    ]
    __observables__ = [ key for key, val in __columns__] + ["needs_update", "dirty"]
    __storables__ = [ val for val in __observables__ if not val in ("data_linked_with", "parent", "needs_update", "dirty")]

    #SIGNALS:
    needs_update = None

    #PROPERTIES:
    data_name = "Name of this component"
    
    _dirty = True
    def get_dirty_value(self): return self._dirty
    def set_dirty_value(self, value):
        if value!=self._dirty: self._dirty = value
    
    _inherit_cell_a = False
    _inherit_cell_b = False
    _inherit_d001 = False
    _inherit_layer_atoms = False
    _inherit_interlayer_atoms = False
    @Model.getter(*[prop.replace("data_", "inherit_", 1) for prop in __inheritables__])
    def get_inherit_prop(self, prop_name): return getattr(self, "_%s" % prop_name)
    @Model.setter(*[prop.replace("data_", "inherit_", 1) for prop in __inheritables__])
    def set_inherit_prop(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        self.dirty = True
        self.needs_update.emit()

    _data_linked_with = None
    _linked_with_index = None
    def get_data_linked_with_value(self): return self._data_linked_with
    def set_data_linked_with_value(self, value):
        if value != self._data_linked_with:
            if self._data_linked_with != None:
                self.relieve_model(self._data_linked_with)
            self._data_linked_with = value
            self.dirty = True
            if self._data_linked_with==None:
                self.observe_model(self._data_linked_with)
                for prop in self.__inheritables__:
                    setattr(self, prop.replace("data_", "inherit_", 1), False)
            
    #INHERITABLE PROPERTIES:
    _data_cell_a = 1.0
    data_cell_a_range = [0,2.0]
    _data_cell_b = 1.0
    data_cell_b_range = [0,2.0]
    _data_d001 = 1.0
    data_d001_range = [0,2.0]
    _data_layer_atoms = None
    _data_interlayer_atoms = None
    @Model.setter(*__inheritables__)
    def set_inheritable(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        self.dirty = True
        self.needs_update.emit()
    @Model.getter(*__inheritables__)
    def get_inheritable(self, prop_name):
        inh_name = prop_name.replace("data_", "inherit_", 1)
        if self.data_linked_with != None and getattr(self, inh_name):
            return getattr(self.data_linked_with, prop_name)
        else:
            return getattr(self, "_%s" % prop_name)

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name=None, data_cell_a=1.0, data_cell_b=1.0, data_d001=None,
                 data_layer_atoms=None, data_interlayer_atoms=None,
                 inherit_cell_a=False, inherit_cell_b=False, inherit_d001=False, inherit_proportion=False, 
                 inherit_layer_atoms=False, inherit_interlayer_atoms=False,
                 linked_with_index = None, parent=None):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        self.needs_update = Signal()
        self._dirty = True
        
        self.data_name = data_name or self.data_name
    
        self._data_d001 = data_d001 or self.data_d001
        self._data_cell_a = data_cell_a or self.data_cell_a
        self._data_cell_b = data_cell_b or self.data_cell_b
        
        self._data_layer_atoms = data_layer_atoms or ObjectListStore(Atom)
        self._data_interlayer_atoms = data_interlayer_atoms or ObjectListStore(Atom)
        
        def on_item_changed(*args):
            self.dirty = True
            self.needs_update.emit()
        
        self._data_layer_atoms.connect("item-removed", on_item_changed)
        self._data_interlayer_atoms.connect("item-removed", on_item_changed)        
        self._data_layer_atoms.connect("item-inserted", on_item_changed)
        self._data_interlayer_atoms.connect("item-inserted", on_item_changed)
        self._data_layer_atoms.connect("row-changed", on_item_changed)
        self._data_interlayer_atoms.connect("row-changed", on_item_changed)        

        self._linked_with_index = linked_with_index if linked_with_index > -1 else None
        
        self._inherit_d001 = inherit_d001
        self._inherit_cell_a = inherit_cell_a
        self._inherit_cell_b = inherit_cell_b        
        self._inherit_layer_atoms = inherit_layer_atoms          
        self._inherit_interlayer_atoms = inherit_interlayer_atoms


    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Observer.observe("dirty", assign=True)
    def notify_dirty_changed(self, model, prop_name, info):
        if model.dirty: self.dirty = True
        pass
    
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------  
    def resolve_json_references(self):
        for atom in self._data_layer_atoms._model_data:
            atom.resolve_json_references()
        for atom in self._data_interlayer_atoms._model_data:
            atom.resolve_json_references()
        
        if self._linked_with_index != None and self._linked_with_index != -1:
            self.data_linked_with = self.parent.data_based_on.data_components.get_user_data_from_index(self._linked_with_index)
            
    def json_properties(self):
        retval = Storable.json_properties(self)
        retval["linked_with_index"] = self.parent.data_based_on.data_components.index(self.data_linked_with) if self.data_linked_with != None else -1
        return retval
        
    @classmethod          
    def from_json(type, **kwargs):
        project = kwargs['parent'].parent
        kwargs['data_layer_atoms'] = ObjectListStore.from_json(parent=project, **kwargs['data_layer_atoms']['properties'])
        kwargs['data_interlayer_atoms'] = ObjectListStore.from_json(parent=project, **kwargs['data_interlayer_atoms']['properties'])
        return type(**kwargs)

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------  
    def get_structure_factors(self, range_stl):
        sf_tot = np.zeros(range_stl.shape, dtype=np.complex_)
        atoms = (self.data_layer_atoms._model_data + self.data_interlayer_atoms._model_data)
        for atom in atoms:
            sf_tot += atom.get_structure_factors(range_stl)
        return sf_tot

    def get_phase_factors(self, range_stl):
        return np.exp(2*pi*self.data_d001*range_stl*1j)

    def get_cell_a(self):
        return self.data_cell_a
        
    def get_cell_b(self):
        return self.data_cell_b
        
    def get_cell_c(self):
        return self.data_d001

    def get_volume(self):
        return self.get_cell_a() * self.get_cell_b() * self.get_cell_c()

    def get_weight(self):
        weight = 0
        for atom in (self.data_layer_atoms._model_data + self.data_interlayer_atoms._model_data):
            weight += atom.data_pn * atom.data_atom_type.data_weight
        return weight


class Phase(ChildModel, ObjectListStoreChildMixin, Storable):

    #MODEL INTEL:
    __refineables__ = ("data_mean_CSDS", "data_sigma_star")
    __inheritables__ = __refineables__ + ("data_min_CSDS", "data_max_CSDS", "data_probabilities")
    __parent_alias__ = 'project'
    __columns__ = [
        ('data_name', str),
        ('data_based_on', object),
        ('inherit_mean_CSDS', bool),
        ('data_mean_CSDS', float),
        ('inherit_min_CSDS', bool),
        ('data_min_CSDS', float),
        ('inherit_max_CSDS', bool),
        ('data_max_CSDS', float),
        ('inherit_sigma_star', bool),
        ('data_sigma_star', float),
        ('data_probabilities', object),
        ('inherit_probabilities', bool),
        ('data_G', int),
        ('data_R', int),
        ('data_components', object),
    ]
    __observables__ = [ key for key, val in __columns__] + ["needs_update", "dirty"]
    __storables__ = [ val for val in __observables__ if not val in ("data_based_on", "parent", "needs_update", "dirty")]
    
    #SIGNALS:
    needs_update = None
    
    #PROPERTIES:
    data_name = "Name of this phase"
    
    _dirty = True
    def get_dirty_value(self): return self._dirty
    def set_dirty_value(self, value):
        if value!=self._dirty:
            self._dirty = value
            self._cached_diffracted_intensities = dict()

    
    _inherit_mean_CSDS = False
    _inherit_min_CSDS = False
    _inherit_max_CSDS = False
    _inherit_sigma_star = False
    _inherit_probabilities = False
    @Model.getter(*[prop.replace("data_", "inherit_", 1) for prop in __inheritables__])
    def get_inherit_prop(self, prop_name): return getattr(self, "_%s" % prop_name)
    @Model.setter(*[prop.replace("data_", "inherit_", 1) for prop in __inheritables__])    
    def set_inherit_prop(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
        self.dirty = True
        self.needs_update.emit()
    
    based_on_observer = None
    """class BasedOnObserver(Observer): #FIXME MOVE THIS DOWN!
        phase = None
        
        def __init__(self, phase, *args, **kwargs):
            self.phase = phase
            Observer.__init__(self, *args, **kwargs)
        
        @Observer.observe("removed", signal=True)
        def notification(self, model, prop_name, info):
            #model      = phase that we're observing
            #self.phase = phase that is observing the model
            if model == self.phase.data_based_on: #this check is not 100% neccesary, but it can't hurt either
                self.phase.data_based_on = None
                for component in self.phase.data_components:
                    component.data_linked_with = None"""
                
    _based_on_index = None #temporary property
    _data_based_on = None
    def get_data_based_on_value(self): return self._data_based_on
    def set_data_based_on_value(self, value):
        if self._data_based_on is not None:
            self.relieve_model(self._data_based_on)
        if value == None or value.get_based_on_root() == self or value.parent != self.parent:
            value = None
        if value != self._data_based_on:
            self._data_based_on = value
            for component in self.data_components._model_data:
                component.data_linked_with = None
        if self._data_based_on is not None:
            self.observe_model(self._data_based_on)
        self.dirty = True
        self.needs_update.emit()
    def get_based_on_root(self):
        if self.data_based_on != None:
            return self.data_based_on.get_based_on_root()
        else:
            return self
    
    #INHERITABLE PROPERTIES:
    _data_mean_CSDS = 10.0
    data_mean_CSDS_range = [0,500]
    _data_min_CSDS = 1.0
    _data_max_CSDS = 50.0
    _data_sigma_star = 3.0
    data_sigma_star_range = [0,90]
    _data_probabilities = None
    @Model.getter(*__inheritables__)
    def get_inheritable(self, prop_name):
        inh_name = "inherit_" + prop_name.replace("data_", "", 1)
        if self.data_based_on is not None and getattr(self, inh_name):
            return getattr(self.data_based_on, prop_name)
        else:
            return getattr(self, "_%s" % prop_name)
    @Model.setter(*__inheritables__)
    def set_inheritable(self, prop_name, value):
        prob = (prop_name == "data_probabilities")
        if prob and self._data_probabilities:
            self.relieve_model(self._data_probabilities)
        setattr(self, "_%s" % prop_name, value)
        if prob and self._data_probabilities:
            self.observe_model(self._data_probabilities)
        self.dirty = True
        self.needs_update.emit()
    
    _data_components = None    
    def get_data_components_value(self): return self._data_components
    def set_data_components_value(self, value):
        if self._data_components != None:
            for comp in self._data_components._model_data: self.relieve_model(comp)
        self._data_components = value
        if self._data_components != None:
            for comp in self._data_components._model_data: self.observe_model(comp)
        self.dirty = True
    def get_data_G_value(self):
        if self.data_components != None:
            return len(self.data_components._model_data)
        else:
            return 0
            
    _data_R = 0
    def get_data_R_value(self):
        return self._data_R
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data_name=None, data_mean_CSDS=None, data_max_CSDS=None, data_min_CSDS=None, data_sigma_star=None, data_probabilities=None, data_G=None, data_R=0,
                 inherit_mean_CSDS=False, inherit_min_CSDS=False, inherit_max_CSDS=False, inherit_sigma_star=False, inherit_probabilities=False, inherit_wtfractions=False,
                 based_on_index = None, parent=None):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        self._dirty = True
        self._cached_diffracted_intensities = dict()
        
        self.needs_update = Signal()
        
        self.data_name = data_name or self.data_name
    
        self._data_mean_CSDS = data_mean_CSDS or self.data_mean_CSDS
        self._data_min_CSDS = data_min_CSDS or self.data_min_CSDS
        self._data_max_CSDS = data_max_CSDS or self.data_max_CSDS
        self._data_sigma_star = data_sigma_star or self.data_sigma_star 
               
        self.inherit_mean_CSDS = inherit_mean_CSDS
        self.inherit_min_CSDS = inherit_min_CSDS
        self.inherit_max_CSDS = inherit_max_CSDS
        self.inherit_sigma_star = inherit_sigma_star

        if data_G != None and data_G > 0:
            self.data_components = ObjectListStore(Component)
            for i in range(data_G):
                new_comp = Component("Component %d" % (i+1), parent=self)
                self.data_components.append(new_comp)
                self.observe_model(new_comp)
        self._data_R = data_R
        
        self._data_probabilities = data_probabilities or get_correct_probability_model(self)
        self.observe_model(self._data_probabilities)
        self.inherit_probabilities = inherit_probabilities or self.inherit_probabilities

        self._based_on_index = based_on_index if based_on_index > -1 else None

    def __str__(self):
        return "<PHASE %s(%s) %s>" % (self.data_name, repr(self), self.data_based_on)

    """def _unattach_parent(self):
        if self._parent != None:
            self.parent.del_phase(self)
        ChildModel._unattach_parent(self)
        
    def _attach_parent(self):
        if self._parent != None and not self.parent.data_phases.item_in_model(self):
            self.parent.data_phases.append(self)
        ChildModel._attach_parent(self)"""

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Observer.observe("needs_update", signal=True)
    def notify_needs_update(self, model, prop_name, info):
        self.needs_update.emit() #propagate signal
        
    @Observer.observe("dirty", assign=True)
    def notify_dirty_changed(self, model, prop_name, info):
        if model.dirty: self.dirty = True
        pass

    @Observer.observe("updated", signal=True)
    def notify_updated(self, model, prop_name, info):
        self.dirty = True
        self.needs_update.emit() #propagate signal

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------  
    def resolve_json_references(self):
        if self._based_on_index != None and self._based_on_index != -1:
            self.data_based_on = self.parent.data_phases.get_user_data_from_index(self._based_on_index)
        for component in self.data_components._model_data:
            component.resolve_json_references()
    
    def json_properties(self):
        retval = Storable.json_properties(self)
        retval["based_on_index"] = self.parent.data_phases.index(self.data_based_on) if self.data_based_on != None else -1
        return retval
    
    @classmethod          
    def from_json(type, **kwargs):
        # strip components, setup phase and generate components
        data_components = kwargs['data_components']['properties']
        del kwargs['data_components']
        data_probabilities = kwargs['data_probabilities']
        del kwargs['data_probabilities']
        
        phase = type(**kwargs)
        phase.data_components = ObjectListStore.from_json(parent=phase, **data_components)
        phase.data_probabilities = PyXRDDecoder(parent=phase).__pyxrd_decode__(data_probabilities)
        return phase

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------  
    """def get_lorentz_polarisation_factor(self, range_theta, S, S1S2):
        ss = max(self.data_sigma_star, 0.0000000000001)
        Q = S / (sqrt8 * np.sin(range_theta) * ss)
        T = erf(Q) * sqrt2pi / (2.0*ss * S) - 2.0*np.sin(range_theta) * (1.0- np.exp(-(Q**2.0))) / (S**2.0)
        return (1.0 + np.cos(2.0*range_theta)**2) * T / np.sin(range_theta)"""    
    
    __last_Tmean = None
    __last_Tmax = None
    __last_Tmin = None
    __last_Tdistr = None
    __last_Qdistr = None
    def _update_interference_distributions(self):
        Tmean = max(self.data_mean_CSDS, 1)
        Tmax = self.data_max_CSDS
        Tmin = self.data_min_CSDS

        if self.__last_Tmean != Tmean or self.__last_Tmax != Tmax or self.__last_Tmin != Tmin:
            a = 0.9485 * log(Tmean) - 0.017
            b = sqrt(0.1032*log(Tmean) + 0.0034)
            
            steps = int(Tmax - Tmin) + 1
            
            smq = 0
            q_log_distr = []
            TQDistr = dict()
            for i in range(steps):
                T = max(Tmin + i, 1e-50)
                q = lognormal(T, a, b)
                smq += q
                
                TQDistr[int(T)] = q
                
            Rmean = 0
            for T,q in TQDistr.iteritems():
                TQDistr[T] = q / smq
                Rmean += T*q
            Rmean /= smq
            self.__last_Tmean = Tmean
            self.__last_Tmax = Tmax
            self.__last_Tmin = Tmin
            self.__last_Trest = (TQDistr.items(), TQDistr, Rmean)
            
        return self.__last_Trest
    
    """def get_interference(self, range_stl): #FIXME
        
        Tmean = self.data_mean_CSDS
        d001 = self.data_d001
        
        distr, ddict, real_mean = self._update_interference_distributions()
        
        ""ifs_range = list()
        for stl in range_stl: 
            ifs = 0
            if False:
                #calculate the summation:
                Tmax = distr[-1][0]
                f = 4*pi*d001*stl
                for T, q in distr:
                    fact = 0
                    for t in range(int(T+1), Tmax):
                        fact += (t-T)*ddict[t]
                    ifs += fact*cos(f*T)
                    real_mean += T*q
                ifs = ifs*2 + real_mean
            else:        
                f = 2*pi*d001*stl
                for T, q in distr:
                    ifs += (q*(sin(f*T)**2) / (sin(f)**2))
            
            ifs_range += ifs,""
        
        phase_range = (2*pi*d001*range_stl)    
        ifs = np.zeros(phase_range.shape)
        for T, q in distr:
            ifs += q * np.sin(phase_range*T)**2 / (np.sin(phase_range)**2)
            
        return ifs"""
       
    #@print_timing
    _cached_diffracted_intensities = None
    def get_diffracted_intensity (self, range_theta, range_stl, lpf_callback, quantity, correction_range):
        hsh = get_md5_hash(range_theta)
        if self.dirty or not hsh in self._cached_diffracted_intensities:
            #print "for specimen %s" % self
            from numpy.core.umath_tests import matrix_multiply as mmultr
            def mmult(A, B):
                return np.sum(np.transpose(A,(0,2,1))[:,:,:,np.newaxis]*B[:,:,np.newaxis,:],-3)
            def mdot(A,B):
                C = np.zeros(shape=A.shape, dtype=np.complex)
                for i in range(A.shape[0]):
                    C[i] = np.dot(A[i], B[i])
                return C
            def mtim(A,B):
                C = np.zeros(shape=A.shape, dtype=np.complex)
                for i in range(A.shape[0]):
                    C[i] = np.multiply(A[i], B[i])
                return C
                    
                
            def solve_division(A,B):
                bt = np.transpose(B, axes=(0,2,1))
                at = np.transpose(A, axes=(0,2,1))
                return np.array([np.transpose(np.linalg.lstsq(bt[i], at[i])[0]) for i in range(bt.shape[0])])

            stl_dim = range_stl.shape[0]
            def repeat_to_stl(arr):
                return np.repeat(arr[np.newaxis,...], stl_dim, axis=0)
           
            #Get interference (log-normal) distribution:
            distr, ddict, real_mean = self._update_interference_distributions()
            
            #Get junction probabilities & weight fractions
            W, P = self.data_probabilities.get_distribution_matrix(), self.data_probabilities.get_probability_matrix()
            
            W = repeat_to_stl(W).astype(np.complex_)
            P = repeat_to_stl(P).astype(np.complex_)
            G = self.data_G
            
            #get structure factors and phase factors for individual components:
            #        components
            #       .  .  .  .  .  .
            #  stl  .  .  .  .  .  .
            #       .  .  .  .  .  .
            #
            shape = range_stl.shape + (G,)
            SF = np.zeros(shape, dtype=np.complex_)
            PF = np.zeros(shape, dtype=np.complex_)
            for i, component in enumerate(self.data_components._model_data):
                SF[:,i] = component.get_structure_factors(range_stl)
                PF[:,i] = component.get_phase_factors(range_stl)
                component.dirty = False
            
            intensity = np.zeros(range_stl.size, dtype=np.complex_)
            first = True

            rank = P.shape[1]
            reps = rank / G
             
            #Create Phi & F matrices:        
            SFa = np.repeat(SF[...,np.newaxis,:], SF.shape[1], axis=1)
            SFb = np.transpose(np.conjugate(SFa), axes=(0,2,1)) #np.conjugate(np.repeat(SF[...,np.newaxis], SF.shape[1], axis=2)) 
                   
            F = np.repeat(np.repeat(np.multiply(SFb, SFa), reps, axis=2), reps, axis=1)

            #Create Q matrices:
            PF = np.repeat(PF[...,np.newaxis,:], reps, axis=1)
            Q = np.multiply(np.repeat(np.repeat(PF, reps, axis=2), reps, axis=1), P)
                              
            #Calculate the intensity:
            method = 0
                
            if method == 0:
                ################### FIRST WAY ###################                 
                
                Qn = np.empty((self.data_max_CSDS+1,), dtype=object)
                Qn[1] = np.copy(Q)
                for n in range(2, int(self.data_max_CSDS+1)):
                    Qn[n] = mmult(Qn[n-1], Q)
                      
                SubTotal = np.zeros(Q.shape, dtype=np.complex)
                CSDS_I = repeat_to_stl(np.identity(rank, dtype=np.complex) * real_mean)
                for n in range(1, int(self.data_max_CSDS)+1):
                    factor = 0
                    for m in range(n+1, int(self.data_max_CSDS)+1):
                        factor += (m-n) * ddict[m]
                    SubTotal += 2 * factor * Qn[n]
                SubTotal = (CSDS_I + SubTotal)
                SubTotal = mmult(mmult(F, W), SubTotal)
                intensity = np.real(np.trace(SubTotal,  axis1=2, axis2=1))
            elif method == 1:
                ################### SCND WAY ################### #FIXME doesn't work for now
                SubTotal = np.zeros(Q.shape, dtype=np.complex_)
                I = repeat_to_stl(np.identity(rank))
                CSDS_I = repeat_to_stl(np.identity(rank, dtype=np.complex_) * real_mean)
                      
                Qn = np.empty((self.data_max_CSDS+1,), dtype=object)
                Qn[1] = np.copy(Q)
                for n in range(2, int(self.data_max_CSDS+1)):
                    Qn[n] = mmult(Qn[n-1], Q)
                      
                IQ = (I-Q)
                IIQ = solve_division(I, IQ)
                IIQ2 = solve_division(I, mmult(IQ,IQ))
                R = np.zeros(Q.shape, dtype=np.complex_)
                for n in range(1, int(self.data_max_CSDS)):
                    R = (I + 2*Q*IIQ + (2 / n) * (Qn[n+1]-Q) * IIQ2) * ddict[n]
                    intensity += np.real(np.trace(mmult(mmult(F, W), R), axis1=2, axis2=1))
                
            lpf = lpf_callback(range_theta, self.data_sigma_star)
            scale = self.get_absolute_scale() * quantity
            self.dirty = False
            self._cached_diffracted_intensities[hsh] = intensity * correction_range * scale * lpf
        return self._cached_diffracted_intensities[hsh]

    def get_absolute_scale(self):
        mean_d001 = 0
        mean_volume = 0
        mean_density = 0
        W = self.data_probabilities.get_distribution_array()
        for wtfraction, component in zip(W, self.data_components._model_data):
            mean_d001 += (component.data_d001 * wtfraction)
            volume = component.get_volume()
            mean_volume += (volume * wtfraction)
            mean_density +=  (component.get_weight() * wtfraction / volume)
        
        if self.__last_Tmean == None or self.__last_Tmean != self.data_mean_CSDS:
            distr, ddict, real_mean = self._update_interference_distributions()
        else:
            distr, ddict, real_mean = self.__last_Trest
        
        return mean_d001 / (real_mean *  mean_volume**2 * mean_density);

    pass #end of class
