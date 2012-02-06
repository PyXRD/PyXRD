# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from gtkmvc.model import Model, Observer

import numpy as np

from math import sin, cos, pi, sqrt, exp, radians, log

from scipy.special import erf

from generic.utils import lognormal, sqrt2pi, sqrt8

from generic.io import Storable
from generic.models import ChildModel
from generic.treemodels import ObjectListStore
from atoms.models import Atom
from probabilities.models import get_correct_probability_model

class Component(ChildModel, Storable):
    __inheritables__ = ("data_name", "data_based_on",
                        "data_d001", "data_cell_a", "data_cell_b",
                        "data_layer_atoms", "data_interlayer_atoms")

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
    __observables__ = [ key for key, val in __columns__]
    __storables__ = [ val for val in __observables__ if not val in ('data_linked_with', 'parent')]

    data_name = "Name of this component"
    
    inherit_cell_a = False
    inherit_cell_b = False
    inherit_d001 = False
    inherit_layer_atoms = False
    inherit_interlayer_atoms = False

    _data_linked_with = None
    _linked_with_index = None
    @Model.getter("data_linked_with")
    def get_data_linked_with(self, prop_name):
        return self._data_linked_with
    @Model.setter("data_linked_with")
    def set_data_linked_with(self, prop_name, value):
        if self._data_linked_with != value:
            self._data_linked_with = value
            for prop in self.__inheritables__:
                setattr(self, prop.replace("data_", "inherit_", 1), False)
            
    #INHERTIABLE PROPERTIES:
    _data_cell_a = 1.0
    _data_cell_b = 1.0
    _data_d001 = 1.0
    _data_layer_atoms = None
    _data_interlayer_atoms = None
    @Model.getter(*__inheritables__)
    def get_data(self, prop_name):
        inh_name = prop_name.replace("data_", "inherit_", 1)
        if self.data_linked_with != None and getattr(self, inh_name):
            return getattr(self.data_linked_with, prop_name)
        else:
            return getattr(self, "_%s" % prop_name)
    @Model.setter(*__inheritables__)
    def set_data(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)

    def __init__(self, data_name=None, data_cell_a=1.0, data_cell_b=1.0, data_d001=None,
                 data_layer_atoms=None, data_interlayer_atoms=None,
                 inherit_cell_a=False, inherit_cell_b=False, inherit_d001=False, inherit_proportion=False, 
                 inherit_layer_atoms=False, inherit_interlayer_atoms=False,
                 linked_with_index = None, parent=None):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
        self.data_name = data_name or self.data_name
    
        self._data_d001 = data_d001 or self.data_d001
        self._data_cell_a = data_cell_a or self.data_cell_a
        self._data_cell_b = data_cell_b or self.data_cell_b
        
        self._data_layer_atoms = data_layer_atoms or ObjectListStore(Atom)
        self._data_interlayer_atoms = data_interlayer_atoms or ObjectListStore(Atom)
        
        self.inherit_d001 = inherit_d001
        self.inherit_cell_a = inherit_cell_a
        self.inherit_cell_b = inherit_cell_b        
        self.inherit_layer_atoms = inherit_layer_atoms          
        self.inherit_interlayer_atoms = inherit_interlayer_atoms

        self._linked_with_index = linked_with_index if linked_with_index > -1 else None

    #IO STUFF:
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

    def get_structure_factors(self, range_stl):
        sf_tot = np.zeros(range_stl.shape, dtype=np.complex_)
        atoms = (self.data_layer_atoms._model_data + self.data_interlayer_atoms._model_data)
        for atom in atoms:
            sf_tot += atom.get_structure_factors(range_stl)
        return sf_tot

    def get_phase_factors(self, range_stl):
        return np.exp(4*pi*self.data_d001*range_stl*1j)

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


