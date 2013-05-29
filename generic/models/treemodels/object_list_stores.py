# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from traceback import print_exc

import gobject

from gtkmvc import Observer

from generic.io import storables, Storable, PyXRDDecoder
from .utils import smart_repos

from base_models import BaseObjectListStore

@storables.register()
class ObjectListStore(BaseObjectListStore, Storable):
    """
        GenericTreeModel implementation that holds a list with storable objects.
        Has support for some extra signals (pass the actual object instead of
        an iter). This ListStore does not require the objects to be unique.
    """

    #MODEL INTEL:
    __store_id__ = "ObjectListStore"

    #SIGNALS:
    __gsignals__ = { 
        'item-removed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'item-inserted' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
    }

    #PROPERTIES:
    _model_data = None #list with class_type instances

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, class_type, model_data=None, parent=None):
        if isinstance(class_type, basestring):
            class_type = storables[class_type]
        BaseObjectListStore.__init__(self, class_type)
        Storable.__init__(self)
        self._model_data = list()
        if model_data!=None:
            decoder = PyXRDDecoder(parent=parent)
            for obj in model_data:
                item = decoder.__pyxrd_decode__(obj, parent=parent)
                self._model_data.append(item)

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def json_properties(self):
        return { 'class_type': self._class_type.__store_id__,
                 'model_data': self._model_data }
                 
    def __reduce__(self):
        return (type(self), ((self._class_type,),{ 
            "model_data": self._model_data,
        }))

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def on_get_iter(self, path):
        try:
            return self._model_data[path[0]]
        except IndexError, msg:
            return None

    def on_get_path(self, rowref):
        try:
            return (self._model_data.index(rowref),)
        except ValueError:
            print "ValueError in on_get_path of %s caused by %s" % (self, rowref)
            print_exc()
            return None

    def set_value(self, itr, column, value):
        user_data = self.get_user_data(itr)
        setattr(user_data, self._columns[column][0], value)
        self.row_changed(self.get_path(itr), itr)

    def on_get_value(self, rowref, column):
        return getattr(rowref, self._columns[column][0])

    def on_iter_next(self, rowref):
        n, = self.on_get_path(rowref)
        try:
            rowref = self._model_data[n+1]
        except IndexError, msg:
            rowref = None
        return rowref

    def on_iter_children(self, rowref):
        if rowref:
            return None
        if self._model_data:
            return self.on_get_iter((0,))
        return None

    def on_iter_has_child(self, rowref):
        if rowref:
            return False
        if len(self._model_data) > 0:
            return True
        return False

    def on_iter_n_children(self, rowref):
        if rowref:
            return 0
        return len(self._model_data)

    def on_iter_nth_child(self, parent, n):
        if parent:
            return None
        if n < 0 or n >= len(self._model_data):
            return None
        return self._model_data[n]

    def on_iter_parent(self, rowref):
        return None
        
    def append(self, item):
        if not isinstance(item, self._class_type):
            raise ValueError, 'Invalid type, must be %s but got %s instead' % (self._class_type, type(item))
        elif not self.item_in_model(item):
            self._model_data.append(item)
            return self._emit_added(item)          
    def insert(self, pos, item):
        if not isinstance(item, self._class_type):
            raise ValueError, 'Invalid type, must be %s but got %s instead' % (self._class_type, type(item))
        elif not self.item_in_model(item):
            self._model_data.insert(pos, item)
            return self._emit_added(item)
    def _emit_added(self, item):
        if hasattr(item, "__list_store__"):
            item.__list_store__ = self
        itr = self.create_tree_iter(item)
        path = self.get_path(itr)
        self.row_inserted(path, itr)
        self.emit('item-inserted', item)
        return path
                
    def remove(self, itr):
        self.remove_item(self.get_user_data(itr))
    def remove_item(self, item):
        self.__remove_item_index(item, self._model_data.index(item))
    def __remove_item_index(self, item, index):
        del self._model_data[index]
        if hasattr(item, "__list_store__"):
            item.__list_store__ = None
        self.emit('item-removed', item)
        self.row_deleted((index,))

    def clear(self, callback=None):
        data = list(self._model_data) #make a copy
        def reverse_enum(L):
           for index in reversed(xrange(len(L))):
              yield index, L[index]
        for i, item in reverse_enum(data):
            self.__remove_item_index(item, i)
            if callable(callback): callback(item)

    def on_item_changed(self, item):
        itr = self.create_tree_iter(item)
        path = self.get_path(itr)
        self.row_changed(path, itr)

    def item_in_model(self, item):
        return item in self._model_data

    def index(self, item):
        return self._model_data.index(item)
        
    def replace_item(self, old_item, new_item):
        index = self.index(old_item)
        self.remove_item(old_item)
        self.insert(index, new_item)
        
    def get_user_data_from_index(self, index):
        return self._model_data[index]
        
    def reposition_item(self, item, new_pos):
        old_pos = self._model_data.index(item)
        if old_pos != new_pos:
            new_order = smart_repos(len(self._model_data), old_pos, new_pos)   
            
            self._model_data.remove(item)
            self._model_data.insert(new_pos, item)
            
            itr = self.create_tree_iter(item)
            path = self.get_path(itr)
            self.rows_reordered(None, None, new_order)
    
    def move_item_down(self, item):
        if item!=None:
            old_pos = self._model_data.index(item)
            new_pos = old_pos + 1            
            if new_pos < len(self._model_data):
                self.reposition_item(item, new_pos)
    def move_item_up(self, item):
        if item!=None:
            old_pos = self._model_data.index(item)
            new_pos = old_pos - 1            
            if new_pos >= 0:
                self.reposition_item(item, new_pos) 
                
    def get_raw_model_data(self):
        return self._model_data
        
    def iter_objects(self):
        for item in self._model_data:
            yield item

    pass #end of class

