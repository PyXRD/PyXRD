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

from generic.views.treeview_tools import new_text_column, new_pb_column, new_toggle_column
from generic.mathtext_support import create_pb_from_mathtext
from generic.controllers import DialogController, BaseController, ObjectListStoreController, ctrl_setup_combo_with_list
from generic.views.validators import FloatEntryValidator #FIXME use handlers!
from generic.utils import get_case_insensitive_glob

from phases.models import Phase, Component

from mixture.models import Mixture
from mixture.views import EditMixtureView, RefinementView #, BusyView

class RefinementController(DialogController):

    def register_adapters(self):
        if self.model is not None:  
            tv_model = self.model.refinables
            tv = self.view['tv_param_selection']
            tv.set_show_expanders(True)
            tv.set_model(tv_model)
                          
            #Labels are parsed for mathtext markup into pb's:                   
            def get_pb(column, cell, model, itr, user_data=None):
                ref_prop = model.get_user_data(itr)
                if not hasattr(ref_prop, "pb") or not ref_prop.pb:
                    ref_prop.pb = create_pb_from_mathtext(
                        ref_prop.title,
                        align='left', 
                        weight='medium'
                    )
                cell.set_property("pixbuf", ref_prop.pb)
                return       
            tv.append_column(new_pb_column('Name/Prop', xalign=0.0, data_func=get_pb))

            #Editable floats:
            def get_value(column, cell, model, itr, *args):
                value = model.get_value(itr, column.get_col_attr('markup'))
                try: value = "%.5f" % value
                except TypeError: value = ""
                cell.set_property("markup",  value)                    
                return
            def on_float_edited(rend, path, new_text, col):
                itr = tv_model.get_iter(path)
                tv_model.set_value(itr, col, float(new_text))
                return True
                
            def_float_args = {
                "sensitive_col": tv_model.c_refinable,
                "editable_col": tv_model.c_refinable,
                "visible_col": tv_model.c_refinable,
                "data_func": get_value
            }
                
            tv.append_column(new_text_column("Value", markup_col=tv_model.c_value,
                    edited_callback=(on_float_edited, (tv_model.c_value,)), 
                    **def_float_args))
            tv.append_column(new_text_column("Min", markup_col=tv_model.c_value_min,
                    edited_callback=(on_float_edited, (tv_model.c_value_min,)), 
                    **def_float_args))
            tv.append_column(new_text_column("Max", markup_col=tv_model.c_value_max,
                    edited_callback=(on_float_edited, (tv_model.c_value_max,)), 
                    **def_float_args))
            
            #The 'refine' checkbox:
            tv.append_column(new_toggle_column("Refine",
                    toggled_callback=(self.refine_toggled, (tv_model,)),
                    resizable=False,
                    expand=False,
                    active_col=tv_model.c_refine,
                    sensitive_col=tv_model.c_refinable,
                    activatable_col=tv_model.c_refinable,
                    visible_col=tv_model.c_refinable))
                       
            #Refine method combobox:
            for name in self.model.get_properties():
                if name == "refine_method":
                    ctrl_setup_combo_with_list(self, 
                        self.view["cmb_data_refine_method"],
                        "refine_method", "_refine_methods")
        return

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------

            
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_cancel(self):
        if not self.model.refine_lock:
            self.view.hide()
        else:
            return True #do nothing
    
    def refine_toggled(self, cell, path, model):
        if model is not None:
            itr = model.get_iter(path)
            model.set_value(itr, model.c_refine, not cell.get_active())
        return True
        
    def on_auto_restrict_clicked(self, event):
        self.model.auto_restrict()
        
    @DialogController.status_message("Refining mixture...", "refine_mixture")
    def on_refine_clicked(self, event):
        self.view.show_refinement_info(
            self.model.refine, self.update_last_rp, 
            self.on_complete, self.model.current_rp)
        
    def on_complete(self, data):
        x0, initialR2, lastx, lastR2, apply_solution = data
        def on_accept(dialog):
            apply_solution(lastx)
        def on_reject(dialog):
            apply_solution(x0)
        self.run_confirmation_dialog(
            "Do you want to keep the found solution?\n" + \
            "Initial Rp: %.2f\nFinal Rp: %.2f\n" % (initialR2, lastR2),
            on_accept, on_reject, parent=self.view.get_toplevel())
        
    def update_last_rp(self):
        self.view.update_refinement_info(self.model.last_refine_rp)
        
    pass #end of class
        
