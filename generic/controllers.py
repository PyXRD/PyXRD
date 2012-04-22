# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk
import gobject
 
from gtkmvc import Controller

from generic.utils import retreive_lowercase_extension

def ctrl_setup_combo_with_list(ctrl, combo, prop_name, list_prop_name):
    store = gtk.ListStore(str, str)   
    list_data = getattr(ctrl.model, list_prop_name)             
    for key in list_data:
        store.append([key, list_data[key]])
        
    combo.set_model(store)

    cell = gtk.CellRendererText()
    combo.pack_start(cell, True)
    combo.add_attribute(cell, 'text', 1)
    
    def on_changed(combo, user_data=None):
        itr = combo.get_active_iter()
        if itr != None:
            val = combo.get_model().get_value(itr, 0)
            setattr(ctrl.model, prop_name, val)
    combo.connect('changed', on_changed)

    for row in store:
        if store.get_value(row.iter, 0) == str(getattr(ctrl.model, prop_name)):
            combo.set_active_iter(row.iter)
            break


class DialogMixin():
    def extract_filename(self, dialog):
        filename = self._adjust_filename(dialog.get_filename(), self.get_selected_glob(dialog.get_filter()))
        dialog.set_filename(filename)
        return filename

    def _adjust_filename(self, filename, glob):
        extension = glob[1:]
        if filename[len(filename)-len(extension):] != extension:
            filename = "%s%s" % (filename, glob[1:])
        return filename

    def get_selected_glob(self, filter, file_filters=None):
        selected_name = filter.get_name()
        for name, globs in (file_filters or self.file_filters):
            if selected_name==name:
                return retreive_lowercase_extension(globs[0])

    def _get_object_file_filters(self):
        for name, re in self.file_filters:
            ffilter = gtk.FileFilter()
            ffilter.set_name(name)
            if isinstance(re, (str, unicode)):
                ffilter.add_pattern(re)
            else:
                for expr in re:
                    ffilter.add_pattern(expr)
            yield ffilter

    def _run_dialog(self, dialog, on_accept_callback=None, on_reject_callback=None):
        response = dialog.run()
        if response in (gtk.RESPONSE_ACCEPT, gtk.RESPONSE_YES, gtk.RESPONSE_APPLY, gtk.RESPONSE_OK) and on_accept_callback is not None:
            on_accept_callback(dialog)
        elif on_reject_callback is not None:
            on_reject_callback(dialog)
        dialog.destroy() 

    def run_file_dialog(self, action, title, on_accept_callback, on_reject_callback=None, parent=None, suggest_name=None, extra_widget=None, multiple=False):
        dialog = gtk.FileChooserDialog(
                        title=title,
                        parent=parent,
                        action=action,
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                 gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        dialog.set_select_multiple(multiple)
        if extra_widget:
            dialog.set_extra_widget(extra_widget)
        dialog.set_do_overwrite_confirmation(True)
        if suggest_name:
            dialog.set_current_name(suggest_name)
        for fltr in self._get_object_file_filters():
            dialog.add_filter (fltr)
        self._run_dialog(dialog, on_accept_callback, on_reject_callback)
        
    def run_save_dialog(self, title, on_accept_callback, on_reject_callback=None, parent=None, suggest_name=None, extra_widget=None):
        self.run_file_dialog(gtk.FILE_CHOOSER_ACTION_SAVE, title, on_accept_callback, on_reject_callback, parent, suggest_name, extra_widget, multiple=False)
            
    def run_load_dialog(self, title, on_accept_callback, on_reject_callback=None, parent=None, suggest_name=None, extra_widget=None, multiple=False):
        self.run_file_dialog(gtk.FILE_CHOOSER_ACTION_OPEN, title, on_accept_callback, on_reject_callback, parent, suggest_name, extra_widget, multiple=multiple)

    def run_confirmation_dialog(self, message, on_accept_callback, on_reject_callback=None, parent=None):
            dialog = gtk.MessageDialog(
                        parent=parent,
                        flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                        type=gtk.MESSAGE_WARNING,
                        buttons=gtk.BUTTONS_YES_NO,
                        message_format=message)
            self._run_dialog(dialog, on_accept_callback, on_reject_callback)
            
    def run_information_dialog(self, message, on_accept_callback=None, parent=None):
            dialog = gtk.MessageDialog(
                        parent=parent,
                        flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                        type=gtk.MESSAGE_INFO,
                        buttons=gtk.BUTTONS_OK,
                        message_format=message)
            self._run_dialog(dialog, None, None)

class _Delayed():
    def __init__(self, f):
        self.__f = f
        self.__tmrid = None

    def __call__(self):
        def wrapper(*args, **kwargs):
            if self.__tmrid != None:
                gobject.source_remove(self.__tmrid)   
            self.__tmrid = gobject.timeout_add(500, self.__timeout_handler__, *args, **kwargs)
        return wrapper
      
    def __timeout_handler__(self, *args, **kwargs):
        self.__f(*args, **kwargs)
        self._upt_id = None
        return False

def delayed(f, *args, **kwargs):
    return _Delayed(f).__call__()

class BaseController (Controller, DialogMixin):

    file_filters = ("All Files", "*.*")

    def __init__(self, model, view, spurious=False, auto_adapt=False, parent=None):
        self.parent = parent
        
        Controller.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt)
        
        if parent is not None:
            self.statusbar = parent.statusbar
        else:
            self.statusbar = view['statusbar']
        if self.statusbar is not None:
            self.status_cid = self.statusbar.get_context_id(self.__class__.__name__)

    def push_status_msg(self, msg, cid=None):
        if cid is not None:
            cid = self.statusbar.get_context_id(cid)
        else:
            cid = self.status_cid
        if cid is not None:
            self.statusbar.push(cid, msg)
    def pop_status_msg(self, cid=None):
        if cid is not None:
            cid = self.statusbar.get_context_id(cid)
        else:
            cid = self.status_cid
        if cid is not None:
            self.statusbar.pop(cid)

    def register_view(self, view):
        if self.model is not None:
            return Controller.register_view(self, view)
        else:
            return None

