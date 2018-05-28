# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

#TODO make this gtk agnostic

from pkg_resources import resource_filename # @UnresolvedImport
import gi
gi.require_version('Gtk', '3.0')  # @UndefinedVariable
from gi.repository import GdkPixbuf  # @UnresolvedImport

def get_icon_list():
    return [
        GdkPixbuf.Pixbuf.new_from_file(resource_filename(__name__, "icons/pyxrd_icon_16x16.png")), #@UndefinedVariable 
        GdkPixbuf.Pixbuf.new_from_file(resource_filename(__name__, "icons/pyxrd_icon_24x24.png")), #@UndefinedVariable
        GdkPixbuf.Pixbuf.new_from_file(resource_filename(__name__, "icons/pyxrd_icon_32x32.png")), #@UndefinedVariable
        GdkPixbuf.Pixbuf.new_from_file(resource_filename(__name__, "icons/pyxrd_icon_48x48.png")), #@UndefinedVariable
        GdkPixbuf.Pixbuf.new_from_file(resource_filename(__name__, "icons/pyxrd_icon_64x64.png")), #@UndefinedVariable
        GdkPixbuf.Pixbuf.new_from_file(resource_filename(__name__, "icons/pyxrd_icon_128x128.png")) #@UndefinedVariable
    ]
