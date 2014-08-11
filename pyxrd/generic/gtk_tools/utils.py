# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk, gobject

def convert_string_to_gdk_color_int(color):
    """
        Converts a string hexadecimal color description to an integer that can
        be used by gdk functions.
    """
    color = gtk.gdk.color_parse(color) # @UndefinedVariable
    return (int(color.red_float * 255) << 24) + (int(color.green_float * 255) << 16) + (int(color.blue_float * 255) << 8) + 255

def run_when_idle(func):
    """
        Decorator that can be used to run certain methods on the main GTK loop
        whenever it's idle.
    """
    def callback(*args):
        gobject.idle_add(func, *args)
    return callback