class DialogController(BaseController):
    
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.view.hide()
        return True
        
    def on_keypress(self, widget, event) :
		if event.keyval == gtk.keysyms.Escape :
            self.on_cancel()
			return True
        
    def on_window_edit_dialog_delete_event(self, event, args=None):
        self.on_cancel()
        return True #do not propagate
        
    def on_cancel(self):
        self.view.hide()

class ChildController(BaseController):

    def __init__(self, *args, **kwargs):
        #strip parent from args:
        if "parent" in kwargs:
            self.cparent = kwargs["parent"]
            del kwargs["parent"]
        BaseController.__init__(self, *args, **kwargs)
        
class HasObjectTreeview():

    def get_selected_object(self, tv):
        objects = HasObjectTreeview.get_selected_objects(self, tv)
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
            model, paths = selection.get_selected_rows()
            return paths
        return None
        
    def get_all_objects(self, tv):
        return tv.get_model().get_raw_model_data()
        
    def set_selected_paths(self, tv, paths):
        selection = tv.get_selection()
        selection.unselect_all()
        for path in paths:
            selection.select_path(path)

class ObjectListStoreMixin(HasObjectTreeview):

    model_property_name = ""
    edit_controller = None
    edit_view = None
    columns = [ ("Object name", 0) ]
    delete_msg = "Deleting objects is irreverisble!\nAre You sure you want to continue?"

    def __init__(self, model_property_name="", columns=[], delete_msg=""):
        self.model_property_name = model_property_name or self.model_property_name
        self.columns = columns or self.columns
        self.delete_msg = delete_msg or self.delete_msg

    @property
    def liststore(self):
        if self.model!=None:
            return getattr(self.model, self.model_property_name)
        else:
            return None

    def get_new_edit_view(self, obj):
        if obj == None:
            return self.view.none_view
        else:
            raise NotImplementedError, "Unsupported object type; subclasses of %s need to override this method for objects not equalling None!" % type(self)
        
    def get_new_edit_controller(self, obj, view, parent=None):
        if obj == None:
            return None
        else:
            raise NotImplementedError, "Unsupported object type; subclasses of %s need to override this method for objects not equalling None!" % type(self)
    
    def edit_object(self, obj):
        self.edit_view = self.get_new_edit_view(obj)
        self.edit_controller =  self.get_new_edit_controller(obj, self.view.set_edit_view(self.edit_view), parent=self.parent)
        return True

    def register_adapters(self):
        if self.model is not None:
            # connects the treeview to the liststore
            tv = self.view['edit_objects_treeview']
            tv.set_model(self.liststore)
            #tv.connect('button-press-event', self.phases_tv_button_press)

            sel = tv.get_selection()
            sel.set_mode(gtk.SELECTION_MULTIPLE)
            sel.connect('changed', self.objects_tv_selection_changed)

            #reset:
            for col in tv.get_columns():
                tv.remove_column(col)

            for name, col in self.columns:
                rend = gtk.CellRendererText()
                col = gtk.TreeViewColumn(name, rend, text=col)
                col.set_resizable(False)
                col.set_expand(False)
                tv.append_column(col)
            
            self.set_object_sensitivities(False) #FIXME
        # we can now edit 'nothing':
        self.edit_object(None)

    def set_object_sensitivities(self, value):
        if self.view.edit_view != None:
            self.view.edit_view.get_top_widget().set_sensitive(value)
        self.view["button_del_object"].set_sensitive(value)
        self.view["button_save_object"].set_sensitive(value)

    def get_selected_object(self):
        return HasObjectTreeview.get_selected_object(self, self.view['edit_objects_treeview'])
        
    def get_selected_objects(self):
        return HasObjectTreeview.get_selected_objects(self, self.view['edit_objects_treeview'])

    def get_all_objects(self):
        return HasObjectTreeview.get_all_objects(self, self.view['edit_objects_treeview'])

    def select_object(self, obj, unselect_all=True):
        selection = self.view['edit_objects_treeview'].get_selection()
        if unselect_all: selection.unselect_all()
        selection.select_path(self.liststore.on_get_path(obj))
        
    def select_objects(self, objs):
        for obj in objs: self.select_object(obj, False)
        
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def objects_tv_selection_changed(self, selection):        
        obj = self.get_selected_object()
        objs = self.get_selected_objects()
        self.set_object_sensitivities((obj!=None or objs!=None))
        if self.edit_controller==None or obj!=self.edit_controller.model:
            self.edit_object(obj)

    def on_load_object_clicked(self, event):
        raise NotImplementedError

    def on_save_object_clicked(self, event):
        raise NotImplementedError

    def on_add_object_clicked(self, event):
        raise NotImplementedError

    def on_del_object_clicked(self, event, del_callback=None, callback=None):
        tv = self.view['edit_objects_treeview']
        selection = tv.get_selection()
        if selection.count_selected_rows() >= 1:
            def delete_objects(dialog):
                for obj in self.get_selected_objects():
                    if callable(del_callback):
                        del_callback(obj)
                    else:
                        self.liststore.remove_item(obj)
                    if callable(callback): callback(obj)
                self.set_object_sensitivities(False)
                self.edit_object(None)
            self.run_confirmation_dialog(message=self.delete_msg, on_accept_callback=delete_objects, parent=self.view.get_top_widget())

        
class ObjectListStoreController(DialogController, ObjectListStoreMixin):
    title="Edit Dialog"
  
    def __init__(self, model, view,
                 spurious=False, auto_adapt=False, parent=None,
                 model_property_name="", columns=[], delete_msg="", title=""):
        DialogController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt, parent=parent)
        ObjectListStoreMixin.__init__(self, model_property_name=model_property_name, columns=columns, delete_msg=delete_msg)        
        self.title = title or self.title
        view.set_title(self.title)
        
    def register_adapters(self):
        ObjectListStoreMixin.register_adapters(self)
            
class ChildObjectListStoreController(ChildController, ObjectListStoreMixin):
  
    def __init__(self, model, view,
                 spurious=False, auto_adapt=False, parent=None,
                 model_property_name="", columns=[], delete_msg=""):
        ChildController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt, parent=parent)
        ObjectListStoreMixin.__init__(self, model_property_name=model_property_name, columns=columns, delete_msg=delete_msg)
        
    def register_adapters(self):
        ObjectListStoreMixin.register_adapters(self)

def get_color_val(widget):
    c = widget.get_color()
    return "#%02x%02x%02x" % (int(c.red_float*255), int(c.green_float*255), int(c.blue_float*255))