class Phase(ChildModel, Storable):
    __inheritables__ = ("data_mean_CSDS", "data_min_CSDS", "data_max_CSDS", "data_sigma_star", "data_probabilities")
    
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
    __observables__ = [ key for key, val in __columns__]
    __storables__ = [ val for val in __observables__ if not val in ('data_based_on', 'parent')]
    
    #STATIC PROPERTIES & RELATED STUFF (NON-INHERITABLE):
    
    def _unattach_parent(self):
        if self._parent != None:
            self.parent.del_phase(self)
        ChildModel._unattach_parent(self)
        
    def _attach_parent(self):
        if self._parent != None:
            self.parent.add_phase(self)
        ChildModel._attach_parent(self)

    data_name = "Name of this phase"
    
    inherit_mean_CSDS = False
    inherit_min_CSDS = False
    inherit_max_CSDS = False
    inherit_sigma_star = False
    inherit_probabilities = False
    
    based_on_observer = None
    class BasedOnObserver(Observer):
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
                    component.data_linked_with = None
                
    _based_on_index = None #temporary property
    _data_based_on = None
    @Model.getter("data_based_on")
    def get_data_based_on(self, prop_name):
        return self._data_based_on
    @Model.setter("data_based_on")
    def set_data_based_on(self, prop_name, value):
        if self.based_on_observer == None:
            self.based_on_observer = Phase.BasedOnObserver(self)
        elif self._data_based_on is not None:
            self.based_on_observer.relieve_model(self._data_based_on)
        if value == None or value.get_based_on_root() == self or value.parent != self.parent:
            value = None
        self._data_based_on = value
        for component in self.data_components._model_data: #TODO set probs, wt fracs and comp dimensions accordingly!
            component.data_linked_with = None
        if self._data_based_on is not None:
            self.based_on_observer.observe_model(self._data_based_on)
    def get_based_on_root(self):
        if self.data_based_on != None:
            return self.data_based_on.get_based_on_root()
        else:
            return self
    
    #INHERTIABLE PROPERTIES:
    _data_mean_CSDS = 10.0
    _data_min_CSDS = 1.0
    _data_max_CSDS = 50.0
    _data_sigma_star = 3.0
    _data_probabilities = None
    @Model.getter(*__inheritables__)
    def get_data(self, prop_name):
        inh_name = "inherit_" + prop_name.replace("data_", "", 1)
        if self.data_based_on is not None and getattr(self, inh_name):
            return getattr(self.data_based_on, prop_name)
        else:
            return getattr(self, "_%s" % prop_name)
    @Model.setter(*__inheritables__)
    def set_data(self, prop_name, value):
        setattr(self, "_%s" % prop_name, value)
    
    data_components = None    
    @Model.getter("data_G")
    def get_data_G(self, prop_name):
        if self.data_components != None:
            return len(self.data_components._model_data)
        else:
            return 0
            
    _data_R = 0
    @Model.getter("data_R")
    def get_data_R(self, prop_name):
        return self._data_R
    
    def __init__(self, data_name=None, data_mean_CSDS=None, data_max_CSDS=None, data_min_CSDS=None, data_sigma_star=None, data_probabilities=None, data_G=None, data_R=None,
                 inherit_mean_CSDS=False, inherit_min_CSDS=False, inherit_max_CSDS=False, inherit_sigma_star=False, inherit_probabilities=False, inherit_wtfractions=False,
                 based_on_index = None, parent=None):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
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
        self._data_R = data_R or self._data_R
        
        self._data_probabilities = data_probabilities or get_correct_probability_model(self)
        self.inherit_probabilities = inherit_probabilities or self.inherit_probabilities

        self._based_on_index = based_on_index if based_on_index > -1 else None

    #IO STUFF:
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
        phase = type(**kwargs)
        phase.data_components = ObjectListStore.from_json(parent=phase, **data_components)
        return phase

    #CALCULATIONS:
    def get_lorentz_polarisation_factor(self, range_theta, S, S1S2):
        lpf_range = list()
        ss = max(self.data_sigma_star, 0.0000000000001)
        Q = S / (sqrt8 * np.sin(range_theta) * ss)
        T = erf(Q) * sqrt2pi / (2*ss * S) - 2*np.sin(range_theta) * (1 - np.exp(-(Q**2))) / (S**2)
        return (1 + np.cos(2*range_theta)**2) * T / np.sin(range_theta)
    
    __last_Tmean = None
    __last_Tmax = None
    __last_Tmin = None
    __last_Tdistr = None
    __last_Qdistr = None
    def _update_interference_distributions(self):
        Tmean = self.data_mean_CSDS
        Tmax = self.data_max_CSDS
        Tmin = self.data_min_CSDS

        if self.__last_Tmean != Tmean and self.__last_Tmax != Tmax and self.__last_Tmin != Tmin:
            a = 0.9485 * log(Tmean) - 0.017
            b = sqrt(0.103*log(Tmean) + 0.034)
            
            steps = int(Tmax - Tmin)
            
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
                
            self.__last_Tmean = Tmean
            self.__last_Tmax = Tmax
            self.__last_Tmin = Tmin
            self.__last_Trest = (TQDistr.items(), TQDistr, Rmean)
            
        return self.__last_Trest
    
    def get_interference(self, range_stl): #FIXME
        
        Tmean = self.data_mean_CSDS
        d001 = self.data_d001
        
        distr, ddict, real_mean = self._update_interference_distributions()
        
        """ifs_range = list()
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
            
            ifs_range += ifs,"""
        
        phase_range = (2*pi*d001*range_stl)    
        ifs = np.zeros(phase_range.shape)
        for T, q in distr:
            ifs += q * np.sin(phase_range*T)**2 / (np.sin(phase_range)**2)
            
        return ifs
            
    def get_diffracted_intensity (self, range_theta, range_stl, S, S1S2, quantity, correction_range):
        
        """scale = self.get_absolute_scale() * quantity
        lpf = self.get_lorentz_polarisation_factor(range_theta, S, S1S2)
        iff = self.get_interference(range_stl)
        stfa, stfb = self.get_structure_factors(range_stl)
        return (stfa**2 + stfb**2) * lpf * iff * correction_range * scale"""
        
        #TODO: get & read book from Drits & Tchoubar
        # things to remember:
        #  - if I want readable matrix multiplications with numpy, I need to work on per-angle basis and not use arrays/lists inside matrixes/arrays, rather lists of matrixes!
        #  - main performance hit will still be the structure factors so get these once for each component (as it is down here)
        
        distr, ddict, real_mean = self._update_interference_distributions()
        
        W = np.matrix(np.diag(self.data_wtfractions))
        P = np.array(self.data_probabilities)
        
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
        
        F, Q = ([None]*range_stl.size,)*2 #list of matrices containing structure factor matrix and Q matrices
        intensity = np.zeros(range_stl.size, dtype=np.complex_)
        for stl in range(range_stl.size):
            #create F matrix using kronecker product:
            F = np.matrix(numpy.kron(np.matrix(SF[stl]), np.matrix(np.conjugate(SF[stl])).transpose()))
        
            #create probability * phase matrices:
            # - multiply with P (element-wise) with a 2D array composed out of columns containing the phase factor (PFa & PFb) for each component
            Q = np.matrix(P * np.repeat(PF[stl,:,np.newaxis,], G, 1), dtype=np.complex_)
        
            #create empty CSDS probability * phase matrix:
            Qn = [None]*self.data_max_CSDS
            Qn[1] = Q
        
            SubTotal = np.matrix(np.zeros(Qnre[1].shape))
            CSDS_ident = np.matrix(np.identity(Qnre[1].shape[0]) * real_mean)
            for n in range(1, self.data_max_CSDS+1):
                if n > 1:
                    Qn[n] = Qn[n-1] * Q
                factor = 0
                for m in range(n, self.data_max_CSDS+1): #TODO calculate this only once!
                    factor += (m-n)*distr[m]
                SubTotal += (factor*Qn[n])              
            intensity[stl] = np.spur(np.real(F * W * (CSDS_ident + 2*SubTotal)))
            

        scale = self.get_absolute_scale() * quantity
        return intensity*scale

    def get_absolute_scale(self):
        mean_d001 = 0
        mean_volume = 0
        mean_weight =  0
        mean_density = 0
        for wtfraction, component in zip(self.data_wtfractions, self.data_components._model_data):
            mean_d001 += (component.data_d001 * wtfraction)
            mean_volume += (component.get_volume() * wtfraction)
            mean_weight +=  (component.get_weight() * wtfraction)
        mean_density = mean_weight / mean_volume
        
        if self.__last_Tmean == None or self.__last_Tmean != self.data_mean_CSDS:
            distr, ddict, real_mean = self._update_interference_distributions()
        else:
            distr, ddict, real_mean = self.__last_Trest
        
        return mean_d001 / (real_mean *  mean_volume**2 * mean_density);

    def __str__(self):
        return "<PHASE %s(%s) %s>" % (self.data_name, repr(self), self.data_based_on)