gobject.type_register(ObjectListStore)

@storables.register()
class IndexListStore(ObjectListStore):
    """
        GenericTreeModel implementation that holds a list with objects.
        Has support for some extra signals (pass the actual object instead of
        an iter). This ListStore requires the objects to be unique, based on
        their '__index_column__' value.
    """
    __store_id__ = "IndexListStore"
    _index_column_name = None
    _index = None
    
    _item_observer = None
    class ItemObserver(Observer):
        liststore = None
        
        ignore_next_notification = False
        
        def __init__(self, liststore, *args, **kwargs):
            self.liststore = liststore
            self.index_column_name = liststore._index_column_name
            Observer.__init__(self, *args, **kwargs)
            self.observe(self.notification, liststore._index_column_name, assign=True)
        
        def notification(self, model, prop_name, info):
            if not self.ignore_next_notification:
                if self.liststore.index_in_model(info["new"]):
                    self.ignore_next_notification = True
                    info["new"] = "%s_2" % info["new"]
                    setattr(model, self.liststore._index_column_name, info["new"])
                    self.liststore._index[info["new"]] = model
                    del self.liststore._index[info["old"]]
                    return
                else:
                    self.liststore._index[info["new"]] = model
                    del self.liststore._index[info["old"]]
            self.ignore_next_notification = False
    
    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, class_type, **kwargs):
        if isinstance(class_type, basestring):
            class_type = storables[class_type]
        if not hasattr(class_type, '__index_column__'):
            raise TypeError, "class_type should have an __index_column__ \
                attribute, but %s has not" % class_type
        if not class_type.__index_column__ in zip(*class_type.__columns__)[0]:
            raise AttributeError, "The index column '%s' should be a member of \
                the __columns__" % class_type.__index_column__
        if not class_type.__index_column__ in class_type.__observables__:
            raise AttributeError, "The index column '%s' should be a member of \
                the __observables__" % class_type.__index_column__
        self._index = dict()
        self._index_column_name = class_type.__index_column__
        self._item_observer = IndexListStore.ItemObserver(liststore=self)
        ObjectListStore.__init__(self, class_type, **kwargs)
       
    def __reduce__(self):
        return (type(self), ((self._class_type,),{ 
            "model_data": self._model_data,
        }))
       
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------ 
    def append(self, item):
        assert not self.item_in_model(item)
        return ObjectListStore.append(self, item)
    def insert(self, pos, item):
        assert not self.item_in_model(item)
        return ObjectListStore.insert(self, pos, item)
    def _emit_added(self, item):
        path = ObjectListStore._emit_added(self, item)
        self._index[getattr(item, self._index_column_name)] = item
        self._item_observer.observe_model(item)
        return path

    def remove_item(self, item):
        assert self.item_in_model(item)
        self._item_observer.relieve_model(item)
        del self._index[getattr(item, self._index_column_name)]
        ObjectListStore.remove_item(self, item)

    def clear(self):
        self._index.clear()
        ObjectListStore.clear(self, self._item_observer.relieve_model)
       
    def item_in_model(self, item):
        index = getattr(item, self._index_column_name)
        return index in self._index

    def index_in_model(self, index):
        return (index in self._index)
        
    def get_item_by_index(self, index):
        if self.index_in_model(index):
            return self._index[index]
        else:
            return None
            
    def get_raw_model_data(self):
        return self._index

    pass #end of class

gobject.type_register(IndexListStore)
