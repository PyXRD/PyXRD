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

import os

import gtk
from pyxrd.generic.io.utils import get_case_insensitive_glob

def get_file_chooser_kwags():
    return dict(
        action=gtk.FILE_CHOOSER_ACTION_SAVE,
        title="The dialog title",
        parent=gtk.Window(),
        current_name="suggested_file_name",
        current_folder=os.path.expanduser("~"),
        extra_widget=gtk.Label("Test Label"),
        filters=[ ("Text File", get_case_insensitive_glob("*.txt")) ],
        multiple=False,
        confirm_overwrite=True
    )
