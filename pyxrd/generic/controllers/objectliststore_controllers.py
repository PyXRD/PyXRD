# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from contextlib import contextmanager

import gtk

from pyxrd.generic.views.treeview_tools import new_text_column, setup_treeview
from base_controllers import DialogController, BaseController

class ObjectTreeviewMixin():
    """
        Mixin that provides some generic methods to acces or set the objects selected in a treeview.
    """

    def get_selected_object(self, tv):
        objects = ObjectTreeviewMixin.get_selected_objects(self, tv)
        if objects is not None and len(objects) == 1:
            return objects[0]
        return None

    def get_selected_objects(self, tv):
        selection = tv.get_selection()
        if selection.count_selected_rows() >= 1:
            model, paths = selection.get_selected_rows()
            return map(model.get_user_data_from_path, paths)
        return None

    def get_selected_paths(self, tv):
        selection = tv.get_selection()
        if selection.count_selected_rows() >= 1:
            model, paths = selection.get_selected_rows() # @UnusedVariable
            return paths
        return None

    def get_all_objects(self, tv):
        return tv.get_model().get_raw_model_data()

    def set_selected_paths(self, tv, paths):
        selection = tv.get_selection()
        selection.unselect_all()
        for path in paths:
            selection.select_path(path)

class ObjectListStoreMixin(ObjectTreeviewMixin):
    """
        Mixin that can be used for regular ObjectListStoreControllers (two-pane view).
        
        Attributes:
            model_property_name: the property name in the model corresponding to
             the ObjectListStore
            multi_selection: whether or not to allow multiple items to be selected
            columns: a list of tuples (name, column index or name) detailing which
             columns should be added to the TreeView. If a column name is passed,
             it is translated to the corresponding index.
             By default a text column is added, for custom setups you can define
             a custom method name according to this format: setup_treeview_col_name_%s
             Replace the %s with the column name you specified in this list.
            delete_msg: the default message to display when a user wants to delete one or more items.
            obj_type_map: a list of three-tuples (object type, view type, controller type)
             used to create the controller and view for editing a selected object.
    """

    model_property_name = ""
    multi_selection = True
    columns = [ ("Object name", 0) ]
    delete_msg = "Deleting objects is irreversible!\nAre You sure you want to continue?"
    obj_type_map = [] # list of three-tuples (object type, view type, controller type)

    _edit_controller = None
    _edit_view = None

    def __init__(self, model_property_name="", multi_selection=None, columns=[], delete_msg=""):
        self.model_property_name = model_property_name or self.model_property_name
        self.multi_selection = multi_selection or self.multi_selection

        self.liststore.connect("item-removed", self.on_item_removed)
        self.liststore.connect("item-inserted", self.on_item_inserted)

        self.columns = columns or self.columns
        self.delete_msg = delete_msg or self.delete_msg

    @property
    def liststore(self):
        if self.model != None:
            return getattr(self.model, self.model_property_name)
        else:
            return None

    def get_new_edit_view(self, obj):
        """
            Gets a new 'edit object' view for the given obj, view and parent
            view. Default implementation loops over the `obj_type_map` attribute
            until it encounters a match.
        """
        if obj == None:
            return self.view.none_view
        else:
            for obj_tp, view_tp, ctrl_tp in self.obj_type_map: # @UnusedVariable
                if isinstance(obj, obj_tp):
                    return view_tp(parent=self.view)
            raise NotImplementedError, ("Unsupported object type; subclasses of"
                " ObjectListStoreMixin need to define an obj_type_map attribute!")

    def get_new_edit_controller(self, obj, view, parent=None):
        """
            Gets a new 'edit object' controller for the given obj, view and parent
            controller. Default implementation loops over the `obj_type_map` attribute
            until it encounters a match.
        """
        if obj == None:
            return None
        else:
            for obj_tp, view_tp, ctrl_tp in self.obj_type_map: # @UnusedVariable
                if isinstance(obj, obj_tp):
                    return ctrl_tp(model=obj, view=view, parent=parent)
            raise NotImplementedError, ("Unsupported object type; subclasses of"
                " ObjectListStoreMixin need to define an obj_type_map attribute!")

    def edit_object(self, obj):
        self._edit_view = self.view.set_edit_view(self.get_new_edit_view(obj))
        self._edit_controller = self.get_new_edit_controller(obj, self._edit_view, parent=self.parent)
        self._edit_view.show_all()
        return True

    def register_adapters(self):
        # connects the treeview to the liststore
        self.setup_treeview(self.view.treeview)
        # we can now edit 'nothing':
        self.view.set_selection_state(None)
        self.edit_object(None)

    def setup_treeview(self, tv):
        """
            Sets up the treeview with columns based on the columns-tuple passed
            to the __init__ or set in the class definition.
            Subclasses can override either this method completely or provide
            custom column creation code on a per-column basis.
            To do this, create a method for e.g. column with colnr = 2:
            def setup_treeview_col_2(self, treeview, name, col_descr, col_index, tv_col_nr):
                ...
            If a string description of the column number was given, e.g. for the
            column c_name the definition should be:
            def setup_treeview_col_c_name(self, treeview, name, col_descr, col_index, tv_col_nr):
                ...
                
            The method should return True upon success or False otherwise.
        """
        sel_mode = gtk.SELECTION_MULTIPLE if self.multi_selection else gtk.SELECTION_SINGLE
        setup_treeview(
            tv, self.liststore,
            sel_mode=sel_mode,
            on_selection_changed=self.objects_tv_selection_changed)
        tv.set_model(self.liststore)

        # reset:
        for col in tv.get_columns():
            tv.remove_column(col)

        # add columns
        for tv_col_nr, (name, col_descr) in enumerate(self.columns):
            try:
                col_index = int(col_descr)
            except:
                col_index = getattr(self.liststore, str(col_descr), col_descr)

            handled = False
            if hasattr(self, "setup_treeview_col_%s" % str(col_descr)):
                handler = getattr(self, "setup_treeview_col_%s" % str(col_descr))
                if callable(handler):
                    handled = handler(tv, name, col_descr, col_index, tv_col_nr)
            # custom handler failed or not present, default text column:
            if not handled:
                tv.append_column(new_text_column(
                    name, text_col=col_index,
                    resizable=(tv_col_nr == 0),
                    expand=(tv_col_nr == 0),
                    xalign=0.0 if tv_col_nr == 0 else 0.5))

        return True

    def get_selected_object(self):
        return ObjectTreeviewMixin.get_selected_object(self, self.view.treeview)

    def get_selected_objects(self):
        return ObjectTreeviewMixin.get_selected_objects(self, self.view.treeview)

    def get_all_objects(self):
        return ObjectTreeviewMixin.get_all_objects(self, self.view.treeview)

    def select_object(self, obj, unselect_all=True):
        selection = self.view.treeview.get_selection()
        if unselect_all: selection.unselect_all()
        if obj:
            path = self.liststore.on_get_path(obj)
            if path != None: selection.select_path(path)

    def select_objects(self, objs):
        for obj in objs: self.select_object(obj, False)

    def add_object(self, new_object):
        if new_object:
            cur_obj = self.get_selected_object()
            if cur_obj:
                index = self.liststore.index(cur_obj)
                self.liststore.insert(index + 1, new_object)
            else:
                self.liststore.append(new_object)

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------

    def on_item_removed(self, model, item):
        pass

    def on_item_inserted(self, model, item):
        pass

    def objects_tv_selection_changed(self, selection):
        obj = self.get_selected_object()
        objs = self.get_selected_objects()
        self.view.set_selection_state(len(objs) if objs != None else None)
        if self._edit_controller == None or obj != self._edit_controller.model:
            self.edit_object(obj)

    def on_load_object_clicked(self, event):
        raise NotImplementedError

    def on_save_object_clicked(self, event):
        raise NotImplementedError

    def create_new_object_proxy(self):
        raise NotImplementedError

    def on_add_object_clicked(self, event):
        new_object = self.create_new_object_proxy()
        if new_object:
            self.add_object(new_object)
            self.select_object(new_object)
        return True

    @contextmanager
    def _multi_operation_context(self):
        """
            This method should be called as a context manager (with self._multi_...)
            anytime more then one object is changed at the same time.
            Default implementation does not do anything, but this can be used
            to e.g. hold signals from firing until all objects have changed.  
        """
        yield # default implementation doesn't do anything.

    def on_del_object_clicked(self, event, del_callback=None, callback=None):
        tv = self.view.treeview
        selection = tv.get_selection()
        if selection.count_selected_rows() >= 1:
            def delete_objects(dialog):
                with self._multi_operation_context():
                    for obj in self.get_selected_objects():
                        if callable(del_callback):
                            del_callback(obj)
                        else:
                            self.liststore.remove_item(obj)
                        if callable(callback): callback(obj)
                    self.edit_object(None)
            self.run_confirmation_dialog(message=self.delete_msg, on_accept_callback=delete_objects, parent=self.view.get_top_widget())


