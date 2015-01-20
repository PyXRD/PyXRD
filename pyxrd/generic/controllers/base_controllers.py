# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from contextlib import contextmanager
import os
import gtk

from mvc.controller import Controller

from pyxrd.generic.io.utils import retrieve_lowercase_extension

class DialogMixin(object):
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
        gtk.RESPONSE_ACCEPT, # @UndefinedVariable
        gtk.RESPONSE_YES, # @UndefinedVariable
        gtk.RESPONSE_APPLY, # @UndefinedVariable
        gtk.RESPONSE_OK # @UndefinedVariable
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
        """ Returns the extension glob corresponding to the selected filter """
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

        # Using an event prevents deadlocks, because we can return to the Main Loop
        def _dialog_response_cb(dialog, response):
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

        # Connect callback and present the dialog
        dialog.connect('response', _dialog_response_cb)
        dialog.set_modal(True)
        dialog.show()

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

    def get_error_dialog(self, message, parent=None):
        return self.get_message_dialog(message, gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, parent=parent)

    def run_error_dialog(self, message,
            on_accept_callback=None, on_reject_callback=None, parent=None):
        dialog = self.get_information_dialog(message, parent)
        return self.run_dialog(dialog, on_accept_callback, on_reject_callback)

    def get_custom_dialog(self, content, parent=None):
        window = gtk.Window()
        window.set_border_width(10)
        window.set_modal(True)
        window.set_transient_for(parent)
        window.connect('delete-event', lambda widget, event: True)
        window.add(content)
        return window

    @contextmanager
    def ui_error_handler(self, message):
        try:
            yield
        except:
            self.run_error_dialog(message, parent=self.view.get_top_widget())
            raise # This will be handled by the default UI bug dialog
    ############################################################################


class BaseController(Controller, DialogMixin):

    file_filters = ("All Files", "*.*")
    widget_handlers = {} # handlers can be string representations of a class method
    auto_adapt_included = None
    auto_adapt_excluded = None

    @property
    def statusbar(self):
        if self.parent is not None:
            return self.parent.statusbar
        elif self.view is not None:
            return self.view['statusbar']
        else:
            return None

    @property
    def status_cid(self):
        if self.statusbar is not None:
            return self.statusbar.get_context_id(self.__class__.__name__)
        else:
            return None

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

    pass #end of class
