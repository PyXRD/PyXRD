# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

from cell_renderer_tools import get_default_renderer, parse_callback, parse_kwargs

def add_renderer_with_attrs(combo, col_attrs, rend):
    combo.pack_start(rend, True)
    for attr, val in col_attrs.iteritems():
        combo.add_attribute(rend, attr, val)

def add_combo_text_column(combo,
        data_func=None,
        **kwargs):
    kwargs["xalign"] = kwargs.get("xalign", 0.0)
    kwargs, col_attrs = parse_kwargs(**kwargs)
    rend = get_default_renderer('text', **kwargs)
    add_renderer_with_attrs(combo, col_attrs, rend)
    if data_func!=None:
        callback, args = parse_callback(data_func)
        combo.set_cell_data_func(rend, callback, args)
    return rend
