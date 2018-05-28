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

from .utils import adjust_filename_to_globs, retrieve_lowercase_extension, run_dialog
import os

class FileChooserDialog(Gtk.FileChooserDialog):

    accept_responses = (
        Gtk.ResponseType.ACCEPT, # @UndefinedVariable
        Gtk.ResponseType.YES, # @UndefinedVariable
        Gtk.ResponseType.APPLY, # @UndefinedVariable
        Gtk.ResponseType.OK # @UndefinedVariable
    )

    persist = False

    @property
    def parser(self):
        try:
            return getattr(self.get_filter(), "parser")
        except AttributeError:
            return None

    @property
    def filename(self):
        """ Extracts the selected filename from a Gtk.Dialog """
        filename = super(FileChooserDialog, self).get_filename()
        if filename is not None:
            filename = adjust_filename_to_globs(filename, self.selected_globs)
            self.set_filename(filename)
        return filename

    @property
    def selected_globs(self):
        """ Returns the extension glob corresponding to the selected filter """
        fltr = self.get_filter() # THIS RETURNS NONE??
        if fltr is None:
            return None
        else:
            selected_name = fltr.get_name()
            for fltr in self.filters:
                try:
                    name, globs = fltr
                except TypeError: # filter is not a tuple, perhaps it is a FileFilter from a parser
                    parser = getattr(fltr, "parser")
                    name, globs = parser.description, parser.extensions
                if selected_name == name:
                    if len(globs) and globs[0] != "*.*":
                        return [retrieve_lowercase_extension(glob) for glob in globs]
                    else:
                        return None

    def __init__(self, title, action, parent=None, buttons=None,
            current_name=None, current_folder=os.path.expanduser('~'),
            extra_widget=None, filters=[],
            multiple=False, confirm_overwrite=True, persist=False):
        super(FileChooserDialog, self).__init__(
            title=title, action=action, parent=parent, buttons=buttons
        )
        self.update(
            multiple=multiple, confirm_overwrite=confirm_overwrite,
            extra_widget=extra_widget, filters=filters,
            current_name=current_name, current_folder=current_folder,
            persist=persist
        )

    def update(self, **kwargs):
        """ Updates the dialog with the given set of keyword arguments, 
            and then returns itself """
        if "title" in kwargs and kwargs["title"] is not None:
            self.set_title(kwargs.pop("title"))

        if "action" in kwargs and kwargs["action"] is not None:
            self.set_action(kwargs.pop("action"))

        if "parent" in kwargs and kwargs["parent"] is not None:
            self.set_parent(kwargs.pop("parent"))

        if "buttons" in kwargs:
            self.get_action_area().foreach(lambda w: w.destroy())
            self.add_buttons(*kwargs.pop("buttons"))

        # Multiple files are allowed or not:
        if "multiple" in kwargs:
            self.set_select_multiple(kwargs.pop("multiple"))

        # Ask before overwriting yes/no
        if "confirm_overwrite" in kwargs:
            self.set_do_overwrite_confirmation(kwargs.pop("confirm_overwrite"))

        # Extra widget packed at the bottom:
        if "extra_widget" in kwargs and kwargs["extra_widget"] is not None:
            self.set_extra_widget(kwargs.pop("extra_widget"))

        # Set suggested file name
        if "current_name" in kwargs and kwargs["current_name"] is not None:
            self.set_current_name(kwargs.pop("current_name"))

        # Set suggested folder
        if "current_folder" in kwargs and kwargs["current_folder"] is not None:
            self.set_current_folder(kwargs.pop("current_folder"))

        # Add file filters
        if "filters" in kwargs:
            # Clear old filters:
            for fltr in self.list_filters():
                self.remove_filter(fltr) 
            # Set new filters:
            self.filters = list(kwargs.pop("filters"))
            for fltr in self._get_object_file_filters(self.filters):
                self.add_filter(fltr)

        self.persist = kwargs.pop("persist", self.persist)

        return self

    def _get_object_file_filters(self, filters=[]):
        """ Parses a list of textual file filter globs or Gtk.FileFilter objects
         into Gtk.FileFilter objects """
        for obj in filters:
            if isinstance(obj, Gtk.FileFilter):
                yield obj
            else:
                # if not a Gtk.FileFilter we assume it is a glob tuple
                name, re = obj
                ffilter = Gtk.FileFilter()
                ffilter.set_name(name)
                if isinstance(re, str):
                    ffilter.add_pattern(re)
                else: # if not a single glob, assume an iterable is given
                    for expr in re:
                        ffilter.add_pattern(expr)
                yield ffilter

    #override
    def run(self, *args, **kwargs):
        kwargs['destroy'] = not self.persist
        return run_dialog(self, *args, **kwargs)

    pass #end of class