class ObjectListStoreController(DialogController, ObjectListStoreMixin):
    """
        A stand-alone, regular ObjectListStore controller (left pane with objects and right pane with object properties)
    """
    title = "Edit Dialog"

    def __init__(self, model, view,
                 spurious=False, auto_adapt=False, parent=None,
                 model_property_name="", columns=[], delete_msg="", title=""):
        DialogController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt, parent=parent)
        ObjectListStoreMixin.__init__(self, model_property_name=model_property_name, columns=columns, delete_msg=delete_msg)
        self.title = title or self.title
        view.set_title(self.title)

    def register_adapters(self):
        ObjectListStoreMixin.register_adapters(self)

class ChildObjectListStoreController(BaseController, ObjectListStoreMixin):
    """
        An embeddable, regular ObjectListStore controller (left pane with objects and right pane with object properties)
    """
    def __init__(self, model, view,
                 spurious=False, auto_adapt=False, parent=None,
                 model_property_name="", columns=[], delete_msg=""):
        BaseController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt, parent=parent)
        ObjectListStoreMixin.__init__(self, model_property_name=model_property_name, columns=columns, delete_msg=delete_msg)

    def register_adapters(self):
        ObjectListStoreMixin.register_adapters(self)

class InlineObjectListStoreController(BaseController, ObjectTreeviewMixin):
    """
        ObjectListStore controller that consists of a single TreeView, 
        with import & export and add & delete buttons and an optional combo box
        for type selection
        Subclasses should override the _setup_treeview method to setup their 
        columns and edit support.
    """
    treeview = None
    enable_import = True
    enable_export = True
    model_property_name = ""
    add_types = list()

    @property
    def liststore(self):
        return getattr(self.model, self.model_property_name)

    def _edit_item(self, item):
        item_type = type(item)
        for name, tpe, view, ctrl in self.add_types: # @UnusedVariable
            if tpe == item_type:
                vw = view()
                ctrl(model=item, view=vw, parent=self)
                vw.present()
                break

    def _setup_combo_type(self, combo):
        if self.add_types:
            store = gtk.ListStore(str, object, object, object)
            for name, type, view, ctrl in self.add_types: # @ReservedAssignment
                store.append([name, type, view, ctrl])

            combo.set_model(store)

            cell = gtk.CellRendererText()
            combo.pack_start(cell, True)
            combo.add_attribute(cell, 'text', 0)

            def on_changed(combo, user_data=None):
                itr = combo.get_active_iter()
                if itr != None:
                    val = combo.get_model().get_value(itr, 1)
                    self.add_type = val
            combo.connect('changed', on_changed)
            combo.set_active_iter(store[0].iter)
            combo.set_visible(True)
            combo.set_no_show_all(False)
            combo.show_all()

    def _setup_treeview(self, tv, model):
        raise NotImplementedError

    def __init__(self, model_property_name, enable_import=True, enable_export=True, *args, **kwargs):
        BaseController.__init__(self, *args, **kwargs)
        self.enable_import = enable_import
        self.enable_export = enable_export
        self.model_property_name = model_property_name

    def register_adapters(self):
        if self.liststore is not None:
            self.treeview = self.view.treeview_widget
            self.treeview.connect('cursor-changed', self.on_treeview_cursor_changed, self.liststore)
            self._setup_treeview(self.treeview, self.liststore)
            self.type_combobox = self.view.type_combobox_widget
            self._setup_combo_type(self.type_combobox)
        self.update_sensitivities()
        return

    def update_sensitivities(self):
        self.view.del_item_widget.set_sensitive((self.treeview.get_cursor() != (None, None)))
        self.view.add_item_widget.set_sensitive((self.liststore is not None))
        self.view.export_items_widget.set_visible(self.enable_export)
        self.view.export_items_widget.set_sensitive(len(self.liststore) > 0)
        self.view.import_items_widget.set_visible(self.enable_import)

    def get_selected_object(self):
        return ObjectTreeviewMixin.get_selected_object(self, self.treeview)

    def get_selected_objects(self):
        return ObjectTreeviewMixin.get_selected_objects(self, self.treeview)

    def get_all_objects(self):
        return ObjectTreeviewMixin.get_all_objects(self, self.treeview)

    def select_object(self, obj, unselect_all=True):
        selection = self.treeview.get_selection()
        if unselect_all: selection.unselect_all()
        if hasattr(self.liststore, "on_get_path"):
            selection.select_path(self.liststore.on_get_path(obj))

    def create_new_object_proxy(self):
        raise NotImplementedError

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_treeview_cursor_changed(self, widget, model):
        self.update_sensitivities()

    def on_add_item(self, widget, user_data=None):
        new_object = self.create_new_object_proxy()
        if new_object != None:
            self.liststore.append(new_object)
            self.select_object(new_object)
        self.update_sensitivities()

    def on_del_item(self, widget, user_data=None):
        path, col = self.treeview.get_cursor() # @UnusedVariable
        if path != None:
            itr = self.liststore.get_iter(path)
            self.liststore.remove(itr)
            self.update_sensitivities()
            return True
        return False

    def on_export_item(self, widget, user_data=None):
        raise NotImplementedError

    def on_import_item(self, widget, user_data=None):
        raise NotImplementedError

    def on_item_cell_edited(self, cell, path, new_text, model, col):
        model.set_value(model.get_iter(path), col, model.convert(col, new_text))
        pass

    pass # end of class
