# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport
import gtk

def get_icon_list():
    return [
        gtk.gdk.pixbuf_new_from_file(resource_filename(__name__, "icons/pyxrd_icon_16x16.png")), #@UndefinedVariable
        gtk.gdk.pixbuf_new_from_file(resource_filename(__name__, "icons/pyxrd_icon_24x24.png")), #@UndefinedVariable
        gtk.gdk.pixbuf_new_from_file(resource_filename(__name__, "icons/pyxrd_icon_32x32.png")), #@UndefinedVariable
        gtk.gdk.pixbuf_new_from_file(resource_filename(__name__, "icons/pyxrd_icon_48x48.png")), #@UndefinedVariable
        gtk.gdk.pixbuf_new_from_file(resource_filename(__name__, "icons/pyxrd_icon_64x64.png")), #@UndefinedVariable
        gtk.gdk.pixbuf_new_from_file(resource_filename(__name__, "icons/pyxrd_icon_128x128.png")) #@UndefinedVariable
    ]
