# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk
 
from gtkmvc import Controller
from gtkmvc.adapters import Adapter

from generic.views.treeview_tools import new_text_column, setup_treeview
from handlers import default_widget_handler, widget_handlers
import settings 

def ctrl_setup_combo_with_list(ctrl, combo, prop_name, list_prop_name=None, list_data=None, store=None):

    if store==None:
        if list_data!=None:
            store = gtk.ListStore(str, str)
        elif list_prop_name!=None:
            store = gtk.ListStore(str, str)
            list_data = getattr(ctrl.model, list_prop_name)
        else:
            raise AttributeError, "Either one of list_prop_name, list_data or store is required to be passed!"
        for key in list_data:
            store.append([key, list_data[key]])
    combo.set_model(store)

    cell = gtk.CellRendererText()
    combo.pack_start(cell, True)
    combo.add_attribute(cell, 'text', 1)
    cell.set_property('family', 'Monospace')
    cell.set_property('size-points', 10)
    
    def on_changed(combo, user_data=None):
        itr = combo.get_active_iter()
        if itr != None:
            val = combo.get_model().get_value(itr, 0)
            setattr(ctrl.model, prop_name, val)
    combo.connect('changed', on_changed)

    for row in store:
        if store.get_value(row.iter, 0) == str(getattr(ctrl.model, prop_name)):
            combo.set_active_iter(row.iter)
            break
            
def get_case_insensitive_glob(*strings):
    '''Ex: '*.ora' => '*.[oO][rR][aA]' '''
    return ['*.%s' % ''.join(["[%s%s]" % (c.lower(), c.upper()) for c in string.split('.')[1]]) for string in strings]
    
def retrieve_lowercase_extension(glob):
    '''Ex: '*.[oO][rR][aA]' => '*.ora' '''
    return ''.join([ c.replace("[", "").replace("]", "")[:-1] for c in glob.split('][')])
