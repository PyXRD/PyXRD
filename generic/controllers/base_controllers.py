# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os
import gtk

from gtkmvc import Controller

from .utils import retrieve_lowercase_extension
from handlers import widget_handlers

class DialogMixin():
    """
        Generic mixin that provides some functions and methods for handling
        dialogs, e.g. information, warnings, opening & saving files, ...
        
        Attributes:
            suggest_folder: the path at which the file dialogs are opened
            accept_responses: a list of GtkResponseCodes that 'accept' the action 
                of the dialog
            file_filters: A list of two-tuples containing the description of the
                file format and the file extensions 'glob' pattern.
    """

    file_filters = []
    suggest_folder = os.path.expanduser('~')

    accept_responses = (
        gtk.RESPONSE_ACCEPT,
        gtk.RESPONSE_YES,
        gtk.RESPONSE_APPLY,
        gtk.RESPONSE_OK
    )

    def extract_filename(self, dialog, filters=None):
        """ Extracts the selected filename from a gtk.Dialog """
        glob = self.get_selected_glob(dialog.get_filter(), filters=filters)
        filename = self._adjust_filename(dialog.get_filename(), glob)
        dialog.set_filename(filename)
        return filename

    def _adjust_filename(self, filename, glob):
        """ Adjusts a given filename so it ends with the proper extension """
        if glob:
            extension = glob[1:]
            if filename[len(filename) - len(extension):].lower() != extension.lower():
                filename = "%s%s" % (filename, glob[1:])
        return filename

    def get_selected_glob(self, filter, filters=None):
        """ """
        selected_name = filter.get_name()
        for fltr in (filters or self.file_filters):
            try:
                name, globs = fltr
            except TypeError: # filter is not a tuple, perhaps it is a FileFilter from a parser
                parser = fltr.get_data("parser")
                name, globs = parser.description, parser.extensions
            if selected_name == name:
                if len(globs) and globs[0] != "*.*":
                    return retrieve_lowercase_extension(globs[0])
                else:
                    return None

    def _get_object_file_filters(self, filters=None):
        filters = filters or self.file_filters
        for obj in filters:
            if isinstance(obj, gtk.FileFilter):
                yield obj
            else:
                name, re = obj
                ffilter = gtk.FileFilter()
                ffilter.set_name(name)
                if isinstance(re, (str, unicode)):
                    ffilter.add_pattern(re)
                else:
                    for expr in re:
                        ffilter.add_pattern(expr)
                yield ffilter

    def run_dialog(self,
            dialog, on_accept_callback=None, on_reject_callback=None, destroy=True):
        response = dialog.run()
        retval = None
        if response in self.accept_responses and on_accept_callback is not None:
            retval = on_accept_callback(dialog)
        elif on_reject_callback is not None:
            retval = on_reject_callback(dialog)
        if destroy:
            dialog.destroy()
        else:
            dialog.hide()
        return retval

    ############################################################################
    def get_file_dialog(self, action, title,
            parent=None, suggest_name=None, suggest_folder=None,
            extra_widget=None, multiple=False, filters=None):
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
        DialogMixin.suggest_folder = suggest_folder or DialogMixin.suggest_folder
        dialog.set_current_folder(DialogMixin.suggest_folder)
        for fltr in self._get_object_file_filters(filters):
            dialog.add_filter (fltr)
        return dialog

    def run_file_dialog(self, action, title,
            on_accept_callback, on_reject_callback=None,
            parent=None, suggest_name=None, suggest_folder=None,
            extra_widget=None, multiple=False, filters=None):
        dialog = self.get_file_dialog(action, title,
            parent=parent, suggest_name=suggest_name, suggest_folder=suggest_folder,
            extra_widget=extra_widget, multiple=multiple, filters=filters)
        return self.run_dialog(dialog, on_accept_callback, on_reject_callback)
    ############################################################################

    ############################################################################
    def get_save_dialog(self, title, parent=None,
            suggest_name=None, suggest_folder=None,
            extra_widget=None, filters=None):
        return self.get_file_dialog(
            gtk.FILE_CHOOSER_ACTION_SAVE, title, parent,
            suggest_name, suggest_folder, extra_widget,
            multiple=False, filters=filters)

    def run_save_dialog(self, title,
            on_accept_callback, on_reject_callback=None,
            parent=None, suggest_name=None, suggest_folder=None,
            extra_widget=None, filters=None):
        dialog = self.get_save_dialog(title, parent,
            suggest_name, suggest_folder,
            extra_widget, filters)
        return self.run_dialog(dialog, on_accept_callback, on_reject_callback)
    ############################################################################

    ############################################################################
    def get_load_dialog(self, title, parent=None,
            suggest_name=None, suggest_folder=None,
            extra_widget=None, multiple=False, filters=None):
        return self.get_file_dialog(
            gtk.FILE_CHOOSER_ACTION_OPEN, title, parent,
            suggest_name, suggest_folder, extra_widget,
            multiple=multiple, filters=filters)

    def run_load_dialog(self,
            title, on_accept_callback, on_reject_callback=None, parent=None,
            suggest_name=None, suggest_folder=None, extra_widget=None,
            multiple=False, filters=None):
        dialog = self.get_load_dialog(title, parent,
            suggest_name, suggest_folder,
            extra_widget, multiple=multiple, filters=filters)
        return self.run_dialog(dialog, on_accept_callback, on_reject_callback)
    ############################################################################

    ############################################################################
    def get_message_dialog(self, message, type, buttons=gtk.BUTTONS_YES_NO, parent=None):
        dialog = gtk.MessageDialog(
                    parent=parent,
                    flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                    type=type,
                    buttons=buttons)
        dialog.set_markup(message)
        return dialog

    def get_confirmation_dialog(self, message, parent=None):
        return self.get_message_dialog(message, gtk.MESSAGE_WARNING, parent=parent)

    def run_confirmation_dialog(self, message,
            on_accept_callback, on_reject_callback=None, parent=None):
        dialog = self.get_confirmation_dialog(message, parent=parent)
        return self.run_dialog(dialog, on_accept_callback, on_reject_callback)

    def get_information_dialog(self, message, parent=None):
        return self.get_message_dialog(message, gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK, parent=parent)

    def run_information_dialog(self, message,
            on_accept_callback=None, on_reject_callback=None, parent=None):
        dialog = self.get_information_dialog(message, parent)
        return self.run_dialog(dialog, on_accept_callback, on_reject_callback)
    ############################################################################


