# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

from gtkmvc import Model, Controller
from gtkmvc.adapters import Adapter

import settings

from generic.views import ChildObjectListStoreView
from generic.views.treeview_tools import new_text_column, new_pb_column
from generic.views.combobox_tools import add_combo_text_column
from generic.controllers import DialogController, BaseController, ObjectListStoreController
from generic.controllers.utils import get_case_insensitive_glob
from generic.models.treemodels.utils import create_treestore_from_directory

from probabilities.models import get_Gbounds_for_R, get_Rbounds_for_G
from probabilities.controllers import EditProbabilitiesController
from probabilities.views import EditProbabilitiesView

from phases.controllers import EditCSDSTypeController, ComponentsController
from phases.views import EditPhaseView, AddPhaseView, EditCSDSDistributionView
from phases.models import Phase

class EditPhaseController(BaseController):
    """ 
        Controller for the phase edit view
    """
    probabilities_controller = None
    
    components_view = None
    components_controller = None
    
    widget_handlers = { 
        'custom': 'custom_handler',
        'combo': 'combo_handler'
    }

    def register_view(self, view):
        BaseController.register_view(self, view)

        self.csds_view = EditCSDSDistributionView(parent=self.view)
        self.view.set_csds_view(self.csds_view)
                
        if self.model.G > 1:
            self.probabilities_view = EditProbabilitiesView(parent=self.view)
            self.view.set_probabilities_view(self.probabilities_view)
        else:
            self.view.remove_probabilities()
        
        self.components_view = ChildObjectListStoreView(parent=self.view)
        self.components_view["button_add_object"].set_visible(False)
        self.components_view["button_add_object"].set_no_show_all(True)
        self.components_view["button_del_object"].set_visible(False)
        self.components_view["button_del_object"].set_no_show_all(True)
        self.view.set_components_view(self.components_view)

    @staticmethod
    def custom_handler(self, intel, prefix):
        if intel.name == "CSDS_distribution":
            self.csds_controller = EditCSDSTypeController(model=self.model, view=self.csds_view, parent=self)
        elif intel.name == "components":
            self.components_controller = ComponentsController(model=self.model, view=self.components_view, parent=self)
        elif intel.name == "probabilities":
            if self.model.G > 1:
                self.probabilities_controller = EditProbabilitiesController(model=self.model.probabilities, view=self.probabilities_view, parent=self)
        else: return False
        return True
        
    @staticmethod
    def combo_handler(self, intel, prefix):
        if intel.name == "based_on":
            combo = self.view["phase_based_on"]

            tv_model = self.parent.model.current_project.phases
            
            combo.set_model(tv_model)
            combo.connect('changed', self.on_based_on_changed)
            
            def phase_renderer(celllayout, cell, model, itr, user_data=None):
                phase = model.get_user_data(itr)
                if phase: # an error can occur here if the phase list is cleared and the view is still open
                    cell.set_sensitive(phase.R == self.model.R and phase.G == self.model.G and phase.get_based_on_root() != self.model)            
            add_combo_text_column(combo, data_func=phase_renderer, text_col=tv_model.c_name)
            
            for row in tv_model:
                if tv_model.get_user_data(row.iter) == self.model.based_on:
                    combo.set_active_iter (row.iter)
                    break
        else: return False
        return True

    def register_adapters(self):
        BaseController.register_adapters(self)
        self.update_sensitivities()

    def update_sensitivities(self):
        can_inherit = (self.model.based_on != None)
        
        for name in ("sigma_star", "display_color"):
            widget_name = "container_%s" % name
            self.view[widget_name].set_sensitive(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view[widget_name].set_visible(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view["phase_inherit_%s" % name].set_sensitive(can_inherit)

        for name in ("CSDS_distribution", "probabilities"):
            sensitive = not (can_inherit and getattr(self.model, "inherit_%s" % name))            
            #FIXME self.view["phase_%s" % name].set_sensitive(sensitive)
            self.view["phase_inherit_%s" % name].set_sensitive(can_inherit)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("inherit_display_color", assign=True)    
    @Controller.observe("inherit_sigma_star", assign=True)
    @Controller.observe("inherit_CSDS_distribution", assign=True)
    @Controller.observe("inherit_probabilities", assign=True)
    def notif_change_inherit(self, model, prop_name, info):
        self.update_sensitivities()
        return
    
    @Controller.observe("probabilities", assign=True)
    def notif_change_probabilities(self, model, prop_name, info):
        if hasattr(self, "probabilities_controller"):
            self.probabilities_controller.relieve_model(self.probabilities_controller.model)
            del self.probabilities_controller
        self.probabilities_controller = EditProbabilitiesController(model=self.model.probabilities, view=self.probabilities_view, parent=self)
        return
    
    @Controller.observe("name", assign=True)
    def notif_name_changed(self, model, prop_name, info):
        self.parent.model.current_project.phases.on_item_changed(self.model)
        return

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_based_on_changed(self, combo, user_data=None):
        itr = combo.get_active_iter()
        if itr != None:
            val = combo.get_model().get_user_data(itr)
            #cannot be based on itself == not based on anything
            #cannot be based on a model with a different # of components
            if val != self.model and val.get_based_on_root() != self.model and val.G == self.model.G: 
                self.model.based_on = val
                self.update_sensitivities()
                return
        combo.set_active(-1)
        self.update_sensitivities()
        self.model.based_on = None        

class PhasesController(ObjectListStoreController):
    """ 
        Controller for the phase ObjectListStore
    """
    file_filters = [("Phase file", get_case_insensitive_glob("*.PHS")),]
    model_property_name = "phases"
    multi_selection = True
    columns = [ 
        ("Phase name", "c_name"),
        (" ", "c_display_color"),
        ("R", "c_R"),
        ("#", "c_G"),
    ]
    delete_msg = "Deleting a phase is irreverisble!\nAre You sure you want to continue?"
    title="Edit Phases"

    def get_new_edit_view(self, obj):
        if isinstance(obj, Phase):
            return EditPhaseView(parent=self.view)
        else:
            return ObjectListStoreController.get_new_edit_view(self, obj)
        
    def get_new_edit_controller(self, obj, view, parent=None):
        if isinstance(obj, Phase):
            return EditPhaseController(model=obj, view=view, parent=parent)
        else:
            return ObjectListStoreController.get_new_edit_controller(self, obj, view, parent=parent)

    def load_phases(self, filename):
        print "Importing phase..."
        for phase in Phase.load_phases(filename, parent=self.model):
            self.add_object(phase)
            phase.resolve_json_references()
        self.select_object(phase)

    def setup_treeview_col_c_display_color(self, treeview, name, col_descr, col_index, tv_col_nr):
    
        def set_pb(column, cell_renderer, tree_model, iter, col_index):
            color = gtk.gdk.color_parse(tree_model.get_value(iter, col_index))
            color = (int(color.red_float*255) << 24) + (int(color.green_float*255) << 16) + (int(color.blue_float*255) << 8) + 255            
            phase = tree_model.get_user_data(iter)
            pb, old_color = getattr(phase, "__col_c_pb", (None, None))
            if old_color != color:
                pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 10, 20)
                pb.fill(color)
                setattr(phase, "__col_c_pb", (color, pb))
            cell_renderer.set_property('pixbuf', pb)
    
        treeview.append_column(new_pb_column(
            name,
            data_func=(set_pb, (col_index,)),
            resizable=False,
            expand=False))
            
        return True

    def create_new_object_proxy(self):
        def on_accept(phase, G, R):
            if not phase:
                G = int(G)
                R = int(R)
                if G != None and G > 0 and R != None and R >= 0 and R <= 4:
                    self.add_object(Phase("New Phase",  G=G, R=R, parent=self.model))
                    self.select_object(phase)
            else:
                self.load_phases(phase)
                
        add_model = Model()
        add_view = AddPhaseView(parent=self.view)
        add_ctrl = AddPhaseController(add_model, add_view, parent=self.parent, callback=on_accept)
        
        add_view.present()
        return None

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_save_object_clicked(self, event):
        def on_accept(dialog):
            print "Exporting phases..."
            filename = self.extract_filename(dialog)
            Phase.save_phases(self.get_selected_objects(), filename=filename)
        self.run_save_dialog("Export phase", on_accept, parent=self.view.get_top_widget())
        return True
        
        
    def on_load_object_clicked(self, event):
        def on_accept(dialog):
            self.load_phases(dialog.get_filename())
        self.run_load_dialog("Import phase", on_accept, parent=self.view.get_top_widget())
        return True
        
class AddPhaseController(DialogController):
    """ 
        Controller for the add phase dialog
    """
    def __init__(self, model, view, spurious=False, auto_adapt=False, parent=None, callback=None):
        DialogController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt)    
        self.callback = callback
    
    def register_view(self, view):
        self.update_bounds()
        self.generate_combo()

    def register_adapters(self):
        pass #has no intel, or a model!

    def update_R_bounds(self):
        if self.view != None:
            min_R, max_R, R = get_Rbounds_for_G(self.view.get_G(), self.view.get_R())
            self.view["adj_R"].set_upper(max_R)
            self.view["adj_R"].set_lower(min_R)
            self.view["R"].set_value(R)
            
    def update_G_bounds(self):
        if self.view != None:
            min_G, max_G, G = get_Gbounds_for_R(self.view.get_R(), self.view.get_G())
            self.view["adj_G"].set_upper(max_G)
            self.view["adj_G"].set_lower(min_G)
            self.view["G"].set_value(G)
            
    def update_bounds(self):
        self.update_G_bounds()
        self.update_R_bounds()
        
    def generate_combo(self):        
        cmb_model = create_treestore_from_directory(settings.DATA_REG.get_directory_path("DEFAULT_PHASES"), ".phs")        
        self.view.phase_combo_box.set_model(cmb_model)
        add_combo_text_column(self.view.phase_combo_box, text_col=0, sensitive_col=2)
    
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.view.hide()
        self.callback(self.view.get_phase(), self.view.get_G(), self.view.get_R())
        return True
        
    def on_r_value_changed(self, *args):
        self.update_G_bounds()
        return True
        
    def on_g_value_changed(self, *args):
        self.update_R_bounds()
        return True
        
    def on_keypress(self, widget, event):
		if event.keyval == gtk.keysyms.Escape:
			self.view.hide()
			return True
		if event.keyval == gtk.keysyms.Return:
			self.view.hide()
            self.callback(self.view.get_phase(), self.view.get_G(), self.view.get_R())
			return True
        
    def on_window_edit_dialog_delete_event(self, event, args=None):
        self.view.hide()
        return True #do not propagate
        
    pass #end of class
