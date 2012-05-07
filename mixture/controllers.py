# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import locale

import gtk

from gtkmvc import Controller, Observer
from gtkmvc.adapters import Adapter

from generic.plot_controllers import DraggableVLine, EyedropperCursorPlot
from generic.models import XYData
from generic.controllers import DialogController, DialogMixin, ChildController, ObjectListStoreController, HasObjectTreeview, get_color_val, ctrl_setup_combo_with_list
from generic.validators import FloatEntryValidator
from generic.utils import get_case_insensitive_glob

from phases.models import Phase, Component

from mixture.models import Mixture
from mixture.views import EditMixtureView, RefinementView, BusyView

class RefinementController(DialogController):
    def register_adapters(self):
        if self.model is not None:
            tv = self.view['tv_param_selection']
            tv_model = self.model.data_refineables
            tv.set_model(tv_model)
            #tv.connect('cursor_changed', self.on_exp_data_tv_cursor_changed)

            rend = gtk.CellRendererText()
            col = gtk.TreeViewColumn('Name/Prop', rend)
            def get_name(column, cell, model, itr, user_data=None):
                ref_prop = model.get_user_data(itr)
                cell.set_property("markup", ref_prop.title)
                return
            col.set_cell_data_func(rend, get_name, data=None)
            col.set_expand(True)                
            tv.append_column(col)
            
            def get_name(column, cell, model, itr, user_data=None):
                ref_prop = model.get_user_data(itr)
                refineable = ref_prop.refineable
                cell.set_sensitive(refineable)
                cell.set_property("markup", ("%.5f" % ref_prop.sensitivity) if refineable else "")
                return            
            rend = gtk.CellRendererText()
            col = gtk.TreeViewColumn("Sensitivity [%]", rend, text=3)
            col.set_cell_data_func(rend, get_name, data=None)              
            tv.append_column(col)
            
            def add_editable_float(title, prop_name, callback):                
                def get_name(column, cell, model, itr, user_data=None):
                    ref_prop = model.get_user_data(itr)
                    refineable = ref_prop.refineable
                    cell.set_property("editable", refineable)        
                    cell.set_sensitive(refineable)
                    cell.set_property("markup", ("%.5f" % getattr(ref_prop, prop_name)) if refineable else "")
                    return
                rend = gtk.CellRendererText()
                rend.connect("edited", callback, prop_name)
                col = gtk.TreeViewColumn(title, rend, text=3)
                col.set_cell_data_func(rend, get_name, data=None)              
                tv.append_column(col)
            def on_value_minmax_edited(rend, path, new_text, prop_name):
                ref_prop = self.model.data_refineables.get_user_data_from_path((int(path),))
                setattr(ref_prop, prop_name, float(new_text))
            add_editable_float("Min", "value_min", on_value_minmax_edited)
            add_editable_float("Max", "value_max", on_value_minmax_edited)      
            
            def get_refine(column, cell, model, itr, user_data=None):
                ref_prop = model.get_user_data(itr)
                cell.set_sensitive(ref_prop.refineable)
                cell.set_property("activatable", ref_prop.refineable)
                cell.set_property("visible", ref_prop.refineable) 
                cell.set_property("active", ref_prop.refineable and ref_prop.refine)
                return
            rend = gtk.CellRendererToggle()
            rend.connect('toggled', self.refine_toggled, tv_model)
            col = gtk.TreeViewColumn("Refine", rend, active=4)
            col.set_cell_data_func(rend, get_refine)
            col.activatable = True
            col.set_resizable(False)
            col.set_expand(False)
            tv.append_column(col)
            
            
            for name in self.model.get_properties():
                pass#TODO
            return

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    """@Controller.observe("bg_type", assign=True)
    def notif_bg_type_changed(self, model, prop_name, info):
        self.view.select_bg_view(self.model.get_bg_type_lbl().lower())
        return"""
            
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def refine_toggled(self, cell, path, model=None, col=4):
        if model is not None:
            itr = model.get_iter(path)
            refine = cell.get_active()
            model.set_value(itr, col, not refine)
        return True
        
    def on_refine_clicked(self,event):
        #TODO display progress window...
        busy = BusyView(parent=self.view)
        busy.present()
        self.model.refine(busy.set_R)
        busy.hide()
        pass
        
    def on_sens_clicked(self,event):
        self.model.update_sensitivities()
        
    pass #end of class
        
