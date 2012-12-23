# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk

import settings

from gtkmvc import Controller

from generic.views.validators import FloatEntryValidator

from generic.views.treeview_tools import (
    new_text_column, 
    new_pb_column, 
    new_combo_column, 
    create_float_data_func, 
    setup_treeview
)
from generic.views.combobox_tools import add_combo_text_column
from generic.views import InlineObjectListStoreView
from generic.controllers import (
    DialogController,
    InlineObjectListStoreController,
    BaseController,
)

from atoms.models import Atom

from phases.views import EditUnitCellPropertyView, EditAtomRatioView, EditAtomContentsView
from phases.atom_relations import AtomRatio, AtomContents

class EditUnitCellPropertyController(BaseController):
    """ 
        Controller for the UnitCellProperty models (a and b cell lengths)
    """
    
    widget_handlers = {
        'combo': 'combo_handler',
        'check': 'check_handler',
    }
    
    def reset_prop_store(self):
        combo = self.view[self.view.widget_format % "prop"]
        #object, property, label(-callback)
        store = gtk.ListStore(object, str, object)
        for i, atom in enumerate(self.model.parent._layer_atoms._model_data):
            store.append([atom, "pn", lambda o: o.name])
        for i, atom in enumerate(self.model.parent._interlayer_atoms._model_data):
            store.append([atom, "pn", lambda o: o.name])
        for prop in self.extra_props:
            store.append(prop)
        combo.set_model(store)

        for row in store:
            if list(store.get(row.iter, 0, 1)) == self.model.prop:
                combo.set_active_iter(row.iter)
                break
        return store

    def __init__(self, extra_props, **kwargs):
        BaseController.__init__(self, **kwargs)
        self.extra_props = extra_props

    @staticmethod
    def combo_handler(self, intel, prefix):
        if intel.name == "prop":
            combo = self.view[self.view.widget_format % intel.name]
            store = self.reset_prop_store()
            
            def on_changed(combo, user_data=None):
                itr = combo.get_active_iter()
                if itr != None:
                    obj, prop = combo.get_model().get(itr, 0, 1)
                    self.model.prop = (obj, prop)
            combo.connect('changed', on_changed)
            
            def get_name(layout, cell, model, itr, data=None):
                obj, lbl = model.get(itr, 0, 2)
                if callable(lbl): lbl = lbl(obj)
                cell.set_property("markup", lbl)
            add_combo_text_column(combo, data_func=get_name)
            
            def on_item_changed(*args):
                self.reset_prop_store()
            
            #use private properties so we connect to the actual object stores and not the inherited ones
            self.model.parent._layer_atoms.connect("item-removed", on_item_changed)
            self.model.parent._interlayer_atoms.connect("item-removed", on_item_changed)
            self.model.parent._layer_atoms.connect("item-inserted", on_item_changed)
            self.model.parent._interlayer_atoms.connect("item-inserted", on_item_changed)
        else: return False
        return True
        
    @staticmethod
    def check_handler(self, intel, prefix):
        if intel.name == "enabled":
            self.adapt(intel.name, self.view.widget_format % intel.name)
            self.view["ucp_disabled"].set_active(not self.model.enabled)
            self.view["ucp_enabled"].set_active(self.model.enabled)
        else: return False
        return True

    def register_adapters(self):
        BaseController.register_adapters(self)
        self.update_sensitivities()

    def update_sensitivities(self):
        if self.model.enabled:
            self.view['ucp_value'].set_sensitive(False)
            self.view['box_enabled'].set_sensitive(True)
        else:        
            self.view['ucp_value'].set_sensitive(True)
            self.view['box_enabled'].set_sensitive(False)        
       
    # ------------------------------------------------------------
    #      Notifications of observable properties
    # ------------------------------------------------------------
    @Controller.observe("enabled", assign=True)
    def notif_enabled_changed(self, model, prop_name, info):
        self.update_sensitivities()
        return
        
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_opt_enabled_group_changed(self, widget, *args):
        self.update_sensitivities()
    
    pass #end of class

class EditAtomRatioController(DialogController):
    """ 
        Controller for the atom ratio edit dialog
    """
    
    widget_handlers = {
        'custom': 'custom_handler',
    }
    
    def reset_combo_box(self, name):
        if self.model is not None and self.model.parent is not None:
            #TODO make this a more general function to be used by both AtomRatio's and UCP's
            # problem: what to do with cell length parameters?
            # part of the solution would be to let both of these models
            # generate similar property stores (object, label/callable) tuples
            store = self.model.create_prop_store()
            combo = self.view[self.view.widget_format%name]
            combo.set_model(store)

            combo.clear()
            def atom_renderer(column, cell, model, itr, col):
                obj = model.get_value(itr, col)
                if obj:
                    cell.set_property('text', obj.name)
                else:
                    cell.set_property('text', '#NA#')
            add_combo_text_column(combo, data_func=(atom_renderer, (0,)))

            for row in store:
                if list(store.get(row.iter, 0, 1)) == getattr(self.model, name):
                    combo.set_active_iter(row.iter)
                    break   
                    
            return combo, store
    
    @staticmethod
    def custom_handler(self, intel, prefix):
        if intel.name in ("atom1", "atom2"):                   
            combo, store = self.reset_combo_box(intel.name)
            def on_changed(combo, user_data=None):
                itr = combo.get_active_iter()
                if itr != None:
                    val = combo.get_model().get(itr, 0, 1)
                    setattr(self.model, combo.get_data('model_prop'), val)
            combo.set_data('model_prop', intel.name)
            combo.connect('changed', on_changed)
        else: return False
        return True
            
    pass #end of class
    
