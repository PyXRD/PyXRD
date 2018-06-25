# coding=UTF-8
# ex:ts=4:sw=4r:et=on
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
from gi.repository import Gtk, GLib  # @UnresolvedImport

def add_idle_call(func, *args):
    source = GLib.MainContext.default().find_source_by_id(
        GLib.idle_add(func, *args, priority=GLib.PRIORITY_HIGH_IDLE))
    return source

def remove_source(source):
    return source.destroy()

def add_timeout_call(timeout, func, *args):
    source = GLib.MainContext.default().find_source_by_id(
        GLib.timeout_add(timeout, func, priority=GLib.PRIORITY_HIGH, *args))
    return source

def start_event_loop():
    return Gtk.main()

def stop_event_loop():
    return Gtk.main_quit()