class EditMixtureController(BaseController):

    chicken_egg = False
    ref_view = None

    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "name":
                    self.adapt(name, "mixture_name")
                elif not name in self.model.__have_no_widget__+  ["refinables", "refine_method"]:
                    self.adapt(name)
            self.create_ui()
            return
            
    def create_ui(self):
        self.view.reset_view()
        for index, phase in enumerate(self.model.phases):
            self.add_phase_view(index)
        for index, specimen in enumerate(self.model.specimens):
            self.add_specimen_view(index)
               
    def add_phase_view(self, index):
        def on_label_changed(editable):
            self.model.phases[index] = editable.get_text()
        
        def on_fraction_changed(editable):
            try: self.model.fractions[index] = float(editable.get_text())
            except ValueError: pass #ignore ValueErrors
        
        def on_phase_delete(widget):
            self.model._del_phase_by_index(index)
            widget.disconnect(widget.get_data("deleventid"))
        
        self.view.add_phase(self.model.parent.phases, 
            on_phase_delete, on_label_changed, on_fraction_changed, 
            self.on_combo_changed, label=self.model.phases[index], 
            fraction=self.model.fractions[index], phases=self.model.phase_matrix)
    
    def add_specimen_view(self, index):
        def on_scale_changed(editable):
            try: self.model.scales[index] = float(editable.get_text())
            except ValueError: pass #ignore ValueErrors

        def on_bgs_changed(editable):
            try: self.model.bgshifts[index] = float(editable.get_text())
            except ValueError: pass #ignore ValueErrors

        def on_specimen_changed(combobox):
            itr = combobox.get_active_iter()
            specimen = self.model.parent.specimens.get_user_data(itr) if itr!=None else None
            self.model.specimens[index] = specimen
        
        def on_specimen_delete(widget):
            self.model._del_specimen_by_index(index)
            widget.disconnect(widget.get_data("deleventid"))
        
        self.view.add_specimen(self.model.parent.phases, 
            self.model.parent.specimens, on_specimen_delete, on_scale_changed,
            on_bgs_changed, on_specimen_changed, self.on_combo_changed, 
            scale=self.model.scales[index], bgs=self.model.bgshifts[index],
            specimen=self.model.specimens[index], phases=self.model.phase_matrix)
    
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------   
    @Controller.observe("has_changed", signal=True)
    def notif_has_changed(self, model, prop_name, info):
        if not self.chicken_egg:
            self.view.update_all(self.model.fractions, self.model.scales, self.model.bgshifts)
        
    @Controller.observe("needs_reset", signal=True)
    def notif_needs_reset(self, model, prop_name, info):
        self.create_ui()

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_combo_changed(self, combobox, row, col):
        itr = combobox.get_active_iter()
        phase = self.model.parent.phases.get_user_data(itr) if itr!=None else None
        print "COMBO %d, %d CHANGED %s" % (row, col, phase)
        self.model.phase_matrix[row, col] = phase
    
    def on_add_phase(self, widget, *args):
        self.chicken_egg = True
        index = self.model.add_phase("New Phase", 1.0)
        if index != -1:
            self.add_phase_view(index)
        self.chicken_egg = False
        
    def on_add_specimen(self, widget, *args):
        self.chicken_egg = True
        index = self.model.add_specimen(None, 1.0, 0.0)
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
        else:
            self.ref_view = RefinementView(parent=self.parent.view)
            self.ref_ctrl = RefinementController(self.model, self.ref_view, parent=self)
        self.ref_view.present()        
    
    def on_composition_clicked(self, widget, *args):
        comp  = "The composition of the specimens in this mixture:\n\n\n"
        comp += "<span font-family=\"monospace\">"
        #get the composition matrix (first columns contains strings with elements, others are specimen compositions)
        import re
        for row in self.model.get_composition_matrix():
            
            
            comp += "%s %s\n" % (re.sub(r'(\d+)', r'<sub>\1</sub>', row[0]), " ".join(row[1:]))
        comp += "</span>"
        self.run_information_dialog(comp, parent=self.view.get_toplevel())
    
    pass #end of class

class MixturesController(ObjectListStoreController):

    model_property_name = "mixtures"
    columns = [ ("Mixture name", "c_name") ]
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
        
    pass #end of class
