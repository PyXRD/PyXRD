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

import settings

from generic.validators import FloatEntryValidator 
from generic.views import ChildObjectListStoreView
from generic.controllers import DialogController, ChildController, ObjectListStoreController, ChildObjectListStoreController, InlineObjectListStoreController

from atoms.models import Atom

from probabilities.models import get_Gbounds_for_R, get_Rbounds_for_G
from probabilities.controllers import EditProbabilitiesController
from probabilities.views import EditProbabilitiesView

from phases.views import EditPhaseView, InlineObjectListStoreView, EditComponentView, AddPhaseView, EditUnitCellPropertyView
from phases.models import Phase, Component, ComponentRatioFunction

class EditUnitCellPropertyController(ChildController):

    def reset_prop_store(self):
        name = "data_prop"
        combo = self.view["data_prop"]
        store = gtk.ListStore(str, object)        
        for i, atom in enumerate(self.model.parent.data_layer_atoms._model_data):
            store.append(["data_layer_atoms.%d" % i, atom])
        for i, atom in enumerate(self.model.parent.data_interlayer_atoms._model_data):
            store.append(["data_interlayer_atoms.%d" % i, atom])
        for prop in self.extra_props:
            store.append(prop)
        combo.set_model(store)

        for row in store:
            if store.get_value(row.iter, 0) == str(getattr(self.model, name)):
                combo.set_active_iter(row.iter)
                break
        return store

    def __init__(self, extra_props, **kwargs):
        ChildController.__init__(self, **kwargs)
        self.extra_props = extra_props

    def register_adapters(self):
        if self.model is not None:
            for name in self.model.get_properties():
                if name == "data_prop":
                    combo = self.view["data_prop"]
                    store = self.reset_prop_store()
                    
                    def on_changed(combo, user_data=None):
                        itr = combo.get_active_iter()
                        if itr != None:
                            val = combo.get_model().get_value(itr, 0)
                            setattr(self.model, "data_prop", val)
                    combo.connect('changed', on_changed)
                    
                    cell = gtk.CellRendererText()
                    combo.pack_start(cell, True)
                    def get_name(celllayout, cell, model, itr, data=None):
                        obj = model.get_value(itr, 1)
                        if hasattr(obj, "data_name"):
                            cell.set_property("markup", obj.data_name)
                        else:
                            cell.set_property("markup", obj)
                    combo.set_cell_data_func(cell, get_name, None)
                    
                    def on_item_changed(*args):
                        self.reset_prop_store()
                    
                    self.model.parent._data_layer_atoms.connect("item-removed", on_item_changed)
                    self.model.parent._data_interlayer_atoms.connect("item-removed", on_item_changed)
                    self.model.parent._data_layer_atoms.connect("item-inserted", on_item_changed)
                    self.model.parent._data_interlayer_atoms.connect("item-inserted", on_item_changed)
                    
                elif name == "data_enabled":
                    self.adapt(name, "opt_enabled")
                    self.view["opt_disabled"].set_active(not self.model.data_enabled)
                    self.view["opt_enabled"].set_active(self.model.data_enabled)
                elif not name in ("data_name", "parent", "added", "removed"):
                    FloatEntryValidator(self.view[name])
                    self.adapt(name)
            self.update_sensitivities()
            return

    def update_sensitivities(self):
        if self.model.data_enabled:
            self.view['value'].set_sensitive(False)
            self.view['box_enabled'].set_sensitive(True)
        else:        
            self.view['value'].set_sensitive(True)
            self.view['box_enabled'].set_sensitive(False)        
       
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("data_enabled", assign=True)
    def notif_enabled_changed(self, model, prop_name, info):
        self.update_sensitivities()
        return
        
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_opt_enabled_group_changed(self, widget, *args):
        self.update_sensitivities()
    
    pass #end of class

