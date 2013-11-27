# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

from cell_renderer_tools import get_default_renderer, parse_callback, parse_kwargs

class PyXRDTreeViewColumn(gtk.TreeViewColumn):
    """
        A custom TreeViewColumn that stores information about its attribute 
        mappings and provides acces to them with the get_col_attr function.
    """

    def __init__(self, title=None, cell_renderer=None, **kwargs):
        gtk.TreeViewColumn.__init__(self, title, cell_renderer)
        self._attrs = dict()
        self.set_attributes(cell_renderer, **kwargs)

    def set_attributes(self, cell_renderer, **kwargs):
        for key, val in kwargs.iteritems():
            self._attrs[key] = val
        gtk.TreeViewColumn.set_attributes(self, cell_renderer, **kwargs)

    def add_attribute(self, cell_renderer, attribute, column):
        self._attrs[attribute] = column
        gtk.TreeViewColumn.set_attributes(self, cell_renderer, attribute, column)

    def clear_attributes(self, cell_renderer):
        self._attrs = dict()
        gtk.TreeViewColumn.clear_attributes(self, cell_renderer)

    def get_col_attr(self, attr):
        return self._attrs.get(attr, -1)

def _get_default_column(title, rend,
        data_func=None,
        spacing=0,
        visible=True,
        resizable=True,
        sizing=0,
        fixed_width=-1,
        min_width=-1,
        max_width=-1,
        expand=True,
        clickable=False,
        alignment=0.0,
        reorderable=False,
        sort_column_id=-1,
        sort_indicator=False,
        sort_order=gtk.SORT_ASCENDING,
        col_attrs={}):
    """
        Creates a PyXRDTreeViewColumn using the arguments passed. Column 
        attribute mappings are to be passed as a single dict,
        not as key-word arguments.
    """
    col = PyXRDTreeViewColumn(title, rend, **col_attrs)
    if data_func is not None:
        callback, args = parse_callback(data_func)
        col.set_cell_data_func(rend, callback, args)
    col.set_spacing(spacing)
    col.set_visible(visible)
    col.set_resizable(resizable)
    col.set_sizing(sizing)
    if fixed_width >= 0:
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(fixed_width)
    else:
        col.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
    col.set_min_width(min_width)
    col.set_max_width(max_width)
    col.set_title(title)
    col.set_expand(expand)
    col.set_clickable(clickable)
    col.set_alignment(alignment)
    col.set_reorderable(reorderable)
    col.set_sort_column_id(sort_column_id)
    col.set_sort_indicator(sort_indicator)
    col.set_sort_order(sort_order)
    col.set_resizable(resizable)
    col.set_expand(expand)
    col.set_alignment(alignment)
    return col

def new_text_column(title,
        edited_callback=None,
        data_func=None,
        spacing=0,
        visible=True,
        resizable=True,
        sizing=0,
        fixed_width=-1,
        min_width=-1,
        max_width=-1,
        expand=True,
        clickable=False,
        alignment=None,
        reorderable=False,
        sort_column_id=-1,
        sort_indicator=False,
        sort_order=gtk.SORT_ASCENDING,
        **kwargs):
    """
        Creates a TreeViewColumn packed with a CellRendererText .
    """
    kwargs, col_attrs = parse_kwargs(**kwargs)
    alignment = alignment if alignment is not None else kwargs["xalign"]

    rend = get_default_renderer(gtk.CellRendererText, **kwargs)
    if edited_callback is not None:
        callback, args = parse_callback(edited_callback, reduce=False)
        rend.connect('edited', callback, *args)

    col = _get_default_column(
        title, rend,
        data_func=data_func,
        spacing=spacing,
        visible=visible,
        resizable=resizable,
        sizing=sizing,
        fixed_width=fixed_width,
        min_width=min_width,
        max_width=max_width,
        expand=expand,
        clickable=clickable,
        alignment=alignment,
        reorderable=reorderable,
        sort_column_id=sort_column_id,
        sort_indicator=sort_indicator,
        sort_order=sort_order,
        col_attrs=col_attrs)
    return col

def new_pb_column(title,
        data_func=None,
        spacing=0,
        visible=True,
        resizable=True,
        sizing=0,
        fixed_width=-1,
        min_width=-1,
        max_width=-1,
        expand=True,
        clickable=False,
        alignment=None,
        reorderable=False,
        sort_column_id=-1,
        sort_indicator=False,
        sort_order=gtk.SORT_ASCENDING,
        **kwargs):
    """
        Creates a TreeViewColumn packed with a CellRendererPixbuf.
    """
    kwargs, col_attrs = parse_kwargs(**kwargs)
    alignment = alignment if alignment is not None else kwargs["xalign"]

    rend = get_default_renderer(gtk.CellRendererPixbuf, **kwargs)

    col = _get_default_column(
        title, rend,
        data_func=data_func,
        spacing=spacing,
        visible=visible,
        resizable=resizable,
        sizing=sizing,
        fixed_width=fixed_width,
        min_width=min_width,
        max_width=max_width,
        expand=expand,
        clickable=clickable,
        alignment=alignment,
        reorderable=reorderable,
        sort_column_id=sort_column_id,
        sort_indicator=sort_indicator,
        sort_order=sort_order,
        col_attrs=col_attrs)
    return col

