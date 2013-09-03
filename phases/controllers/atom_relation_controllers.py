# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

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
from phases.models.atom_relations import AtomRatio, AtomContents

class AtomComboMixin(object):
    
    extra_props = []
    custom_handler_names = []
    
    def reset_combo_box(self, name):
        #Get store, reset combo
        store = self.model.create_prop_store(self.extra_props)
        combo = self.view[self.view.widget_format % name]
        combo.clear()
        combo.set_model(store)
        
        #Add text column:
        def get_name(layout, cell, model, itr, data=None):
            obj, lbl = model.get(itr, 0, 2)
            if callable(lbl): lbl = lbl(obj)
            cell.set_property("markup", lbl)
        add_combo_text_column(combo, data_func=get_name)
        
        #Set the selected item to active:
        prop = getattr(self.model, name)
        if prop != None:
            prop = tuple(prop)
            for row in store:
                if tuple(store.get(row.iter, 0, 1)) == prop:
                    combo.set_active_iter(row.iter)
                    break
           
        return combo, store
        
    @staticmethod
    def custom_handler(controller, intel, prefix):
        if intel.name in controller.custom_handler_names:
            combo, store = controller.reset_combo_box(intel.name)
            def on_changed(combo, user_data=None):
                itr = combo.get_active_iter()
                if itr != None:
                    val = combo.get_model().get(itr, 0, 1)
                    setattr(controller.model, combo.get_data('model_prop'), val)
            combo.set_data('model_prop', intel.name)
            combo.connect('changed', on_changed)
            
            def on_item_changed(*args):
                controller.reset_combo_box(intel.name)
            
            #use private properties so we connect to the actual object stores and not the inherited ones
            controller.model.parent._layer_atoms.connect("item-removed", on_item_changed)
            controller.model.parent._interlayer_atoms.connect("item-removed", on_item_changed)
            controller.model.parent._layer_atoms.connect("item-inserted", on_item_changed)
            controller.model.parent._interlayer_atoms.connect("item-inserted", on_item_changed)
            
        else: return False
        return True
    

class EditUnitCellPropertyController(BaseController, AtomComboMixin):
    """ 
        Controller for the UnitCellProperty models (a and b cell lengths)
    """
    
    custom_handler_names = ["prop",]
    widget_handlers = {
        'combo': 'custom_handler',
        'check': 'check_handler',
    }

    def __init__(self, extra_props, **kwargs):
        BaseController.__init__(self, **kwargs)
        self.extra_props = extra_props
        
    @staticmethod
    def check_handler(controller, intel, prefix):
        if intel.name == "enabled":
            controller.adapt(intel.name, controller.view.widget_format % intel.name)
            controller.view["ucp_disabled"].set_active(not controller.model.enabled)
            controller.view["ucp_enabled"].set_active(controller.model.enabled)
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

class EditAtomRatioController(DialogController, AtomComboMixin):
    """ 
        Controller for the atom ratio edit dialog
    """
    
    custom_handler_names = ["atom1", "atom2"]
    widget_handlers = {
        'custom': 'custom_handler',
    }
            
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
            col = new_pb_column(" ", resizable=False, expand=False, stock_id=image)
            col.set_data("col_descr", colnr)
            tv.append_column(col)
        setup_image_button("213-up-arrow", "Up")
        setup_image_button("212-down-arrow", "Down")
        setup_image_button("030-pencil", "Edit")
                   
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
