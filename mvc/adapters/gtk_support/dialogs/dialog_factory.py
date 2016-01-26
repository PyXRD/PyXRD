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

import gtk
from contextlib import contextmanager

from .message_dialog import MessageDialog
from .file_chooser_dialog import FileChooserDialog

class DialogFactory(object):  
    
    # ------------------------------------------------------------
    #      File dialog creators
    # ------------------------------------------------------------
    
    @staticmethod
    def get_file_dialog(
            action, title, parent=None, 
            suggest_name=None, suggest_folder=None,
            extra_widget=None, filters=[],
            multiple=False, confirm_overwrite=True):
        """ Generic file dialog creator """
        return FileChooserDialog(
            title=title, parent=parent, action=action,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                     gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
            suggest_name=suggest_name, suggest_folder=suggest_folder,
            extra_widget=extra_widget, multiple=multiple, filters=filters)

    @staticmethod
    def get_save_dialog(
            title, parent=None, 
            suggest_name=None, suggest_folder=None,
            extra_widget=None, filters=[],
            confirm_overwrite=True):
        """ Save file dialog creator """
        # Forces save action
        # Does not allow selecting multiple files
        return DialogFactory.get_file_dialog(
            action=gtk.FILE_CHOOSER_ACTION_SAVE, title=title, parent=parent,
            suggest_name=suggest_name, suggest_folder=suggest_folder, 
            extra_widget=extra_widget, filters=filters,
            multiple=False, confirm_overwrite=confirm_overwrite)
    
    @staticmethod
    def get_load_dialog(
            title, parent=None, 
            suggest_name=None, suggest_folder=None,
            extra_widget=None, filters=[],
            multiple=True):
        """ Load file dialog creator """
        # Forces open action
        # Disables overwrite confirmation (doesn't matter really)
        return DialogFactory.get_file_dialog(
            action=gtk.FILE_CHOOSER_ACTION_OPEN, title=title, parent=parent,
            suggest_name=suggest_name, suggest_folder=suggest_folder, 
            extra_widget=extra_widget, filters=filters,
            multiple=multiple, confirm_overwrite=False)

    # ------------------------------------------------------------
    #      Message dialog creators
    # ------------------------------------------------------------
    @staticmethod
    def get_message_dialog(message, type, buttons=gtk.BUTTONS_YES_NO, parent=None):  # @ReservedAssignment
        """ Generic message dialog creator """
        return MessageDialog(
            message=message,
            parent=parent,
            type=type,
            flags=gtk.DIALOG_DESTROY_WITH_PARENT,
            buttons=buttons)

    @staticmethod
    def get_confirmation_dialog(message, parent=None):
        """ Confirmation dialog creator """
        return DialogFactory.get_message_dialog(
            message,
            type=gtk.MESSAGE_WARNING,
            parent=parent            
        )

    @staticmethod
    def get_information_dialog(message, parent=None):
        """ Information dialog creator """
        return DialogFactory.get_message_dialog(
            message,
            type=gtk.MESSAGE_INFO,
            buttons=gtk.BUTTONS_OK,
            parent=parent
        )
        
    @staticmethod
    def get_error_dialog(message, parent=None):
        """ Error dialog creator """
        return DialogFactory.get_message_dialog(
            message,
            typ=gtk.MESSAGE_ERROR,
            buttons=gtk.BUTTONS_OK,
            parent=parent
        )

    # ------------------------------------------------------------
    #      Custom dialog creator
    # ------------------------------------------------------------
    def get_custom_dialog(self, content, parent=None):
        window = gtk.Window()
        window.set_border_width(10)
        window.set_modal(True)
        window.set_transient_for(parent)
        window.connect('delete-event', lambda widget, event: True)
        window.add(content)
        return window

    pass #end of class


    @staticmethod
    @contextmanager
    def error_dialog_handler(message, parent=None, reraise=True):
        """ Context manager that can be used to wrap error-prone code. If an error
        is risen, a dialog will inform the user, optionally the error can be re-raised """
        try:
            yield
        except any, msg:
            DialogFactory.get_error_dialog(
               message.format(msg), parent=parent
            ).run()
            if reraise: raise # This should be handled by the default UI bug dialog
