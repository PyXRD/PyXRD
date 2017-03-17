# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from contextlib import contextmanager

import gtk

from mvc.adapters.gtk_support.tree_view_adapters import wrap_list_property_to_treemodel
from mvc.adapters.gtk_support.dialogs.dialog_factory import DialogFactory

from pyxrd.generic.utils import not_none
from pyxrd.generic.views.treeview_tools import new_text_column, setup_treeview

from .base_controller import BaseController
from .dialog_controller import DialogController


class TreeModelMixin(object):
    """
        A mixin providing functionality to get a TreeModel property from a model.
        If that property is an actual TreeModel, it will use it directly.
        Otherwise it will first wrap it in an ObjectListStore
    """

    treemodel_getter_format = "get_%s_tree_model"

    treemodel_property_name = ""
    treemodel_class_type = None

    _treemodel = None
    @property
    def treemodel(self):
        self._update_treemodel_property()
        return self._treemodel

    @property
    def treemodel_data(self):
        if getattr(self, "model", None) is not None:
            return getattr(self.model, self.treemodel_property_name, None)
        else:
            return None

    def __init__(self, treemodel_property_name=None, treemodel_class_type=None, *args, **kwargs):
        super(TreeModelMixin, self).__init__(*args, **kwargs)
        self.treemodel_property_name = not_none(treemodel_property_name, self.treemodel_property_name)
        self.treemodel_class_type = not_none(treemodel_class_type, self.treemodel_class_type)

    def _update_treemodel_property(self):
        if getattr(self, "model", None) is not None:
            self._treemodel = wrap_list_property_to_treemodel(
                self.model,
                self.model.Meta.get_prop_intel_by_name(self.treemodel_property_name)
            )


class TreeViewMixin(object):
    """
        Mixin that provides some generic methods to access or set the objects selected in a treeview.
    """

    treeview_setup_format = "setup_%s_tree_view"

    def get_selected_object(self, tv):
        # call this implementation, not the overriden method:
        objects = TreeViewMixin.get_selected_objects(self, tv)
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
        return tv.get_model()._data

    def set_selected_paths(self, tv, paths):
        selection = tv.get_selection()
        selection.unselect_all()
        for path in paths:
            selection.select_path(path)