class EditLayerController(InlineObjectListStoreController):
    file_filters = ("Layer file", "*.lyr"),
    new_atom_type = None
    
    def _setup_treeview(self, tv, model):
        tv.set_model(None)
        tv.set_model(model)

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
            rend.connect('edited', self.on_item_cell_edited, (model, colnr))
            col = gtk.TreeViewColumn(title, rend, text=colnr)
            col.set_resizable(False)
            col.set_expand(True)
            if renderer is not None:
                col.set_cell_data_func(rend, renderer, colnr)
            tv.append_column(col)
        add_text_col('Atom name', model.c_data_name)
        add_text_col('Z (nm)', model.c_data_z, float_renderer)
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
        InlineObjectListStoreController.__init__(self, model_property_name, *args, **kwargs)
        self.new_atom_type = None
        
    def create_new_object_proxy(self):
        return Atom("New Atom", parent=self.model)
        
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_export_item(self, widget, user_data=None):
        def on_accept(save_dialog):
            fltr = save_dialog.get_filter()
            filename = save_dialog.get_filename()
            if fltr.get_name() == self.file_filters[0][0]:
                if filename[len(filename)-4:] != self.file_filters[0][1][1:]:
                    filename = "%s%s" % (filename, self.file_filters[0][1][1:])
                Atom.save_as_csv(filename, self.get_all_objects())
        self.run_save_dialog("Export atoms", on_accept, parent=self.view.get_toplevel(), suggest_name="%s%s" % (self.model.data_name.lower(), self.model_property_name.replace("data", "").lower()) )
        
    def on_import_item(self, widget, user_data=None):        
        def import_layer(dialog):
            def on_accept(open_dialog):
                fltr = open_dialog.get_filter()
                if fltr.get_name() == self.file_filters[0][0]:
                    self.liststore.clear()
                    Atom.get_from_csv(open_dialog.get_filename(), self.liststore.append, self.model)
            self.run_load_dialog("Import atoms", on_accept, parent=self.view.get_toplevel())            
        self.run_confirmation_dialog(message="Are you sure?\nImporting a layer file will clear the current list of atoms!", on_accept_callback=import_layer, parent=self.view.get_toplevel())
        
    def on_atom_type_changed(self, combo, path, new_iter, user_data=None):
        self.new_atom_type = self.model.phase.project.data_atom_types.get_user_data(new_iter)
        return True

    def on_atom_type_edited(self, combo, path, new_text, atom_model):
        atom = atom_model.get_user_data_from_path((int(path),))
        if self.new_atom_type == None and not new_text in (None, "" ):
            try:
                self.new_atom_type = self.model.phase.project.data_atom_types.get_item_by_index(new_text)
            except:
                pass
        
        if atom is not None:
            atom.data_atom_type = self.new_atom_type
            self.new_atom_type = None
            return True
        return False
        
    pass #end of class

class EditAtomRatioController(InlineObjectListStoreController):
    file_filters = ("Atom ratio file", "*.rat"),
    
    
    def create_prop_store(self):
        store = gtk.ListStore(str, object)        
        for i, atom in enumerate(self.model._data_layer_atoms._model_data):
            store.append(["data_layer_atoms.%d" % i, atom])
        for i, atom in enumerate(self.model._data_interlayer_atoms._model_data):
            store.append(["data_interlayer_atoms.%d" % i, atom])

        return store
    
    def _reset_treeview(self, tv, model):
        tv.set_model(None)
        tv.set_model(model)

        #reset:
        for col in tv.get_columns():
            tv.remove_column(col)

        def add_text_col(title, colnr, renderer=None):
            rend = gtk.CellRendererText()
            rend.set_property("editable", True)
            rend.connect('edited', self.on_item_cell_edited, (model, colnr))
            col = gtk.TreeViewColumn(title, rend, text=colnr)
            col.set_resizable(False)
            col.set_expand(True)
            if renderer is not None:
                col.set_cell_data_func(rend, renderer, colnr)
            tv.append_column(col)
        add_text_col('Ratio name', model.c_data_name)

        def add_prop_col(title, colnr):
        
            atomstore = self.create_prop_store()
        
            def atom_renderer(column, cell, model, itr, colnr):
                atom_ratio = model.get_user_data(itr)
                prop = model.get_value(itr, colnr)
                atom, attr = atom_ratio._parseattr(prop)
                if attr == prop:
                    cell.set_property("markup", "NaN")
                else:
                    cell.set_property("markup", atom.data_name)
            
            def combo_cell_renderer(column, cell, model, itr, data=None):
                atom = model.get_value(itr, 1)
                cell.set_property("markup", atom.data_name)
            
            def adjust_combo(combo, cell, editable, path, data=None):
                text_cell = cell.get_cells()[0]
                cell.set_cell_data_func(text_cell, combo_cell_renderer, None)
        
            rend = gtk.CellRendererCombo()
            rend.set_property("model", atomstore)
            rend.set_property("text_column", 0)
            rend.set_property("editable", True)
            rend.set_property("has-entry", False)
            rend.connect('edited', self.on_item_cell_edited, (model, colnr))
            rend.connect('editing-started', adjust_combo, None)
            col = gtk.TreeViewColumn(title, rend)
            col.set_resizable(True)
            col.set_expand(True)
            col.set_cell_data_func(rend, atom_renderer, colnr)
            tv.append_column(col)
            
        add_prop_col('Atom #1', model.c_data_prop1)
        add_prop_col('Atom #2', model.c_data_prop2)

        def float_renderer(column, cell, model, itr, col=None):
            nr = model.get_value(itr, col)
            if nr is not None:
                cell.set_property('text', "%.5f" % nr)
            else:
                cell.set_property('text', '#NA#')

        def add_text_col(title, colnr, renderer=None):
            rend = gtk.CellRendererText()
            rend.set_property("editable", True)
            rend.connect('edited', self.on_item_cell_edited, (model, colnr))
            col = gtk.TreeViewColumn(title, rend, text=colnr)
            col.set_resizable(False)
            col.set_expand(True)
            if renderer is not None:
                col.set_cell_data_func(rend, renderer, colnr)
            tv.append_column(col)
        add_text_col('Sum', model.c_data_sum, float_renderer)
        add_text_col('Ratio', model.c_data_ratio, float_renderer)
    
    def _setup_treeview(self, tv, model):
    
        def on_item_changed(*args):
            self._reset_treeview(tv, model)
                    
        self.model._data_layer_atoms.connect("item-removed", on_item_changed)
        self.model._data_interlayer_atoms.connect("item-removed", on_item_changed)
        self.model._data_layer_atoms.connect("item-inserted", on_item_changed)
        self.model._data_interlayer_atoms.connect("item-inserted", on_item_changed)
        
        self._reset_treeview(tv, model)


    def __init__(self, model_property_name, *args, **kwargs):
        InlineObjectListStoreController.__init__(self, model_property_name, *args, **kwargs)
        self.new_atom_type = None
        
    def create_new_object_proxy(self):
        return ComponentRatioFunction(data_name="New Ratio", parent=self.model)
        
    pass #end of class


