# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import locale

import gtk

from gtkmvc import Model, Controller
from gtkmvc.adapters import Adapter

from generic.validators import FloatEntryValidator 
from generic.views import ChildObjectListStoreView
from generic.controllers import DialogController, ChildController, ObjectListStoreController, ChildObjectListStoreController, HasObjectTreeview

from atoms.models import Atom

from probabilities.controllers import EditProbabilitiesController
from probabilities.views import EditProbabilitiesView

from phases.views import EditPhaseView, EditLayerView, EditComponentView, AddPhaseView
from phases.models import Phase, Component


class EditLayerController(ChildController, HasObjectTreeview):
    file_filters = ("Layer file", "*.lyr"),
    treeview = None
    new_atom_type = None
    
    model_property_name = ""
    @property
    def liststore(self):
        return getattr(self.model, self.model_property_name)

    def _setup_atom_treeview(self, tv, model):
        tv.set_model(None)
        tv.set_model(model)
        tv.connect ('cursor-changed', self.on_tvatoms_cursor_changed, model)

        #reset:
        for col in tv.get_columns():
            tv.remove_column(col)

        def float_renderer(column, cell, model, itr, col=None):
            nr = model.get_value(itr, col)
            if nr is not None:
                cell.set_property('text', "%.5f" % nr)
            else:
                cell.set_property('text', '#NA#')

        def add_text_col(title, colnr, renderer=None):
            rend = gtk.CellRendererText()
            rend.set_property("editable", True)
            rend.connect('edited', self.on_atom_cell_edited, (model, colnr))
            col = gtk.TreeViewColumn(title, rend, text=colnr)
            col.set_resizable(False)
            col.set_expand(True)
            if renderer is not None:
                col.set_cell_data_func(rend, renderer, colnr)
            tv.append_column(col)
        add_text_col('Atom name', model.c_data_name)
        add_text_col('Z (Å)', model.c_data_z, float_renderer)
        add_text_col('#', model.c_data_pn, float_renderer)

        def atom_type_renderer(column, cell, model, itr, col=None):
            try:            
                name = model.get_user_data_from_path(model.get_path(itr)).data_atom_type.data_name
            except:
                name = '#NA#'
            cell.set_property('text', name)
            return
        rend = gtk.CellRendererCombo()
        atom_type_model = self.model.parent.parent.data_atom_types
        rend.set_property("model", atom_type_model)
        rend.set_property("text_column", atom_type_model.c_data_name)
        rend.set_property("editable", True)
        rend.set_property("has-entry", True)
        
        def adjust_combo(self, cell, editable, path, data=None):
            cell.set_wrap_width(10)

        rend.connect('changed', self.on_atom_type_changed, None)
        rend.connect('edited', self.on_atom_type_edited, model)
        col = gtk.TreeViewColumn('Element', rend)
        col.set_resizable(True)
        col.set_expand(True)
        col.set_cell_data_func(rend, atom_type_renderer, 3)
        tv.append_column(col)
        rend.connect('editing-started', adjust_combo, None)

    def __init__(self, model_property_name, *args, **kwargs):
        ChildController.__init__(self, *args, **kwargs)
        self.new_atom_type = None
        self.model_property_name = model_property_name

    def register_adapters(self):
        if self.liststore is not None:
            self.treeview = self.view['tvw_atoms']
            self._setup_atom_treeview(self.treeview, self.liststore)
        self.update_sensitivities()
        return

    def update_sensitivities(self):
        sensitive = (self.treeview.get_cursor() != (None, None))
        self.view["btn_del_atom"].set_sensitive(sensitive)
        sensitive = bool(self.liststore is not None and len(self.liststore._model_data)>0)
        self.view["btn_export_layer"].set_sensitive(sensitive)

    def get_selected_object(self):
        return HasObjectTreeview.get_selected_object(self, self.treeview)
        
    def get_selected_objects(self):
        return HasObjectTreeview.get_selected_objects(self, self.treeview)
        
    def get_all_objects(self):
        return HasObjectTreeview.get_all_objects(self, self.treeview)
        
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_tvatoms_cursor_changed(self, widget, model):
        self.update_sensitivities()

    def on_add_atom(self, widget, user_data=None):
        self.liststore.append(Atom("New Atom", parent = self.model.parent.parent))
        self.update_sensitivities()

    def on_del_atom(self, widget, user_data=None):
        path, col = self.treeview.get_cursor()
        if path != None:
            itr = self.liststore.get_iter(path)
            self.liststore.remove(itr)
            self.update_sensitivities()
            return True
        return False

    def on_export_layer(self, widget, user_data=None):
        def on_accept(save_dialog):
            fltr = save_dialog.get_filter()
            filename = save_dialog.get_filename()
            if fltr.get_name() == self.file_filters[0][0]:
                if filename[len(filename)-4:] != self.file_filters[0][1][1:]:
                    filename = "%s%s" % (filename, self.file_filters[0][1][1:])
                Atom.save_as_csv(filename, self.get_all_objects())
        self.run_save_dialog("Export atoms", on_accept, parent=self.view.get_toplevel(), suggest_name="%s%s" % (self.model.data_name.lower(), self.model_property_name.replace("data", "").lower()) )
        
    def on_import_layer(self, widget, user_data=None):        
        def import_layer(dialog):
            def on_accept(open_dialog):
                fltr = open_dialog.get_filter()
                if fltr.get_name() == self.file_filters[0][0]:
                    self.liststore.clear()
                    Atom.get_from_csv(open_dialog.get_filename(), self.liststore.append, self.model.parent.parent)
            self.run_load_dialog("Import atoms", on_accept, parent=self.view.get_toplevel())            
        self.run_confirmation_dialog(message="Are you sure?\nImporting a layer file will clear the current list of atoms!", on_accept_callback=import_layer, parent=self.view.get_toplevel())
        

    def on_atom_cell_edited(self, cell, path, new_text, user_data):
        model, col = user_data
        model.set_value(model.get_iter(path), col, model.convert(col, new_text))
        pass

    def on_atom_type_changed(self, combo, path, new_iter, user_data=None):
        self.new_atom_type = self.model.parent.parent.data_atom_types.get_user_data(new_iter)
        return True

    def on_atom_type_edited(self, combo, path, new_text, atom_model):
        atom = atom_model.get_user_data_from_path((int(path),))
        if self.new_atom_type == None and not new_text in (None, "" ):
            try:
                self.new_atom_type = self.model.parent.parent.data_atom_types.get_item_by_index(new_text)
            except:
                pass
        
        if atom is not None:
            atom.data_atom_type = self.new_atom_type
            self.new_atom_type = None
            return True
        return False

