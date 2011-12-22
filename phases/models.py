# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from gtkmvc.model import Model, Observer

from math import sin, cos, pi, sqrt, exp, radians, log
from operator import mul

from generic.utils import erf, lognormal, sqrt2pi, sqrt8

from generic.io import Storable
from generic.models import ChildModel
from generic.treemodels import ObjectListStore
from atoms.models import Atom

"""
    Phases are to be replaced by SingleLayerMinerals
"""
class Phase(ChildModel, Storable):

    __inheritables__ = ("data_mean_CSDS", "data_min_CSDS", "data_max_CSDS", "data_sigma_star", "data_d001", 
                        "data_proportion", "data_layer_atoms", "data_interlayer_atoms")
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
        ('inherit_d001', bool),
        ('data_d001', float),
        ('inherit_proportion', bool),
        ('data_proportion', float),
        ('inherit_layer_atoms', bool),
        ('data_layer_atoms', None),
        ('inherit_interlayer_atoms', bool),
        ('data_interlayer_atoms', None)
    ]   
    __observables__ = [ key for key, val in __columns__]
    __storables__ = [ val for val in __observables__ if val is not 'data_based_on']
    
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
    inherit_d001 = False
    inherit_proportion = False
    inherit_layer_atoms = False
    inherit_interlayer_atoms = False
    
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
    _data_d001 = 1.0
    _data_proportion = 1.0
    _data_layer_atoms = None
    _data_interlayer_atoms = None
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
    
    
    def __init__(self, data_name=None, data_mean_CSDS=None, data_max_CSDS=None, data_min_CSDS=None, data_sigma_star=None, data_d001=None, data_proportion=None,
                 inherit_mean_CSDS=False, inherit_min_CSDS=False, inherit_max_CSDS=False, inherit_sigma_star=False, inherit_d001=False, inherit_proportion=False, 
                 inherit_layer_atoms=False, inherit_interlayer_atoms=False,
                 based_on_index = None, data_layer_atoms=None, data_interlayer_atoms=None, parent=None):
        ChildModel.__init__(self, parent=parent)
        Storable.__init__(self)
        
        self.data_name = data_name or self.data_name
    
        self._data_mean_CSDS = data_mean_CSDS or self.data_mean_CSDS
        self._data_min_CSDS = data_min_CSDS or self.data_min_CSDS
        self._data_max_CSDS = data_max_CSDS or self.data_max_CSDS
        self._data_sigma_star = data_sigma_star or self.data_sigma_star 
        self._data_d001 = data_d001 or self.data_d001
        self._data_proportion = data_proportion or self.data_proportion
        
        self._data_layer_atoms = data_layer_atoms or ObjectListStore(Atom)
        self._data_interlayer_atoms = data_interlayer_atoms or ObjectListStore(Atom)
        
        self.inherit_mean_CSDS = inherit_mean_CSDS
        self.inherit_min_CSDS = inherit_min_CSDS
        self.inherit_max_CSDS = inherit_max_CSDS
        self.inherit_sigma_star = inherit_sigma_star
        self.inherit_d001 = inherit_d001
        self.inherit_proportion = inherit_proportion
        self.inherit_layer_atoms = inherit_layer_atoms          
        self.inherit_interlayer_atoms = inherit_interlayer_atoms

        self._based_on_index = based_on_index if based_on_index > -1 else None

    #IO STUFF:
    def resolve_json_references(self):
        for atom in self._data_layer_atoms._model_data:
            atom.resolve_json_references()
        for atom in self._data_interlayer_atoms._model_data:
            atom.resolve_json_references()            
        if self._based_on_index != None and self._based_on_index != -1:
            self.data_based_on = self.parent.data_phases.get_user_data_from_index(self._based_on_index)
    
    def json_properties(self):
        retval = Storable.json_properties(self)
        retval["based_on_index"] = self.parent.data_phases.index(self.data_based_on) if self.data_based_on != None else -1
        return retval
    
    @staticmethod          
    def from_json(**kwargs):
        print "FROM JSON CALLED WITH kwargs['parent'] = %s" % kwargs['parent']
        kwargs['data_layer_atoms'] = ObjectListStore.from_json(parent=kwargs['parent'], **kwargs['data_layer_atoms']['properties'])
        kwargs['data_interlayer_atoms'] = ObjectListStore.from_json(parent=kwargs['parent'], **kwargs['data_interlayer_atoms']['properties'])
        return Phase(**kwargs)

    #CALCULATIONS:   
    def get_structure_factors(self, stl):
        sfa, sfb = 0, 0
        sfa_tot, sfb_tot = 0, 0
        for atom in (self.data_layer_atoms._model_data + self.data_interlayer_atoms._model_data):
            sfa, sfb = atom.get_structure_factors(stl)
            sfa_tot += sfa*2
            sfb_tot += sfb*2
        return sfa_tot, sfb_tot
    
    def get_lorentz_polarisation_factor(self, theta, S, S1S2):
        ss = max(self.data_sigma_star, 0.0000000000001)
        Q = S / (sqrt8 * sin(theta) * ss)
        T = erf(Q) * sqrt2pi / (2*ss * S) - 2*sin(theta) * (1 - exp(-(Q**2))) / (S**2)
        return (1 + cos(2*theta)**2) * T / sin(theta)
    
    __last_Tmean = None
    __last_Tdistr = None
    __last_Qdistr = None
    def _get_interference_distributions(self):
        Tmean = self.data_mean_CSDS
        #if self.__last_Tmean != None and self.__last_Tmean == Tmean:
        #    return zip(self.__last_Tdistr, self.__last_Qdistr)
        #else:
            #lognormal distribution according to Drits et al 1997:
        a = 0.9485 * log(Tmean) - 0.017
        b = sqrt(0.103*log(Tmean) + 0.034)
        
        Tmax = self.data_max_CSDS
        Tmin = self.data_min_CSDS
        steps = int(Tmax - Tmin)
        
        smq = 0
        q_log_distr = []
        Qdistr = []
        Tdistr = []
        for i in range(steps):
            T = max(Tmin + i, 1e-50)
            q = lognormal(T, a, b)
            smq += q
            
            Qdistr.append(q)
            Tdistr.append(int(T))
            
        Rmean = 0
        for i in range(steps):
            Qdistr[i] = Qdistr[i] / smq
            Rmean += Tdistr[i]*Qdistr[i]
            
        self.__last_Tmean = Tmean
        self.__last_Rmean = Rmean
        self.__last_Tdistr = Tdistr
        self.__last_Qdistr = Qdistr
        
        return zip(Tdistr, Qdistr), Rmean
    
    #TODO make this a range function:
    def get_interference(self, stl):
        
        #get the distribution functions for CSDS:
        distr, real_mean = self._get_interference_distributions()
        ddict = dict(distr)
            
        if False:
            #calculate the summation:
            ifs = 0
            Tmax = distr[-1][0]
            f = 4*pi*self.data_d001*stl
            for T, q in distr:
                fact = 0
                for t in range(int(T+1), Tmax):
                    fact += (t-T)*ddict[t]
                ifs += fact*cos(f*T)
                real_mean += T*q
            ifs = ifs*2 + real_mean
        else:        
            ifs = 0
            f = 2*pi*self.data_d001*stl
            for T, q in distr:
                ifs += (q*(sin(f*T)**2) / (sin(f)**2))
        
        return ifs
            
    def get_absolute_diffracted_intensity (self, theta, stl, S, S1S2):
        lpf = self.get_lorentz_polarisation_factor(theta, S, S1S2)
        iff = self.get_interference(stl)
        stfa, stfb = self.get_structure_factors(stl)
        stf2 = stfa**2 + stfb**2
        return lpf, iff, stf2, (lpf * iff * stf2)
    
    def get_relative_diffracted_intensity (self, theta, stl, S, S1S2):
        lpf, iff, stf, absint = self.get_absolute_diffracted_intensity(theta, stl, S, S1S2)
        return lpf, iff, stf, absint * self.get_absolute_scale()

    def get_absolute_scale(self):
        scale = self.data_proportion
    
        mean_d001 = self.data_d001
        mean_density = self.get_density()
        mean_volume = self.get_volume()
    
        distr, real_mean = self._get_interference_distributions()
        
        return scale * mean_d001 / (real_mean *  mean_volume**2 * mean_density);

    def get_cell_a(self):
        return self.get_cell_b() / sqrt(3.0)
        
    def get_cell_b(self):
        return 9.22; #just for now
        
    def get_cell_c(self):
        return self.data_d001

    def get_volume(self):
        return self.get_cell_a() * self.get_cell_b() * self.get_cell_c()

    def get_weight(self):
        weight = 0
        for atom in (self.data_layer_atoms._model_data + self.data_interlayer_atoms._model_data):
            weight += atom.data_pn * atom.data_atom_type.data_weight
        return weight

    def get_density(self):
        return self.get_weight() / self.get_volume()
        


    def __str__(self):
        return "<PHASE %s(%s) %s>" % (self.data_name, repr(self), self.data_based_on)
