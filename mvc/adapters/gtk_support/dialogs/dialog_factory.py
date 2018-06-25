# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#
#  mvc is a framework derived from the original pygtkmvc framework
#  hosted at: <http://sourceforge.net/projects/pygtkmvc/>
#
#  mvc is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  mvc is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor,
#  Boston, MA 02110, USA.
#  -------------------------------------------------------------------------

import sys, html
from contextlib import contextmanager

import gi
from mvc.adapters.gtk_support.widgets.threaded_task_box import ThreadedTaskBox
from mvc.support.gui_loop import run_when_idle, add_timeout_call,\
    remove_timeout_call
from mvc.support.cancellable_thread import CancellableThread
gi.require_version('Gtk', '3.0')  # @UndefinedVariable
from gi.repository import Gtk, GObject  # @UnresolvedImport

from .message_dialog import MessageDialog
from .file_chooser_dialog import FileChooserDialog

class DialogFactory(object):

    # ------------------------------------------------------------
    #      File dialog creators
    # ------------------------------------------------------------

    @staticmethod
    def get_file_dialog_from_context(context, parent=None, **kwargs):
        return FileChooserDialog(context, parent=parent, **kwargs)

    @staticmethod
    def get_file_dialog(
            action, title, parent=None,
            current_name=None, current_folder=None,
            extra_widget=None, filters=[],
            multiple=False, confirm_overwrite=True, persist=False):
        """ Generic file dialog creator """
        return FileChooserDialog(
            title=title, action=action, parent=parent,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                     Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT),
            current_name=current_name, current_folder=current_folder,
            extra_widget=extra_widget, filters=filters,
            multiple=multiple, confirm_overwrite=confirm_overwrite, persist=persist
        )

    @staticmethod
    def get_save_dialog(
            title, parent=None,
            current_name=None, current_folder=None,
            extra_widget=None, filters=[],
            confirm_overwrite=True, persist=False):
        """ Save file dialog creator """
        # Forces save action
        # Does not allow selecting multiple files
        return DialogFactory.get_file_dialog(
            action=Gtk.FileChooserAction.SAVE, title=title, parent=parent,
            current_name=current_name, current_folder=current_folder,
            extra_widget=extra_widget, filters=filters,
            multiple=False, confirm_overwrite=confirm_overwrite, persist=persist)

    @staticmethod
    def get_load_dialog(
            title, parent=None,
            current_name=None, current_folder=None,
            extra_widget=None, filters=[],
            multiple=True, persist=False):
        """ Load file dialog creator """
        # Forces open action
        # Disables overwrite confirmation (doesn't matter really)
        return DialogFactory.get_file_dialog(
            action=Gtk.FileChooserAction.OPEN, title=title, parent=parent,
            current_name=current_name, current_folder=current_folder,
            extra_widget=extra_widget, filters=filters,
            multiple=multiple, confirm_overwrite=False, persist=persist)

    # ------------------------------------------------------------
    #      Message dialog creators
    # ------------------------------------------------------------
    @staticmethod
    def get_message_dialog(message, type, buttons=Gtk.ButtonsType.YES_NO, persist=False, parent=None, title=None):  # @ReservedAssignment
        """ Generic message dialog creator """
        return MessageDialog(
            message=message,
            parent=parent,
            type=type,
            flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
            buttons=buttons,
            persist=persist,
            title=title)

    @staticmethod
    def get_confirmation_dialog(message, persist=False, parent=None, title=None):
        """ Confirmation dialog creator """
        return DialogFactory.get_message_dialog(
            message,
            parent=parent,
            type=Gtk.MessageType.WARNING,
            persist=persist,
            title=title
        )

    @staticmethod
    def get_information_dialog(message, persist=False, parent=None, title=None):
        """ Information dialog creator """
        return DialogFactory.get_message_dialog(
            message,
            parent=parent,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            persist=persist,
            title=title
        )

    @staticmethod
    def get_error_dialog(message, persist=False, parent=None, title=None):
        """ Error dialog creator """
        return DialogFactory.get_message_dialog(
            message,
            parent=parent,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            persist=persist,
            title=title
        )

    # ------------------------------------------------------------
    #      Custom dialog creator
    # ------------------------------------------------------------
    @staticmethod
    def get_custom_dialog(content, parent=None):
        window = Gtk.Window()
        window.set_border_width(10)
        window.set_modal(True)
        window.set_transient_for(parent)
        window.connect('delete-event', lambda widget, event: True)
        window.add(content)
        return window

    pass #end of class


    @staticmethod
    @contextmanager  
    def error_dialog_handler(message, parent=None, title=None, reraise=True, print_tb=True):
        """ Context manager that can be used to wrap error-prone code. If an error
        is risen, a dialog will inform the user, optionally the error can be re-raised """
        try:
            yield
        except:
            msg = message.format(html.escape("%s" % sys.exc_info()[1]))
            DialogFactory.get_error_dialog(
               msg, title=title, parent=parent
            ).run()
            if reraise: raise # This should be handled by the default UI bug dialog
            elif print_tb:
                from traceback import print_exc
                print_exc()
                
    @staticmethod
    def get_progress_dialog(action, complete_callback=None, gui_message="Processing ...", toplevel=None):
        """
            Returns a callable that will show a progress dialog
            for the given action - which will be run in a different 
            thread from the GUI.
            The action is expected to take a single argument: `status_dict`
            which is used to format the gui_message (new-style formatting).
            toplevel is the top level window.
            complete_callback is called when the action has completed with
            its return value.
            When interrupted or cancelled by the user, the dialog just hides.  
        """
        def run_action_and_show_progress():

            taskgui = ThreadedTaskBox()
            window = DialogFactory.get_custom_dialog(
                 taskgui, parent=toplevel)

            # Status:
            status_dict = dict()

            # Task:
            def load_peak_thresholds(stop=None):
                action(status_dict)

            # Cancel & stop events:
            def on_interrupted(*args, **kwargs):
                window.hide()

            # Status label update:
            def gui_callback():
                taskgui.set_status(gui_message.format(**status_dict))
                return True
            add_timeout_call(250, gui_callback)

            # Complete event:
            @run_when_idle
            def on_complete(*args, **kwargs):
                remove_timeout_call(gui_callback)
                taskgui.stop()
                window.destroy()
                if callable(complete_callback):
                    complete_callback(*args, **kwargs)
                
            # Run thread:
            thread = CancellableThread(load_peak_thresholds, on_complete)
            thread.start()
            
            # Run task box:
            taskgui.connect("cancelrequested", on_interrupted)
            taskgui.connect("stoprequested", on_interrupted)
            taskgui.set_status("Loading ...")
            taskgui.start()
            window.show_all()

        return run_action_and_show_progress
