# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from traceback import format_exc
from math import sqrt

import gtk
import gobject

import numpy as np
from scipy import stats

from generic.models import PyXRDLine, ChildModel, PropIntel

class Statistics(ChildModel):

    #MODEL INTEL:
    __parent_alias__ = 'specimen'
    __model_intel__ = [ #TODO add labels
        PropIntel(name="points",            data_type=int,   has_widget=True),
        PropIntel(name="residual_pattern",  data_type=object),
        PropIntel(name="Rp",                data_type=float, has_widget=True),
        PropIntel(name="Rwp",               data_type=float, has_widget=True),
        PropIntel(name="Re",                data_type=float, has_widget=True),
        PropIntel(name="chi2",              data_type=float, has_widget=True),
        PropIntel(name="R2",                data_type=float, has_widget=True),
    ]
    
    #PROPERTIES:
    def set_parent_value(self, value):
        ChildModel.set_parent_value(self, value)
        self.update_statistics()
       
    def get_points_value(self):
        try:
            e_ex, e_ey, e_cx, e_cy = self.specimen.get_exclusion_xy()
            return e_ex.size
        except: pass
        return 0

    Rp = None
    Rwp = None
    Re = None
    chi2 = None      
    R2 = None
    residual_pattern = None
         
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    def _get_experimental(self):
        if self.specimen != None:
            x, y = self.specimen.experimental_pattern.xy_store.get_raw_model_data()
            return x.copy(), y.copy()
        else:
            return None, None
    def _get_calculated(self):
        if self.specimen != None:
            x, y = self.specimen.calculated_pattern.xy_store.get_raw_model_data()
            return x.copy(), y.copy()
        else:
            return None, None 
             
    def scale_factor_y(self, offset):
        return self.specimen.scale_factor_y(offset) if self.specimen else (1.0, offset)
      
    def update_statistics(self, num_params=0):
        self.Rp = 0
        self.Rwp = 0
        self.Re = 0
        self.chi2 = 0        
        self.R2 = 0
        if self.residual_pattern == None:
            self.residual_pattern = PyXRDLine(label="Residual Data", color="#000000", parent=self)
        
        exp_x, exp_y = self._get_experimental()
        cal_x, cal_y = self._get_calculated()

        try:
            if cal_y != None and exp_y != None and cal_y.size > 0 and exp_y.size > 0:
                self.residual_pattern.set_data(exp_x, exp_y - cal_y)

                e_ex, e_ey, e_cx, e_cy = self.specimen.get_exclusion_xy()

                #self.chi2 = stats.chisquare(e_ey, e_cy)[0]
                #if exp.size > 0:
                self.R2 = self._calc_R2(e_ey, e_cy)
                self.Rp  = self._calc_Rp(e_ey, e_cy)
                self.Rwp = self._calc_Rwp(e_ey, e_cy)
                self.Re = self._calc_Re(e_ey, e_cy, num_params)                
                self.chi2 = (self.Rwp / self.Re) ** 2
            else:
                self.residual_pattern.clear()                    
        except ValueError, ZeroDivisionError:
            self.residual_pattern.clear()
            print "Error occured when trying to calculate statistics, aborting calculation!"
            print format_exc()
           
       
    @staticmethod
    def _calc_R2(exp, calc):
        avg = sum(exp)/exp.size
        sserr = np.sum((exp - calc)**2)
        sstot = np.sum((exp - avg)**2)
        return 1 - (sserr / sstot)
        
    @staticmethod
    def _calc_Rp(exp, calc):
        return np.sum(np.abs(exp - calc)) / np.sum(np.abs(exp)) * 100

    @staticmethod
    def _calc_Rwp(exp, calc):
        #weighted Rp:   
        # Rwp = Sqrt ( Sum[w * (obs - calc)²] / Sum[w * obs²] )  w = 1 / Iobs
        sm1 = 0
        sm2 = 0
        for i in range(exp.size):
            t = (exp[i] - calc[i])**2 / exp[i]
            if not (np.isnan(t) or np.isinf(t)):
                sm1 += t        
                sm2 += abs(exp[i])
        try:
            return sqrt(sm1 / sm2) * 100
        except:
            return 0

    @staticmethod
    def _calc_Re(exp, calc, num_params):
        # R expected:
        # Re = Sqrt( (Points - Params) / Sum[ w * obs² ] )    
        num_points = exp.size
        return np.sqrt( (num_points - num_params) / np.sum(exp**2) ) * 100
    
    pass #end of class
