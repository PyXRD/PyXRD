# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk

def new_text_column(title, colnr, 
        edited_callback=None, 
        resizable=True, 
        expand=True,
        data_func=None,
        **kwargs):
    kwargs["xalign"] = kwargs.get("xalign", 0.5)
    rend = gtk.CellRendererText()
    for key, val in kwargs.iteritems():
        rend.set_property(key.replace("_", "-"), val)
    if edited_callback!=None:
        args = None
        try:
            callback, args = edited_callback
        except TypeError, ValueError:
            callback = edited_callback
        rend.connect('edited', callback, args)
    col = gtk.TreeViewColumn(title, rend, text=colnr)
    if data_func!=None:
        col.set_cell_data_func(rend, data_func, colnr)    
    col.set_resizable(resizable)
    col.set_expand(expand)
    col.set_alignment(kwargs["xalign"])
    return col
    
def setup_treeview(tv, model, 
        on_cursor_changed=None, 
        on_columns_changed=None, 
        sel_mode=gtk.SELECTION_SINGLE):
    tv.set_model(model)
    if on_cursor_changed!=None:
        tv.connect('cursor_changed', on_cursor_changed)
    if on_columns_changed!=None:
        model.connect('columns-changed', on_columns_changed)
    #allow multiple selection:
    sel = tv.get_selection()
    sel.set_mode(sel_mode)    
