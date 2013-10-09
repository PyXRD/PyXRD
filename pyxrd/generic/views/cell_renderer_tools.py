# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

renderer_map = {
    'text': gtk.CellRendererText,
    'accel': gtk.CellRendererAccel,
    'combo': gtk.CellRendererCombo,
    'spin': gtk.CellRendererSpin,
    'pixbuf': gtk.CellRendererPixbuf,
    'progress': gtk.CellRendererProgress,
    'spinner': gtk.CellRendererSpinner,
    'toggle': gtk.CellRendererToggle,
}

def get_default_renderer(type, **kwargs):
    """
        Creates a CellRendere of type 'type' and sets any attributes passed with
        the key-word arguments. Underscores in variable names are replaced with
        dashes in the proces.
    """
    rend = renderer_map.get(type, type)()
    for key, val in kwargs.iteritems():
        rend.set_property(key.replace("_", "-"), val)
    return rend
    
def parse_callback(callback, reduce=True):
    """
        Parses callbacks for CellRenderers: it splits the 
        callback from its arguments if present. Additionally this method will 
        not create singleton argument lists, but pass them as a single argument.
        
        Returns the callback and its argument(s) (or an empty tuple)
    """
    args = tuple()
    try:
        callback, args = callback
    except TypeError, ValueError:
        pass
    #deconvolve things:
    if reduce and len(args) == 1: args = args[0]
    return callback, args
    
def parse_kwargs(**kwargs):
    """
        Parses key-word arguments.
        It checks for the presence of key-words ending with '_col', these are
        popped and stored in a seperate dictionary, as they are to be passed
        to the constructor of the actual column or combobox (attribute mappings)
        In addition it sets a number of default attributes for the CellRenderer.
        
        Returns a tuple containing a dict with the CellRenderer attributes and a
        dict with the TreeViewColumn attribute mappings
    """
    kwargs["xalign"] = kwargs.get("xalign", 0.5)
    kwargs["yalign"] = kwargs.get("yalign", 0.5)
    
    col_attrs = dict()
    for key, value in dict(kwargs).iteritems():
        if key.endswith("_col"):
            col_attrs[key[:-4]] = value
            kwargs.pop(key)
    return kwargs, col_attrs