class EditComponentController(ChildController, HasObjectTreeview):

    layer_view = None
    layer_controller = None
    
    interlayer_view = None
    interlayer_controller = None

    def __init__(self, *args, **kwargs):
        ChildController.__init__(self, *args, **kwargs)
        
        self.layer_view = EditLayerView(parent=self.view)
        self.layer_controller = EditLayerController("data_layer_atoms", model=self.model, view=self.layer_view, parent=self)
        
        self.interlayer_view = EditLayerView(parent=self.view)
        self.interlayer_controller = EditLayerController("data_interlayer_atoms", model=self.model, view=self.interlayer_view, parent=self)

    def reset_combo_box(self):
        if self.model is not None and self.model.parent is not None:
            combo = self.view["component_data_linked_with"]
            combo.clear()
            if self.model.parent.data_based_on is not None:
                tv_model = self.model.parent.data_based_on.data_components
                combo.set_model(tv_model)
                cell = gtk.CellRendererText()
                combo.pack_start(cell, True)
                combo.add_attribute(cell, 'text', tv_model.c_data_name)
                for row in tv_model:
                    if tv_model.get_user_data(row.iter) == self.model.data_linked_with:
                        print "Found linked with: %s" % row
                        combo.set_active_iter (row.iter)
                        break
            else:
                combo.set_model(None)
                
    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "data_name":
                    self.adapt(name, "component_data_name")
                elif name == "data_linked_with":
                    self.reset_combo_box()
                elif name.find("inherit") is not -1:
                    print name
                    self.adapt(name)
                elif name in ("data_layer_atoms", "data_interlayer_atoms"):
                    self.view.set_layer_view(self.layer_view.get_top_widget())
                    self.view.set_interlayer_view(self.interlayer_view.get_top_widget())
                    pass
                elif not name in ("data_all_atoms", "parent", "added", "removed", "needs_update"):
                    FloatEntryValidator(self.view["component_%s" % name])
                    self.adapt(name)
            self.update_sensitivities()
            return

    def update_sensitivities(self):
        can_inherit = (self.model.data_linked_with != None)
        
        for name in ("d001", "cell_a", "cell_b"):
            widget_name = "component_data_%s" % name
            self.view[widget_name].set_sensitive(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view["component_inherit_%s" % name].set_sensitive(can_inherit)
        for name in ("interlayer_atoms",
                     "layer_atoms"):
            widget_name = "%s_container" % name
            self.view[widget_name].set_sensitive(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view["component_inherit_%s" % name].set_sensitive(can_inherit)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("inherit_layer_atoms", assign=True)
    @Controller.observe("inherit_interlayer_atoms", assign=True)
    @Controller.observe("inherit_cell_a", assign=True)
    @Controller.observe("inherit_cell_b", assign=True)
    @Controller.observe("inherit_d001", assign=True)
    def notif_change_data_inherit(self, model, prop_name, info):
        can_inherit = (self.model.data_linked_with != None)
        if not (prop_name in ("inherit_layer_atoms", "inherit_interlayer_atoms")):
            widget_name = prop_name.replace("inherit_", "component_data_")
        else:
            widget_name = "%s_container" % prop_name.replace("inherit_", "")
        self.view[widget_name].set_sensitive(can_inherit and not info.new)
        return
    
    @Controller.observe("data_name", assign=True)
    def notif_name_changed(self, model, prop_name, info):
        self.model.parent.data_components.on_item_changed(self.model)
        return

    @Controller.observe("data_linked_with", assign=True)
    def notif_linked_with_changed(self, model, prop_name, info):
        self.reset_combo_box()
        return


    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_linked_with_changed(self, combo, user_data=None):
        itr = combo.get_active_iter()
        if itr != None:
            val = combo.get_model().get_user_data(itr)
            self.model.data_linked_with = val
            self.update_sensitivities()
            return
        combo.set_active(-1)
        self.update_sensitivities()
        self.model.data_linked_with = None

class ComponentsController(ChildObjectListStoreController): #limit # of components!

    model_property_name = "data_components"
    columns = [ ("Component name", 0) ]
    delete_msg = "Deleting a component is irreverisble!\nAre You sure you want to continue?"

    def get_new_edit_view(self, obj):
        if isinstance(obj, Component):
            return EditComponentView(parent=self.view)
        else:
            return ChildObjectListStoreController.get_new_edit_view(self, obj)
        
    def get_new_edit_controller(self, obj, view, parent=None):
        if isinstance(obj, Component):
            return EditComponentController(model=obj, view=view, parent=parent)
        else:
            return ChildObjectListStoreController.get_new_edit_controller(self, obj, view, parent=parent)

class EditPhaseController(ChildController):
    
    probabilities_controller = None
    
    components_view = None
    components_controller = None

    def __init__(self, *args, **kwargs):
        ChildController.__init__(self, *args, **kwargs)

        self.probabilities_view = EditProbabilitiesView(parent=self.view)
        self.probabilities_controller = EditProbabilitiesController(model=self.model.data_probabilities, view=self.probabilities_view, parent=self)
        
        self.components_view = ChildObjectListStoreView(display_buttons=False, parent=self.view)
        self.components_controller = ComponentsController(model=self.model, view=self.components_view, parent=self)

    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name in ["data_all_atoms", "parent", "added", "removed", "needs_update"]:
                    pass
                elif name == "data_name":
                    self.adapt(name, "phase_data_name")
                elif name == "data_based_on":
                    combo = self.view["phase_data_based_on"]

                    tv_model = self.cparent.model.current_project.data_phases
                    
                    combo.set_model(tv_model)
                    combo.connect('changed', self.on_based_on_changed)

                    cell = gtk.CellRendererText()
                    combo.pack_start(cell, True)
                    combo.add_attribute(cell, 'text', tv_model.c_data_name)

                    for row in tv_model:
                        if tv_model.get_user_data(row.iter) == self.model.data_based_on:
                            combo.set_active_iter (row.iter)
                            break
                elif name in ("data_probabilities", "data_components"):
                    self.view.set_probabilities_view(self.probabilities_view)
                    self.view.set_components_view(self.components_view)
                elif name.find("inherit") is not -1 or name == "data_numcomp":
                    self.adapt(name)
                else:
                    FloatEntryValidator(self.view["phase_%s" % name])
                    self.adapt(name)
            self.update_sensitivities()
            return

    def update_sensitivities(self):
        can_inherit = (self.model.data_based_on != None)
        
        for name in ("min_CSDS", "max_CSDS", "mean_CSDS", "sigma_star"):
            widget_name = "phase_data_%s" % name
            self.view[widget_name].set_sensitive(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view["phase_inherit_%s" % name].set_sensitive(can_inherit)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("inherit_sigma_star", assign=True)
    @Controller.observe("inherit_min_CSDS", assign=True)    
    @Controller.observe("inherit_max_CSDS", assign=True)    
    @Controller.observe("inherit_mean_CSDS", assign=True)
    def notif_change_data_inherit(self, model, prop_name, info):
        can_inherit = (self.model.data_based_on != None)
        widget_name = prop_name.replace("inherit_", "phase_data_")
        self.view[widget_name].set_sensitive(can_inherit and not info.new)
        return
    
    @Controller.observe("data_name", assign=True)
    def notif_name_changed(self, model, prop_name, info):
        self.cparent.model.current_project.data_phases.on_item_changed(self.model)
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
            if val != self.model and val.get_based_on_root() != self.model and val.data_G == self.model.data_G: 
                self.model.data_based_on = val
                self.update_sensitivities()
                return
        combo.set_active(-1)
        self.update_sensitivities()
        self.model.data_based_on = None        

class PhasesController(ObjectListStoreController):
    file_filters = ("Phase file", "*.phs"),
    model_property_name = "data_phases"
    multi_selection = False
    columns = [ ("Phase name", 0) ]
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

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_add_object_clicked(self, event):
        def on_accept(G, R):
            G = int(G)
            R = int(R)
            if G != None and G > 0 and R != None and R >= 0 and R <= 4:
                new_phase = Phase("New Phase",  data_G=G, data_R=R, parent=self.model)
                self.model.data_phases.append(new_phase)
                self.select_object(new_phase)
                
        add_model = Model()
        add_view = AddPhaseView(parent=self.view)
        add_ctrl = AddPhaseController(add_model, add_view, parent=self.parent, callback=on_accept)
        
        add_view.present()

        return True
        
    def on_save_object_clicked(self, event):
        def on_accept(dialog):
            print "Exporting phase..."
            filename = self.extract_filename(dialog)
            phase = self.get_selected_object()
            if phase is not None:
                phase.save_object(filename=filename)
        self.run_save_dialog("Export phase", on_accept, parent=self.view.get_top_widget())
        return True
        
        
    def on_load_object_clicked(self, event):
        def on_accept(dialog):
            print "Importing phase..."
            new_phase = Phase.load_object(dialog.get_filename(), parent=self.model)
            #new_phase.parent = self.model
            new_phase.resolve_json_references()
            self.model.data_phases.append(new_phase)
        self.run_load_dialog("Import phase", on_accept, parent=self.view.get_top_widget())
        return True
        
class AddPhaseController(DialogController):
    
    def __init__(self, model, view, spurious=False, auto_adapt=False, parent=None, callback=None):
        DialogController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt)    
        self.callback = callback
    
    def on_btn_ok_clicked(self, event):
        self.view.hide()
        self.callback(self.view.get_G(), self.view.get_R())
        return True
        
    def on_keypress(self, widget, event) :
		if event.keyval == gtk.keysyms.Escape :
			self.view.hide()
			return True
        
    def on_window_edit_dialog_delete_event(self, event, args=None):
        self.view.hide()
        return True #do not propagate