class TreeControllerMixin(TreeViewMixin, TreeModelMixin):
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

    multi_selection = True
    columns = [ ("Object name", 0) ]
    delete_msg = "Deleting objects is irreversible!\nAre You sure you want to continue?"
    obj_type_map = [] # list of three-tuples (object type, view type, controller type)

    _edit_controller = None
    _edit_view = None

    def __init__(self, *args, **kwargs):
        self.multi_selection = kwargs.pop("multi_selection", True)
        self.columns = kwargs.pop("columns", self.columns)
        self.delete_msg = kwargs.pop("delete_msg", self.delete_msg)

        super(TreeControllerMixin, self).__init__(*args, **kwargs)

    __row_signal_ids = None
    def _update_treemodel_property(self):
        # If we've connected to a treemodel before, clean up first:
        if self.__row_signal_ids is not None:
            old_treemodel, deleted_id, inserted_id = self.__row_signal_ids
            old_treemodel.disconnect(deleted_id)
            old_treemodel.disconnect(inserted_id)
            self.__row_signal_ids = None
        # If the new treemodel is set, connect it up:
        if getattr(self, "model", None) is not None:
            super(TreeControllerMixin, self)._update_treemodel_property()
            # Use private _treemodel attribute, otherwise we get infinite recursions
            self.__row_signal_ids = (
                self._treemodel,
                self._treemodel.connect("row-deleted", self.on_item_removed),
                self._treemodel.connect("row-inserted", self.on_item_inserted)
            )


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
                " TreeControllerMixin need to define an obj_type_map attribute!")

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
                " TreeControllerMixin need to define an obj_type_map attribute!")

    def edit_object(self, obj):
        self._edit_view = self.view.set_edit_view(self.get_new_edit_view(obj))
        self._edit_controller = self.get_new_edit_controller(obj, self._edit_view, parent=self.parent)
        self._edit_view.show_all()
        return True

    def register_adapters(self):
        # connects the treeview to the treemodel
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
        sel_mode = gtk.SELECTION_MULTIPLE if self.multi_selection else gtk.SELECTION_SINGLE # @UndefinedVariable
        setup_treeview(
            tv, self.treemodel,
            sel_mode=sel_mode,
            on_selection_changed=self.objects_tv_selection_changed)
        tv.set_model(self.treemodel)

        # reset:
        for col in tv.get_columns():
            tv.remove_column(col)

        # add columns
        for tv_col_nr, (name, col_descr) in enumerate(self.columns):
            try:
                col_index = int(col_descr)
            except:
                col_index = getattr(self.treemodel, str(col_descr), col_descr)

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

    def get_selected_index(self):
        cur_obj = self.get_selected_object()
        if cur_obj is not None:
            return self.treemodel_data.index(cur_obj)
        else:
            return None

    def get_selected_object(self):
        return super(TreeControllerMixin, self).get_selected_object(self.view.treeview)

    def get_selected_objects(self):
        return super(TreeControllerMixin, self).get_selected_objects(self.view.treeview)

    def get_all_objects(self):
        return super(TreeControllerMixin, self).get_all_objects(self.view.treeview)

    def select_object(self, obj, path=None, unselect_all=True):
        selection = self.view.treeview.get_selection()
        if unselect_all: selection.unselect_all()
        if obj is not None or path is not None:
            if path is None:
                path = self.treemodel.on_get_path(obj)
            if path is not None: selection.select_path(path)

    def select_objects(self, objs):
        for obj in objs: self.select_object(obj, unselect_all=False)

    def add_object(self, new_object):
        if new_object is not None:
            index = self.get_selected_index()
            if index is not None:
                self.treemodel_data.insert(index + 1, new_object)
            else:
                self.treemodel_data.append(new_object)

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------

    def on_item_removed(self, *args):
        self.select_object(None, unselect_all=True)

    def on_item_inserted(self, model, path, iter):
        self.select_object(None, path=path, unselect_all=True)

    def objects_tv_selection_changed(self, selection):
        obj = self.get_selected_object()
        objs = self.get_selected_objects()
        self.view.set_selection_state(len(objs) if objs is not None else None)
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
                            self.treemodel_data.remove(obj)
                        if callable(callback): callback(obj)
                    self.edit_object(None)
            parent = self.view.get_top_widget()
            if not isinstance(parent, gtk.Window): # @UndefinedVariable
                parent = None
            DialogFactory.get_confirmation_dialog(
                message=self.delete_msg, parent=parent
            ).run(delete_objects)


class ObjectListStoreController(DialogController, TreeControllerMixin):
    """
        A stand-alone, regular ObjectListStore controller (left pane with objects and right pane with object properties)
    """
    title = "Edit Dialog"
    auto_adapt = False

    def __init__(self, *args, **kwargs):
        self.title = not_none(kwargs.pop("title", None), self.title)
        super(ObjectListStoreController, self).__init__(*args, **kwargs)

    def register_view(self, view):
        super(ObjectListStoreController, self).register_view(view)
        view.set_title(self.title)

    @DialogController.model.setter
    def _set_model(self, model):
        super(ObjectListStoreController, self)._set_model(model)
        if self.view is not None:
            self._update_treemodel_property()

    def register_adapters(self):
        TreeControllerMixin.register_adapters(self)


class ChildObjectListStoreController(BaseController, TreeControllerMixin):
    """
        An embeddable, regular ObjectListStore controller (left pane with objects and right pane with object properties)
    """
    auto_adapt = False

    @DialogController.model.setter
    def _set_model(self, model):
        super(ObjectListStoreController, self)._set_model(model)
        if self.view is not None:
            self._update_treemodel_property()

    def register_adapters(self):
        TreeControllerMixin.register_adapters(self)

