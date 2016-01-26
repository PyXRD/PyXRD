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

from .utils import adjust_filename_to_globs, retrieve_lowercase_extension, run_dialog
import os

class FileChooserDialog(gtk.FileChooserDialog):
   
    accept_responses = (
        gtk.RESPONSE_ACCEPT, # @UndefinedVariable
        gtk.RESPONSE_YES, # @UndefinedVariable
        gtk.RESPONSE_APPLY, # @UndefinedVariable
        gtk.RESPONSE_OK # @UndefinedVariable
    )
   
    @property
    def parser(self):
        return self.get_filter().get_data("parser")
   
    @property
    def filename(self):
        """ Extracts the selected filename from a gtk.Dialog """
        filename = adjust_filename_to_globs(self.get_filename(), self.selected_globs)
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
                    parser = fltr.get_data("parser")
                    name, globs = parser.description, parser.extensions
                if selected_name == name:
                    if len(globs) and globs[0] != "*.*":
                        return [retrieve_lowercase_extension(glob) for glob in globs]
                    else:
                        return None
   
    def __init__(self, title, action, parent=None, buttons=None,
            suggest_name=None, suggest_folder=os.path.expanduser('~'),
            extra_widget=None, filters=[],
            multiple=False, confirm_overwrite=True):
        super(FileChooserDialog, self).__init__(
            title=title, action=action, parent=parent, buttons=buttons
        )
        
        # Multiple files are allowed or not:
        self.set_select_multiple(multiple)
        
        # Ask before overwriting yes/no
        self.set_do_overwrite_confirmation(confirm_overwrite)
        
        # Extra widget packed at the bottom:
        if extra_widget:
            self.set_extra_widget(extra_widget)
        
        # Set suggested file name
        if suggest_name:
            self.set_current_name(suggest_name)
            
        # Set suggested folder
        self.suggest_folder = suggest_folder
        if self.suggest_folder:
            self.set_current_folder(self.suggest_folder)
        
        # Add file filters
        self.filters = filters
        for fltr in self._get_object_file_filters(filters):
            self.add_filter (fltr)


    def _get_object_file_filters(self, filters=[]):
        """ Parses a list of textual file filter globs or gtk.FileFilter objects
         into gtk.FileFilter objects """ 
        for obj in filters:
            if isinstance(obj, gtk.FileFilter):
                yield obj
            else:
                # if not a gtk.FileFilter we assume it is a glob tuple
                name, re = obj
                ffilter = gtk.FileFilter()
                ffilter.set_name(name)
                if isinstance(re, (str, unicode)):
                    ffilter.add_pattern(re)
                else: # if not a single glob, assume an iterable is given
                    for expr in re:
                        ffilter.add_pattern(expr)
                yield ffilter
                
    #override
    def run(self, *args, **kwargs):
        return run_dialog(self, *args, **kwargs)
                
    pass #end of class