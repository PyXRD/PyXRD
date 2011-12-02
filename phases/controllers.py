# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import locale

import gtk

from gtkmvc import Controller
from gtkmvc.adapters import Adapter

from generic.validators import FloatEntryValidator 
from generic.controllers import ChildController, ObjectListStoreController, HasObjectTreeview

from phases.views import EditPhaseView, EditLayerView
from phases.models import Phase
from atoms.models import Atom

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
            col.set_resizable(True)
            col.set_expand(True)
            if renderer is not None:
                col.set_cell_data_func(rend, renderer, colnr)
            tv.append_column(col)
        add_text_col('Atom name', model.c_data_name)
        add_text_col('Z', model.c_data_z, float_renderer)
        add_text_col('#', model.c_data_pn, float_renderer)

        def atom_type_renderer(column, cell, model, itr, col=None):
            try:            
                name = model.get_user_data_from_path(model.get_path(itr)).data_atom_type.data_name
            except:
                name = '#NA#'
            cell.set_property('text', name)
            return
        rend = gtk.CellRendererCombo()
        rend.set_property("model", self.cparent.cparent.model.current_project.data_atom_types)
        rend.set_property("text_column", 0)
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
        self.model_property_name = model_property_name

    def register_adapters(self):
        if self.liststore is not None:
            self.treeview = self.view['tvw_phase_atoms']
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
        self.liststore.append(Atom("New Atom", parent = self.model.parent))
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
                    Atom.get_from_csv(open_dialog.get_filename(), self.liststore.append, self.cparent.cparent.model.current_project)        
            self.run_load_dialog("Import atoms", on_accept, parent=self.view.get_toplevel())            
        self.run_confirmation_dialog(message="Are you sure?\nImporting a layer file will clear the current list of atoms!", on_accept_callback=import_layer, parent=self.view.get_toplevel())
        

    def on_atom_cell_edited(self, cell, path, new_text, user_data):
        model, col = user_data
        model.set_value(model.get_iter(path), col, model.convert(col, new_text))
        pass

    def on_atom_type_changed(self, combo, path, new_iter, user_data=None):
        self.new_atom_type = self.cparent.cparent.model.current_project.data_atom_types.get_user_data(new_iter)
        return True

    def on_atom_type_edited(self, combo, path, new_text, atom_model):
        atom = atom_model.get_user_data_from_path((int(path),))
        if atom is not None:
            atom.data_atom_type = self.new_atom_type
            self.new_atom_type = None
            return True
        return False

class EditPhaseController(ChildController):
    
    layer_view = None
    layer_controller = None
    
    interlayer_view = None
    interlayer_controller = None

    def __init__(self, *args, **kwargs):
        ChildController.__init__(self, *args, **kwargs)
        self.new_atom_type = None
        
        self.layer_view = EditLayerView(parent=self.view)
        self.layer_controller = EditLayerController("data_layer_atoms", self.model, self.layer_view, parent=self)

        self.interlayer_view = EditLayerView(parent=self.view)
        self.interlayer_controller = EditLayerController("data_interlayer_atoms",self.model, self.interlayer_view, parent=self)

    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "data_all_atoms":
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
                elif name in ("data_layer_atoms", "data_interlayer_atoms"):
                    self.view.set_layer_view(self.layer_view)
                    self.view.set_interlayer_view(self.interlayer_view)
                elif name.find("inherit") is not -1:
                    self.adapt(name)
                else:
                    FloatEntryValidator(self.view["phase_%s" % name])
                    self.adapt(name)
            self.update_sensitivities()
            return

    def update_sensitivities(self):
        can_inherit = (self.model.data_based_on != None)
        for name in ("d001",
                     "mean_CSDS",
                     "sigma_star",
                     "proportion"):
            widget_name = "phase_data_%s" % name
            self.view[widget_name].set_sensitive(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view["phase_inherit_%s" % name].set_sensitive(can_inherit)
        for name in ("interlayer_atoms",
                     "layer_atoms"):
            widget_name = "%s_container" % name
            self.view[widget_name].set_sensitive(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view["phase_inherit_%s" % name].set_sensitive(can_inherit)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("inherit_layer_atoms", assign=True)
    @Controller.observe("inherit_interlayer_atoms", assign=True)
    @Controller.observe("inherit_sigma_star", assign=True)
    @Controller.observe("inherit_mean_CSDS", assign=True)
    @Controller.observe("inherit_d001", assign=True)
    @Controller.observe("inherit_proportion", assign=True)
    def notif_change_data_inherit(self, model, prop_name, info):
        can_inherit = (self.model.data_based_on != None)
        if not (prop_name in ("inherit_layer_atoms", "inherit_interlayer_atoms")):
            widget_name = prop_name.replace("inherit_", "phase_data_")
        else:
            widget_name = "%s_container" % prop_name.replace("inherit_", "")
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
            if val.get_based_on_root() != self.model: #cannot be based on itself == not based on anything
                self.model.data_based_on = val
                self.update_sensitivities()
                return
        combo.set_active(-1)
        self.update_sensitivities()
        self.model.data_based_on = None

    def on_button_save_phase_clicked(self, widget, user_data=None):
        print "TODO SAVE PHASE"
        pass

    def on_button_load_phase_clicked(self, widget, user_data=None):
        print "TODO LOAD PHASE"
        pass
        

class PhasesController(ObjectListStoreController):

    model_property_name = "data_phases"
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
        new_phase = Phase("New Phase", parent=self.model)
        self.model.add_phase(new_phase)
        self.select_object(new_phase)
        return True
