# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk

#general rule is:
#explicit kwargs = column kwargs
#implicit kwargs = renderer kwargs

def _parse_kwargs(**kwargs):
    """
        Parses key-word arguments passed to the new_*_column functions.
        It checks for the presence of key-words ending with '_col', these are
        popped and stored in a seperate dictionary, as they are to be passed
        to the constructor of the actual TreeViewColumn (attribute mappings)
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

def _parse_callback(callback, reduce=True):
    """
        Parses callbacks passed to the new_*_column functions, splits the 
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

def _get_default_renderer(type, **kwargs):
    """
        Creates a CellRendere of type 'type' and sets any attributes passed with
        the key-word arguments. Underscores in variable names are replaced with
        dashes in the proces.
    """
    rend = type()
    for key, val in kwargs.iteritems():
        rend.set_property(key.replace("_", "-"), val)
    return rend

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
        self._attrs[attribute] = dict()
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
    if data_func!=None:
        callback, args = _parse_callback(data_func)
        col.set_cell_data_func(rend, callback, args)
    col.set_spacing(spacing)
    col.set_visible(visible)
    col.set_resizable(resizable)
    col.set_sizing(sizing)
    col.set_fixed_width(fixed_width)
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
    kwargs, col_attrs = _parse_kwargs(**kwargs)
    alignment = alignment if alignment!=None else kwargs["xalign"]
    
    rend = _get_default_renderer(gtk.CellRendererText, **kwargs)
    if edited_callback!=None:
        callback, args = _parse_callback(edited_callback, reduce=False)
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
    kwargs, col_attrs = _parse_kwargs(**kwargs)
    alignment = alignment if alignment!=None else kwargs["xalign"]
        
    rend = _get_default_renderer(gtk.CellRendererPixbuf, **kwargs)
    
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
    kwargs, col_attrs = _parse_kwargs(**kwargs)
    alignment = alignment if alignment!=None else kwargs["xalign"]
    
    rend = _get_default_renderer(gtk.CellRendererToggle, **kwargs)
    if toggled_callback!=None:
        callback, args = _parse_callback(toggled_callback, reduce=False)
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
    
def setup_treeview(tv, model, 
        on_cursor_changed=None, 
        on_columns_changed=None,
        on_selection_changed=None,
        sel_mode=gtk.SELECTION_SINGLE):
    """
        Sets up a treeview (model & signal connection, sets selection mode).
    """
    tv.set_model(model)
    sel = tv.get_selection()
    if on_cursor_changed!=None:
        tv.connect('cursor_changed', on_cursor_changed)
    if on_columns_changed!=None:
        model.connect('columns-changed', on_columns_changed)
    if on_selection_changed!=None:
        sel.connect('changed', on_selection_changed)
    #set selection mode:
    sel.set_mode(sel_mode)    
