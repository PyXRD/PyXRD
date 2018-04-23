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

import gi
gi.require_version('Gtk', '3.0')  # @UndefinedVariable
from gi.repository import Gtk  # @UnresolvedImport

from .utils import run_dialog

class MessageDialog(Gtk.MessageDialog):

    accept_responses = (
        Gtk.ResponseType.ACCEPT, # @UndefinedVariable
        Gtk.ResponseType.YES, # @UndefinedVariable
        Gtk.ResponseType.APPLY, # @UndefinedVariable
        Gtk.ResponseType.OK # @UndefinedVariable
    )

    def __init__(self,
             message, parent=None,
             type=Gtk.MessageType.INFO,  # @ReservedAssignment
             flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
             buttons=Gtk.ButtonsType.NONE,
             persist=False,
             title=None):
        super(MessageDialog, self).__init__(
            parent=parent,
            type=type,
            flags=flags,
            buttons=buttons)
        self.persist = persist
        self.set_markup(message)
        if title is not None:
            self.set_title(title)

    #override
    def run(self, *args, **kwargs):
        kwargs['destroy'] = not self.persist
        return run_dialog(self, *args, **kwargs)

    pass #end of class