class EditAtomContentsController(DialogController):
    """ 
        Controller for the atom contents edit dialog
    """
    
    contents_list_view = None
    contents_list_controller = None

    widget_handlers = { 'custom': 'widget_handler' }

    def __init__(self, *args, **kwargs):
        DialogController.__init__(self, *args, **kwargs)
        self.contents_list_view = InlineObjectListStoreView(parent=self.view)
        self.contents_list_controller = ContentsListController("atom_contents", model=self.model, view=self.contents_list_view, parent=self)

    @staticmethod
    def widget_handler(self, intel, prefix):
        if intel.name == "atom_contents":
            self.view.set_contents_list_view(self.contents_list_view.get_top_widget())
        else: return False
        return True
            
    pass #end of class

class ContentsListController(InlineObjectListStoreController):
    """ 
        Controller for the atom contents ListStore
    """
    new_val = None
    
    def _reset_treeview(self, tv, model):
        setup_treeview(tv, model, sel_mode=gtk.SELECTION_MULTIPLE, reset=True)
        
        #Atom column:
        def atom_renderer(column, cell, model, itr, col):
            obj = model.get_value(itr, col)
            if hasattr(obj, "name"):
                cell.set_property('text', obj.name)
            else:
                cell.set_property('text', '#NA#')
        def adjust_combo(cell, editable, path, data=None):
            if editable!=None:
                rend = gtk.CellRendererText()
                editable.clear()
                editable.pack_start(rend)
                editable.set_cell_data_func(rend, atom_renderer, 0)
        tv.append_column(new_combo_column(
            "Atoms",
            changed_callback=self.on_atom_changed,
            edited_callback=self.on_atom_edited,
            editing_started_callback=adjust_combo,
            xalign=0.0,
            model=self.model.create_prop_store(),
            data_func=(atom_renderer, (0,)),
            text_column=0,
            editable=True))
        
        #Content column:
        def on_float_edited(rend, path, new_text, col):
            itr = model.get_iter(path)
            try:
                model.set_value(itr, col, float(new_text))
            except ValueError:
                print "Invalid value entered ('%s')!" % new_text
            return True
        tv.append_column(new_text_column('Default contents', text_col=2, xalign=0.0, 
            editable=True,
            data_func=create_float_data_func(),
            edited_callback=(on_float_edited, (2,))))
                   
    def _setup_treeview(self, tv, model):
        self._reset_treeview(tv, model)
        
    def __init__(self, model_property_name, **kwargs):
        InlineObjectListStoreController.__init__(self, model_property_name, enable_import=False, enable_export=False, **kwargs)
        
    def create_new_object_proxy(self):
        return [None, None, 1.0]
      
    def on_atom_changed(self, combo, path, new_iter, user_data=None):
        self.new_val = combo.get_property("model").get(new_iter, 0, 1)
        
    def on_atom_edited(self, combo, path, new_text, args=None):
        if self.new_val:
            new_atom, new_prop = self.new_val
            self.liststore.set(self.liststore.get_iter(path), 0, new_atom, 1, new_prop)
            self.new_val = None
        return True
        
    pass #end of class

class EditAtomRelationsController(InlineObjectListStoreController):
    """ 
        Controller for the components' atom relations ObjectListStore
    """
    file_filters = ("Atom relation", "*.atr"),
    
    add_types = [
        ("Ratio", AtomRatio, EditAtomRatioView, EditAtomRatioController),
        ("Contents", AtomContents, EditAtomContentsView, EditAtomContentsController),
    ]
    
    def _reset_treeview(self, tv, model):
        setup_treeview(tv, model, sel_mode=gtk.SELECTION_MULTIPLE, reset=True)

        #Name column:
        col = new_text_column(
            'Name',
            editable=True,
            edited_callback=(self.on_item_cell_edited, (model, model.c_name)),
            resizable=False,
            text_col=model.c_name)
        col.set_data("col_descr", 'Name')
        tv.append_column(col)

        #Value of the relation:
        col = new_text_column(
            'Value',
            data_func=create_float_data_func(),
            editable=True,
            edited_callback=(self.on_item_cell_edited, (model, model.c_value)),
            resizable=False,
            text_col=model.c_value)
        col.set_data("col_descr", 'Value')
        tv.append_column(col)
                       
        #Up, down and edit arrows:       
        def setup_image_button(image, colnr):
            col = new_pb_column("", resizable=False, expand=False, stock_id=image)
            col.set_data("col_descr", colnr)
            tv.append_column(col)
        setup_image_button(gtk.STOCK_GO_UP, "Up")
        setup_image_button(gtk.STOCK_GO_DOWN, "Down")
        setup_image_button(gtk.STOCK_EDIT, "Edit")
                   
    def _setup_treeview(self, tv, model):   
        tv.connect('button-press-event', self.tv_button_press)
        self._reset_treeview(tv, model)

    def __init__(self, model_property_name, **kwargs):
        InlineObjectListStoreController.__init__(self, model_property_name, enable_import=False, enable_export=False, **kwargs)
        
    def create_new_object_proxy(self):
        return self.add_type(parent=self.model)
        
    def tv_button_press(self, tv, event):    
        relation = None
        ret = tv.get_path_at_pos(int(event.x), int(event.y))
        
        if ret is not None:
            path, col, x, y = ret
            model = tv.get_model()
            relation = model.get_user_data_from_path(path)
            column = col.get_data("col_descr")
        if event.button == 1 and relation is not None:
            column = col.get_data("col_descr")
            if column == "Edit":
                self._edit_item(relation)
                return True
            elif column == "Up":
                model.move_item_up(relation)
                return True
            elif column == "Down":
                model.move_item_down(relation)
                return True  
    
        
    pass #end of class