class BaseController (Controller, DialogMixin):

    file_filters = ("All Files", "*.*")
    widget_handlers = {} # handlers can be string representations of a class method
    auto_adapt = True
    auto_adapt_included = None
    auto_adapt_excluded = None

    @property
    def statusbar(self):
        if self.parent != None:
            return self.parent.statusbar
        elif self.view != None:
            return self.view['statusbar']
        else:
            return None

    @property
    def status_cid(self):
        if self.statusbar != None:
            return self.statusbar.get_context_id(self.__class__.__name__)
        else:
            return None

    def __init__(self, model, view, spurious=False, auto_adapt=None, parent=None):
        self.parent = parent
        auto_adapt = auto_adapt if auto_adapt != None else self.auto_adapt
        Controller.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt)

    @staticmethod
    def status_message(message, cid=None):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                self.push_status_msg(message, cid)
                res = func(self, *args, **kwargs)
                self.pop_status_msg(cid)
                return res
            return wrapper
        return decorator

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

    def _find_widget_match(self, prop_name):
        """
            Checks if the view has defined a 'widget_format' attribute.
            If so, it uses this format the search for the widget in the view,
            if not it takes the first widget with a name ending with the
            property name.
            Will also try to add certain widgets to the view if they're not
            present.
        """

        widget_name = None
        widget_format = getattr(self.view, 'widget_format', "%s")

        if widget_format:
            widget_name = widget_format % prop_name
            if not widget_name in self.view:
                intel = self.model.get_prop_intel_by_name(prop_name)
                if intel != None and intel.widget_type == 'scale':
                    self.view.add_scale_widget(intel, widget_format=widget_format)
        else:
            for wid_name in self.view:
                if wid_name.lower().endswith(prop_name.lower()):
                    widget_name = wid_name
                    break

        return widget_name

    def _get_handler_list(self):
        # Add default widget handlers:
        local_handlers = {}
        local_handlers.update(widget_handlers)

        # Override with class instance widget handlers:
        for widget_type, handler in self.widget_handlers.iteritems():
            if isinstance(handler, basestring):
                self.widget_handlers[widget_type] = getattr(self, handler)
        local_handlers.update(self.widget_handlers)
        return local_handlers

    def __create_adapters__(self, prop_name, wid_name):
        """
            Slightly modified version that passes the property intel and widget
            name to a (custom) 'handler' that returns the actual adapter class.
        """
        intel = self.model.get_prop_intel_by_name(prop_name)
        try:
            if intel == None: # if no intel is present, we can't be smarter...
                return super(BaseController, self).__create_adapters__(prop_name, wid_name)
            else:
                if intel.has_widget:

                    wid = self.view[wid_name]
                    if wid == None:
                        raise ValueError("Widget '%s' not found" % wid_name)

                    local_handlers = self._get_handler_list()

                    handler = local_handlers.get(intel.widget_type)
                    ad = handler(self, intel, wid)

                    return [ad]
                else:
                    return []
        except:
            print self, prop_name, wid_name
            raise

    pass # end of class

class DialogController(BaseController):
    """
        Simple controller which has a DialogView subclass instance as view.
    """

    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_btn_ok_clicked(self, event):
        self.on_cancel()
        return True

    def on_keypress(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.on_cancel()
            return True

    def on_window_edit_dialog_delete_event(self, event, args=None):
        self.on_cancel()
        return True # do not propagate

    def on_cancel(self):
        self.view.hide()