class EditMixtureController(ChildController):

    chicken_egg = False
    ref_view = None

    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "data_name":
                    self.adapt(name, "mixture_data_name")
                elif not name in self.model.__have_no_widget__+  ["data_refineables"]:
                    self.adapt(name)
            self.create_ui()
            return
            
    def create_ui(self):
        self.view.reset_view()
        for index, phase in enumerate(self.model.data_phases):
            self.add_phase_view(index)
        for index, specimen in enumerate(self.model.data_specimens):
            self.add_specimen_view(index)
            
    #def update_sensitivities(self):
    #    self.view["marker_data_angle"].set_sensitive(not self.model.inherit_angle)
    
    def add_phase_view(self, index):
        def on_label_changed(editable):
            self.model.data_phases[index] = editable.get_text()
        
        def on_fraction_changed(editable):
            try: self.model.data_fractions[index] = float(editable.get_text())
            except ValueError: pass #ignore ValueErrors
        
        self.view.add_column(self.model.parent.data_phases, on_label_changed, on_fraction_changed, self.on_combo_changed, label=self.model.data_phases[index], fraction=self.model.data_fractions[index], phases=self.model.data_phase_matrix)
    
    def add_specimen_view(self, index):
        def on_scale_changed(editable):
            try: self.model.data_scales[index] = float(editable.get_text())
            except ValueError: pass #ignore ValueErrors

        def on_specimen_changed(combobox):
            itr = combobox.get_active_iter()
            specimen = self.model.parent.data_specimens.get_user_data(itr) if itr!=None else None
            self.model.data_specimens[index] = specimen
        
        self.view.add_row(self.model.parent.data_phases, self.model.parent.data_specimens, on_scale_changed, on_specimen_changed, self.on_combo_changed, scale=self.model.data_scales[index], specimen=self.model.data_specimens[index], phases=self.model.data_phase_matrix)
    
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------   
    @Controller.observe("has_changed", signal=True)
    def notif_has_changed(self, model, prop_name, info):
        if not self.chicken_egg:
            self.view.update_all(self.model.data_fractions, self.model.data_scales)
        
    @Controller.observe("needs_reset", signal=True)
    def notif_needs_reset(self, model, prop_name, info):
        self.create_ui()

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_combo_changed(self, combobox, row, col):
        itr = combobox.get_active_iter()
        phase = self.model.parent.data_phases.get_user_data(itr) if itr!=None else None
        self.model.data_phase_matrix[row, col] = phase
    
    def on_add_phase(self, widget, *args):
        self.chicken_egg = True
        index = self.model.add_phase("New Phase", 1.0)
        self.add_phase_view(index)
        self.chicken_egg = False
        
    def on_add_specimen(self, widget, *args):
        self.chicken_egg = True
        index = self.model.add_specimen(None, 1.0)
        self.add_specimen_view(index)
        self.chicken_egg = False
    
    def on_add_both(self, widget, *args):
        self.chicken_egg = True
        self.on_add_specimen(widget, *args)
        self.on_add_phase(widget, *args)
        self.chicken_egg = False
    
    def on_optimize_clicked(self, widget, *args):
        self.model.optimize()
        return
    
    def on_apply_result(self, widget, *args):
        self.model.apply_result()
        return True
    
    def on_refine_clicked(self, widget, *args):
        self.model.update_refinement_treestore()
        if self.ref_view!=None: 
            self.ref_view.hide()
        self.ref_view = RefinementView()
        self.ref_ctrl = RefinementController(self.model, self.ref_view)
        self.ref_view.present()
    
    pass #end of class

class MixturesController(ObjectListStoreController):

    model_property_name = "data_mixtures"
    columns = [ ("Mixture name", 0) ]
    delete_msg = "Deleting a mixture is irreverisble!\nAre You sure you want to continue?"

    def get_new_edit_view(self, obj):
        if isinstance(obj, Mixture):
            return EditMixtureView(parent=self.view)
        else:
            return ObjectListStoreController.get_new_edit_view(self, obj)
        
    def get_new_edit_controller(self, obj, view, parent=None):
        if isinstance(obj, Mixture):
            return EditMixtureController(obj, view, parent=parent)
        else:
            return ObjectListStoreController.get_new_edit_controller(self, obj, view, parent=parent)
    
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------        
    def on_load_object_clicked(self, event):
        pass #cannot load mixtures
    def on_save_object_clicked(self, event):
        pass #cannot save mixtures
        
    def create_new_object_proxy(self):
        return Mixture(parent=self.model)
