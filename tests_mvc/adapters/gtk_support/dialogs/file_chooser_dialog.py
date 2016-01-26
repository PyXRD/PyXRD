# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2016 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
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

import unittest

from mvc.adapters.gtk_support.dialogs.file_chooser_dialog import FileChooserDialog

from .file_chooser_dialog_args import get_file_chooser_kwags
from mock.mock import Mock

__all__ = [
    'FileChooserDialogTest',
]

class FileChooserDialogTest(unittest.TestCase):

    def setUp(self):
        self.kwargs = get_file_chooser_kwags()
        self.dialog = FileChooserDialog(**self.kwargs)


    def tearDown(self):
        pass


    def test_file_dialog_selected_globs(self):
        
        # Set filter:
        filter = self.dialog.list_filters()[0] #this is a *.txt filter, at least it should be... @ReservedAssignment
        self.dialog.set_filter(filter)
        
        #Act        
        sel_globs = self.dialog.selected_globs
        
        #Assert
        self.assertEqual(filter.get_name(), "Text File")
        self.assertEqual(sel_globs, ["*.txt"])
        
        

    def test_file_dialog_applies_filename_filters(self):
        
        no_ext_name = "test name without extension"
        
        # Set filter:
        filter = self.dialog.list_filters()[0] #this is a *.txt filter, at least it should be... @ReservedAssignment
        self.dialog.set_filter(filter)
        # Mock current filename
        self.dialog.get_filename = Mock(return_value=no_ext_name)
        
        # Assert we are working with the filter we expect
        self.assertEqual(filter.get_name(), "Text File")
        
        # Assert name is changed correctly
        self.assertEqual("%s.txt" % no_ext_name, self.dialog.filename)
        self.dialog.get_filename.assert_called_once_with()

if __name__ == "__main__":
    unittest.main()