class InlineObjectListStoreController(BaseController, TreeControllerMixin):
    """
        ObjectListStore controller that consists of a single TreeView, 
        with import & export and add & delete buttons and an optional combo box
        for type selection
        Subclasses should override the _setup_treeview method to setup their 
        columns and edit support.
    """
    treeview = None
    enable_import = False
    enable_export = False
    add_types = list()
    auto_adapt = False

    _edit_dict = None
    def _edit_item(self, item):
        item_type = type(item)
        if self._edit_dict is None:
            # Create a edit dict which keeps track of our controllers
            self._edit_dict = {}

        # If the first time, create the view & controller
        if not item in self._edit_dict:        
            for name, tpe, view, ctrl in self.add_types: # @UnusedVariable
                if tpe == item_type:
                    vw = view()
                    ctrl = ctrl(model=item, view=vw, parent=self)
                    self._edit_dict[item] = (vw, ctrl)
                    break
        # Re-use previously created controllers
        vw, ctrl = self._edit_dict[item]
        vw.present()


    def _setup_combo_type(self, combo):
        if self.add_types:
            store = gtk.ListStore(str, object, object, object) # @UndefinedVariable
            for name, type, view, ctrl in self.add_types: # @ReservedAssignment
                store.append([name, type, view, ctrl])

            combo.set_model(store)

            cell = gtk.CellRendererText() # @UndefinedVariable
            combo.pack_start(cell, True)
            combo.add_attribute(cell, 'text', 0)

            def on_changed(combo, user_data=None):
                itr = combo.get_active_iter()
                if itr is not None:
                    val = combo.get_model().get_value(itr, 1)
                    self.add_type = val
            combo.connect('changed', on_changed)
            combo.set_active_iter(store[0].iter)
            combo.set_visible(True)
            combo.set_no_show_all(False)
            combo.show_all()

    def _setup_treeview(self, tv, model):
        raise NotImplementedError

    def __init__(self, *args, **kwargs):
        self.enable_import = kwargs.pop("enable_import", self.enable_import)
        self.enable_export = kwargs.pop("enable_export", self.enable_export)
        super(InlineObjectListStoreController, self).__init__(*args, **kwargs)

    @BaseController.model.setter
    def _set_model(self, model):
        super(ObjectListStoreController, self)._set_model(model)
        if self.view is not None:
            self._update_treemodel_property()

    def register_adapters(self):
        if self.treemodel is not None:
            self.treeview = self.view.treeview
            self.treeview.connect('cursor-changed', self.on_treeview_cursor_changed, self.treemodel)
            self._setup_treeview(self.treeview, self.treemodel)
            self.type_combobox = self.view.type_combobox_widget
            self._setup_combo_type(self.type_combobox)
            self.update_sensitivities()
        return

    def update_sensitivities(self):
        self.view.del_item_widget.set_sensitive((self.treeview.get_cursor() != (None, None)))
        self.view.add_item_widget.set_sensitive((self.treemodel is not None))
        self.view.export_items_widget.set_visible(self.enable_export)
        self.view.export_items_widget.set_sensitive(len(self.treemodel_data) > 0)
        self.view.import_items_widget.set_visible(self.enable_import)

    def get_selected_object(self):
        return TreeViewMixin.get_selected_object(self, self.treeview)

    def get_selected_objects(self):
        return TreeViewMixin.get_selected_objects(self, self.treeview)

    def get_all_objects(self):
        return TreeViewMixin.get_all_objects(self, self.treeview)

    def select_object(self, obj, path=None, unselect_all=True):
        selection = self.treeview.get_selection()
        if unselect_all: selection.unselect_all()
        if obj is not None and hasattr(self.treemodel, "on_get_path"):
            selection.select_path(self.treemodel.on_get_path(obj))
        elif path is not None:
            selection.select_path(path)

    def create_new_object_proxy(self):
        raise NotImplementedError

    def edit_object(self, obj):
        pass

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_treeview_cursor_changed(self, widget, model):
        self.update_sensitivities()

    def on_item_cell_edited(self, cell, path, new_text, model, col):
        model.set_value(model.get_iter(path), col, model.convert(col, new_text))
        pass

    pass # end of class