class EditComponentController(ChildController):

    layer_view = None
    layer_controller = None
    
    interlayer_view = None
    interlayer_controller = None
    
    atom_ratios_view = None
    atom_ratios_controller = None
    
    ucpa_view = None
    ucpa_controller = None
    
    ucpb_view = None
    ucpb_controller = None

    def __init__(self, *args, **kwargs):
        ChildController.__init__(self, *args, **kwargs)
        
        self.layer_view = InlineObjectListStoreView(parent=self.view)
        self.layer_controller = EditLayerController("_data_layer_atoms", model=self.model, view=self.layer_view, parent=self)
        
        self.interlayer_view = InlineObjectListStoreView(parent=self.view)
        self.interlayer_controller = EditLayerController("_data_interlayer_atoms", model=self.model, view=self.interlayer_view, parent=self)
        
        self.atom_ratios_view = InlineObjectListStoreView(parent=self.view)
        self.atom_ratios_controller = EditAtomRatioController("_data_atom_ratios", model=self.model, view=self.atom_ratios_view, parent=self)       
        
        self.ucpa_view = EditUnitCellPropertyView(parent=self.view)
        self.ucpa_controller = EditUnitCellPropertyController(extra_props=[("data_cell_b", "B cell length"),], model=self.model.data_ucp_a, view=self.ucpa_view, parent=self)
        
        self.ucpb_view = EditUnitCellPropertyView(parent=self.view)
        self.ucpb_controller = EditUnitCellPropertyController(extra_props=[("data_cell_a", "A cell length"),], model=self.model.data_ucp_b, view=self.ucpb_view, parent=self)

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
                    self.adapt(name)
                elif name == "data_layer_atoms":
                    self.view.set_layer_view(self.layer_view.get_top_widget())
                elif name == "data_interlayer_atoms":
                    self.view.set_interlayer_view(self.interlayer_view.get_top_widget())
                elif name ==  "data_atom_ratios":
                    self.view.set_atom_ratios_view(self.atom_ratios_view.get_top_widget())
                elif name in ("data_ucp_a", "data_ucp_b"):
                    self.view.set_ucpa_view(self.ucpa_view.get_top_widget())
                    self.view.set_ucpb_view(self.ucpb_view.get_top_widget())
                elif not name in ("data_all_atoms", "parent", "added", "removed", "needs_update", "dirty", "P_dirty", "F_dirty"):
                    FloatEntryValidator(self.view["component_%s" % name])
                    self.adapt(name)
            self.update_sensitivities()
            return

    def update_sensitivities(self):
        can_inherit = (self.model.data_linked_with != None)

        def update(widget, name):
            self.view[widget].set_sensitive(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view[widget].set_visible(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view["component_inherit_%s" % name].set_sensitive(can_inherit)
        for name in ("d001", ):
            update("component_data_%s" % name, name)
        for name in ("interlayer_atoms", "layer_atoms", "atom_ratios", "ucp_a", "ucp_b"):
            update("%s_container" % name, name)


    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("inherit_layer_atoms", assign=True)
    @Controller.observe("inherit_interlayer_atoms", assign=True)
    @Controller.observe("inherit_atom_ratios", assign=True)
    @Controller.observe("inherit_ucp_a", assign=True)
    @Controller.observe("inherit_ucp_b", assign=True)
    @Controller.observe("inherit_d001", assign=True)
    def notif_change_data_inherit(self, model, prop_name, info):
        self.update_sensitivities()
        """can_inherit = (self.model.data_linked_with != None)
        if prop_name in ("inherit_d001",):
            widget_name = prop_name.replace("inherit_", "component_data_")
        else:
            widget_name = "%s_container" % prop_name.replace("inherit_", "")
            self.view[widget_name].set_visible(can_inherit and not info.new)
        self.view[widget_name].set_sensitive(can_inherit and not info.new)"""
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
    columns = [ ("Component name", "c_data_name") ]
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
                if name in ["data_all_atoms", "parent", "added", "removed", "needs_update", "dirty"]:
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
                    def phase_renderer(celllayout, cell, model, itr, user_data=None):
                        phase = model.get_user_data(itr)
                        cell.set_sensitive(phase.data_R == self.model.data_R and phase.data_G == self.model.data_G and phase.get_based_on_root() != self.model)
                    combo.set_cell_data_func(cell, phase_renderer, None)

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
            self.view[widget_name].set_visible(not (can_inherit and getattr(self.model, "inherit_%s" % name)))
            self.view["phase_inherit_%s" % name].set_sensitive(can_inherit)

        sensitive = not (can_inherit and getattr(self.model, "inherit_probabilities"))            
        self.view["phase_data_probabilities"].set_sensitive(sensitive)
        if not sensitive: self.view["phase_data_probabilities"].set_expanded(sensitive)
        self.view["phase_inherit_probabilities"].set_sensitive(can_inherit)

    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("inherit_sigma_star", assign=True)
    @Controller.observe("inherit_min_CSDS", assign=True)    
    @Controller.observe("inherit_max_CSDS", assign=True)    
    @Controller.observe("inherit_mean_CSDS", assign=True)
    @Controller.observe("inherit_probabilities", assign=True)
    def notif_change_data_inherit(self, model, prop_name, info):
        self.update_sensitivities()
        """can_inherit = (self.model.data_based_on != None)
        widget_name = prop_name.replace("inherit_", "phase_data_")
        self.view[widget_name].set_sensitive(can_inherit and not info.new)"""
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
    columns = [ ("Phase name", "c_data_name") ]
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

    def load_phase(self, filename):
        print "Importing phase..."
        new_phase = Phase.load_object(filename, parent=self.model)
        new_phase.resolve_json_references()
        self.model.data_phases.append(new_phase)
        self.select_object(new_phase)
        return new_phase

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_add_object_clicked(self, event):
        def on_accept(phase, G, R):
            if not phase:
                G = int(G)
                R = int(R)
                if G != None and G > 0 and R != None and R >= 0 and R <= 4:
                    new_phase = Phase("New Phase",  data_G=G, data_R=R, parent=self.model)
                    self.model.data_phases.append(new_phase)
                    self.select_object(new_phase)
            else:
                self.load_phase("%s/%s/%s" % (settings.BASE_DIR, settings.DEFAULT_PHASES_DIR, phase))
                
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
                phase.save_object(filename=filename) #FIXME BREAK LINKS & SET INHERIT_... to False!!
        self.run_save_dialog("Export phase", on_accept, parent=self.view.get_top_widget())
        return True
        
        
    def on_load_object_clicked(self, event):
        def on_accept(dialog):
            self.load_phase(dialog.get_filename())
        self.run_load_dialog("Import phase", on_accept, parent=self.view.get_top_widget())
        return True
        
class AddPhaseController(DialogController):
    
    def __init__(self, model, view, spurious=False, auto_adapt=False, parent=None, callback=None):
        DialogController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt)    
        self.callback = callback
    
    def register_view(self, view):
        self.update_bounds()
        self.generate_combo()
    
    def update_bounds(self):
        if self.view != None:
            min_R, max_R = get_Rbounds_for_G(self.view.get_G())
            self.view["adj_R"].set_upper(max_R)
            self.view["adj_R"].set_lower(min_R)
        
    def generate_combo(self):
        
        cmb_model = gtk.ListStore(str,str)
        cmb_model.append(("", ""))
        
        import os
        for files in os.listdir("%s/%s" % (settings.BASE_DIR, settings.DEFAULT_PHASES_DIR)):
            if files.endswith(".phs"):
                cmb_model.append((files, files))
        self.view.phase_combo_box.set_model(cmb_model)
         
        cell = gtk.CellRendererText()
        self.view.phase_combo_box.pack_start(cell, True)
        self.view.phase_combo_box.add_attribute(cell, 'text', 0)
    
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.view.hide()
        self.callback(self.view.get_phase(), self.view.get_G(), self.view.get_R())
        return True
        
    def on_g_value_changed(self, adj):
        self.update_bounds()      
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
