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

from mvc.adapters.gtk_support.dialogs.dialog_factory import DialogFactory
from .file_chooser_dialog_args import get_file_chooser_kwags

__all__ = [
    'DialogFactoryTest',
]

class DialogFactoryTest(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_get_file_dialog(self):
        kwargs = get_file_chooser_kwags()
        dialog = DialogFactory.get_file_dialog(**kwargs)

        self.assertEqual(dialog.get_action(), kwargs["action"], "Action attribute is not set correctly")
        self.assertEqual(dialog.get_title(), kwargs["title"], "Title attribute is not set correctly")
        self.assertEqual(dialog.get_parent(), kwargs["parent"], "Parent window is not set correctly")
        self.assertEqual(dialog.get_current_name(), kwargs["current_name"], "Current name attribute is not set correctly")
        self.assertEqual(dialog.get_current_folder(), kwargs["current_folder"], "Current folder attribute is not set correctly")
        self.assertEqual(dialog.get_extra_widget(), kwargs["extra_widget"], "Extra widget attribute is not set correctly")
        self.assertEqual(dialog.filters, kwargs["filters"], "Filters attribute is not set correctly")
        self.assertEqual(dialog.get_select_multiple(), kwargs["multiple"], "Multiple attribute is not set correctly")
        self.assertEqual(dialog.get_do_overwrite_confirmation(), kwargs["confirm_overwrite"], "Confirm overwrite attribute is not set correctly")

if __name__ == "__main__":
    unittest.main()