def new_toggle_column(title,
        data_func=None,
        toggled_callback=None,
        spacing=0,
        visible=True,
        resizable=True,
        sizing=0,
        fixed_width=-1,
        min_width=-1,
        max_width=-1,
        expand=True,
        clickable=False,
        alignment=None,
        reorderable=False,
        sort_column_id=-1,
        sort_indicator=False,
        sort_order=gtk.SORT_ASCENDING,
        **kwargs):
    """
        Creates a TreeViewColumn packed with a CellRendererToggle.
    """
    kwargs, col_attrs = parse_kwargs(**kwargs)
    alignment = alignment if alignment is not None else kwargs["xalign"]

    rend = get_default_renderer(gtk.CellRendererToggle, **kwargs)
    if toggled_callback is not None:
        callback, args = parse_callback(toggled_callback, reduce=False)
        rend.connect('toggled', callback, *args)

    col = _get_default_column(
        title, rend,
        data_func=data_func,
        spacing=spacing,
        visible=visible,
        resizable=resizable,
        sizing=sizing,
        fixed_width=fixed_width,
        min_width=min_width,
        max_width=max_width,
        expand=expand,
        clickable=clickable,
        alignment=alignment,
        reorderable=reorderable,
        sort_column_id=sort_column_id,
        sort_indicator=sort_indicator,
        sort_order=sort_order,
        col_attrs=col_attrs)
    return col

def new_combo_column(title,
        data_func=None,
        changed_callback=None,
        edited_callback=None,
        editing_started_callback=None,
        editing_canceled_callback=None,
        spacing=0,
        visible=True,
        resizable=True,
        sizing=0,
        fixed_width=-1,
        min_width=-1,
        max_width=-1,
        expand=True,
        clickable=False,
        alignment=None,
        reorderable=False,
        sort_column_id=-1,
        sort_indicator=False,
        sort_order=gtk.SORT_ASCENDING,
        **kwargs):
    """
        Creates a TreeViewColumn packed with a CellRendererCombo.
    """
    kwargs, col_attrs = parse_kwargs(**kwargs)
    alignment = alignment if alignment is not None else kwargs["xalign"]

    rend = get_default_renderer(gtk.CellRendererCombo, **kwargs)
    if changed_callback is not None:
        callback, args = parse_callback(changed_callback, reduce=False)
        rend.connect('changed', callback, *args)
    if edited_callback is not None:
        callback, args = parse_callback(edited_callback, reduce=False)
        rend.connect('edited', callback, *args)
    if editing_started_callback is not None:
        callback, args = parse_callback(editing_started_callback, reduce=False)
        rend.connect('editing-started', callback, *args)
    if editing_canceled_callback is not None:
        callback, args = parse_callback(editing_canceled_callback, reduce=False)
        rend.connect('editing-canceled', callback, *args)

    col = _get_default_column(
        title, rend,
        data_func=data_func,
        spacing=spacing,
        visible=visible,
        resizable=resizable,
        sizing=sizing,
        fixed_width=fixed_width,
        min_width=min_width,
        max_width=max_width,
        expand=expand,
        clickable=clickable,
        alignment=alignment,
        reorderable=reorderable,
        sort_column_id=sort_column_id,
        sort_indicator=sort_indicator,
        sort_order=sort_order,
        col_attrs=col_attrs)

    return col

def create_float_data_func(attribute='text', fmt="%.5f", invalid="#NA#"):
    """
        Creates a data function that can be used to render floats as formatted
        strings, with detection of invalid values (e.g. None)
    """
    def float_renderer(column, cell, model, itr, args=None):
        nr = model.get_value(itr, column.get_col_attr(attribute))
        try:
            cell.set_property('text', fmt % nr)
        except:
            cell.set_property('text', invalid)
    return float_renderer

def reset_columns(tv):
    """
        Remove all columns from the treeview
    """
    for col in tv.get_columns():
        tv.remove_column(col)

def setup_treeview(tv, model,
        reset=False,
        on_cursor_changed=None,
        on_selection_changed=None,
        sel_mode=gtk.SELECTION_SINGLE):
    """
        Sets up a treeview (signal connection, sets selection mode).
    """
    if reset: reset_columns(tv)
    sel = tv.get_selection()
    sel.set_mode(sel_mode)
    ids = ()
    if on_cursor_changed is not None:
        ids += (tv.connect('cursor_changed', on_cursor_changed),)
    if on_selection_changed is not None:
        ids += (sel.connect('changed', on_selection_changed),)
    return ids

