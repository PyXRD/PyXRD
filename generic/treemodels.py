# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from traceback import print_exc

from collections import namedtuple
from generic.utils import whoami, smart_repos

import numpy as np
from scipy.interpolate import interp1d

from generic.io import Storable, PyXRDDecoder, get_json_type, json_type

from gtkmvc import Model, Observer

import gtk
import gobject
import json

class _BaseObjectListStore(gtk.GenericTreeModel):
    """
        Base class for creating GenericTreeModel implementations for lists of
        objects. It maps the columns of the store with properties of the object.
    """
    
    #PROPERTIES
    _columns = None #list of tuples (name, type)
    _class_type = None

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, class_type):
        gtk.GenericTreeModel.__init__(self)
        self.set_property("leak-references", False)
        if class_type is None:
            raise ValueError, 'Invalid class_type for %s! Expecting object, but None was given' % type(self)
        elif not hasattr(class_type, '__columns__'):
            raise ValueError, 'Invalid class_type for %s! %s does not have __columns__ attribute!' % (type(self), type(class_type))
        else:
            self.setup_class_type(class_type)

    def setup_class_type(self, class_type):
        self._class_type = class_type
        self._columns = self._class_type.__columns__
        i = 0
        for col in self._columns:
            setattr(self, "c_%s" % col[0], i)
            i += 1

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY | gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_n_columns(self):
        return len(self._columns)

    def on_get_column_type(self, index):
        return self._columns[index][1]

    def get_user_data_from_path(self, path):
        return self.on_get_iter(path)
        
    def convert(self, col, new_val):
        return self._columns[col][1](new_val)
        
    def get_objects(self):
        raise NotImplementedError
        
    def iter_objects(self):
        raise NotImplementedError
        
    def __reduce__(self):
        raise NotImplementedError

class ObjectListStore(_BaseObjectListStore, Storable):
    """
        GenericTreeModel implementation that holds a list with objects.
        Has support for some extra signals (pass the actual object instead of
        an iter). This ListStore does not require the objects to be unique.
    """

    #MODEL INTEL:
    

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
            class_type = get_json_type(class_type)
        _BaseObjectListStore.__init__(self, class_type)
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
        return { 'class_type': json_type(self._class_type),
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

class ObjectTreeNode(object):

    def insert(self, index, child_node):
        if not isinstance(child_node, ObjectTreeNode):
            child_node = ObjectTreeNode(child_node)
        child_node.parent = self
        self._children.insert(index, child_node)
        return child_node

    def append(self, child_node):
        if not isinstance(child_node, ObjectTreeNode):
            child_node = ObjectTreeNode(child_node)
        child_node.parent = self
        self._children.append(child_node)
        return child_node

    def remove(self, child_node):
        self._children.remove(child_node)
        child_node._parent = None

    _parent = None
    @property
    def parent(self):
        return self._parent
    @parent.setter
    def parent(self, parent):
        if self._parent:
            self._parent.remove(self)
        self._parent = parent

    @property
    def has_children(self):
        return bool(self._children)
        
    @property
    def child_count(self):
        return len(self._children)

    def __init__(self, obj=None, children=()):
        object.__init__(self)
        self.object = obj
        self._children = list()
        for child in children: self.append(child)
               
    def get_child_node_index(self, child_node):
        return self._children.index(child_node)
        
    def get_root_node(self):
        parent = self.parent
        while parent.parent!=None:
            parent = parent.parent
        return parent
        
    def get_next_node(self):
        try:
            return self.parent.get_child_node(
                self.parent.get_child_node_index(self)+1)
        except IndexError:
            return None
        
    def get_prev_node(self):
        try:
            return self.parent.get_child_node(
                self.parent.get_child_node_index(self)-1)
        except IndexError:
            return None            
        
    def get_indeces(self):
        parent = self.parent
        node = self
        indeces = tuple()
        while parent!=None:
            indeces += (parent.get_child_node_index(node),)
            node = parent
            parent = parent.parent
        return indeces[::-1] or None
        
    def get_child_node(self, *indeces):
        node = self
        for index in indeces:
            node = node._children[index]
        return node
        
    def get_first_child_node(self):
        try:
            return self._children[0]
        except IndexError:
            return None
        
    def get_child_object(self, *indeces):
        return self.get_child_node(*indeces).object
        
    def clear(self):
        for c in self.iter_children(reverse=True, recursive=True):
            yield c
            c.parent=None
        
    def iter_children(self, reverse=False, recursive=False):
        children = self._children if not reverse else self._children[::-1]
        for child_node in children:
            if recursive and child_node.has_children:
                for c in child_node.iter_children(reverse=reverse, recursive=recursive):
                    yield c
            yield child_node
        
    def __repr__(self):
        return '%s(%s - %s)' % (type(self).__name__, self.object, "%d child nodes"%len(self._children))
        
class ObjectTreeStore(_BaseObjectListStore, Storable):
    """
        GenericTreeModel implementation that holds a tree with objects.
        Has support for some extra signals (pass the actual object instead of
        an iter). This TreeStore does not require the objects to be unique.
    """

    #MODEL INTEL:
    

    #SIGNALS:
    __gsignals__ = { 
        'item-removed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'item-inserted' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
    }

    #PROPERTIES:
    # An object tree node with obj = None  
    _model_data = None
    _object_node_map = None

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, class_type, model_data=None, parent=None):
        if isinstance(class_type, basestring):
            class_type = get_json_type(class_type)
        _BaseObjectListStore.__init__(self, class_type)
        Storable.__init__(self)
        self._model_data = ObjectTreeNode()
        self._object_node_map = dict()
        #if model_data!=None: FIXME!!
        #    decoder = PyXRDDecoder(parent=parent)
        #    for obj in model_data:
        #        item = decoder.__pyxrd_decode__(obj, parent=parent)
        #        self.append(item)

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def json_properties(self):
        return { 'class_type': json_type(self._class_type),
                 'model_data': self._model_data }
                 
    def __reduce__(self):
        return (type(self), ((self._class_type,),{ 
            "model_data": self._model_data,
        }))

    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def on_get_flags(self):
        return gtk.TREE_MODEL_ITERS_PERSIST
        
    def on_get_iter(self, path):
        try:
            if hasattr(path, 'split'): path = map(int, path.split(":"))
            return self._model_data.get_child_node(*path)
        except IndexError, msg:
            print "self in on_get_iter of %s caused by %s" % (self, path)
            return None

    def on_get_path(self, node):
        try:
            return ":".join(map(str,node.get_indeces()))
        except ValueError:
            print "ValueError in on_get_path of %s caused by %s" % (self, node)
            raise
            return None

    def set_value(self, itr, column, value):
        user_data = self.get_user_data(itr)
        setattr(user_data, self._columns[column][0], value)
        self.row_changed(self.get_path(itr), itr)

    def on_get_value(self, node, column):
        
        return getattr(node.object, self._columns[column][0])

    def on_iter_next(self, node):
        return node.get_next_node()

    def on_iter_children(self, node):
        node = node or self._model_data
        return node.get_first_child_node()

    def on_iter_has_child(self, node):
        node = node or self._model_data
        return node.has_children

    def on_iter_n_children(self, node):
        node = node or self._model_data
        return node.child_count

    def on_iter_nth_child(self, parent, n):
        node = parent or self._model_data
        try:
            return node.get_child_node(n)
        except:
            return None

    def on_iter_parent(self, node):
        return node.parent
        
    def append(self, parent, item):
        if not isinstance(item, self._class_type):
            raise ValueError, 'Invalid type, must be %s but got %s instead' % (self._class_type, type(item))
        else:
            parent = parent or self._model_data
            node = parent.append(item)
            return self._emit_added(node)          
    def insert(self, parent, pos, item):
        if not isinstance(item, self._class_type):
            raise ValueError, 'Invalid type, must be %s but got %s instead' % (self._class_type, type(item))
        else:
            parent = parent or self._model_data
            node = parent.insert(pos, item)
            return self._emit_added(node)
    def _emit_added(self, node):
        if hasattr(node.object, "__list_store__"):
            node.object.__list_store__ = self
        self._object_node_map[node.object] = node
        itr = self.create_tree_iter(node)
        path = self.get_path(itr)
        self.row_inserted(path, itr)
        self.emit('item-inserted', node.object)
        return node
                
    def remove(self, itr):
        self.remove_item(self.get_tree_node(itr))
    def remove_item(self, node):
        indeces = node.get_indeces()
        node.parent = None #break link
        del self._object_node_map[node.object]
        if hasattr(node.object, "__list_store__"):
            node.object.__list_store__ = None
        self.emit('item-removed', node.object)
        self.row_deleted(indeces)

    def clear(self, callback=None):
        for node in self._model_data.clear():
            self.remove_item(node)
            if callable(callback): callback(node)

    def on_item_changed(self, object):
        node = self._object_node_map[object]
        itr = self.create_tree_iter(node)
        path = self.get_path(itr)
        self.row_changed(path, itr)
               
    def get_raw_model_data(self):
        return self._model_data
        
    def iter_objects(self):
        for node in self._model_data.iter_children(recursive=True):
            yield node.object

    def get_tree_node(self, itr):
        return _BaseObjectListStore.get_user_data(self, itr)

    def get_tree_node_from_path(self, path):
        return _BaseObjectListStore.get_user_data_from_path(self, path)

    def get_user_data(self, itr):
        return _BaseObjectListStore.get_user_data(self, itr).object
        
    def get_user_data_from_path(self, path):
        return _BaseObjectListStore.get_user_data_from_path(self, path).object

    pass #end of class

gobject.type_register(ObjectTreeStore)

class IndexListStore(ObjectListStore):
    """
        GenericTreeModel implementation that holds a list with objects.
        Has support for some extra signals (pass the actual object instead of
        an iter). This ListStore requires the objects to be unique, based on
        their '__index_column__' value.
    """
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
            class_type = get_json_type(class_type)
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

Point = namedtuple('Point', ['x', 'y'], verbose=False)
Point.__columns__ = [
    ('x', float),
    ('y', float)
]

class XYListStore(_BaseObjectListStore, Storable):
    """
        GenericTreeModel implementation that holds a list with X,Y values.
        Is specialized for handling large lists, and uses Numpy arrays 
        internally instead of a regular list. Has two columns X and Y.
        Also implements some additional signals, passing an (X,Y) tuple instead
        of an iter.
    """
    
    __gsignals__ = { 
        'item-removed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'item-inserted' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'columns-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
    }

    _model_data_x = None
    _model_data_y = None
    _y_names = None

    # ------------------------------------------------------------
    #      Initialisation and other internals
    # ------------------------------------------------------------
    def __init__(self, data=None):
        _BaseObjectListStore.__init__(self, Point)
        Storable.__init__(self)
        self.set_property("leak-references", False)
        self._model_data_x = np.array([], dtype=float)
        self._model_data_y = np.zeros(shape=(0,0), dtype=float)
        self._y_names = []
        
        self._iters = dict()
        
        if data!=None:
            self._load_data(data)
        else:
            self.set_from_data(np.array([], dtype=float), np.array([], dtype=float))
           
    def _load_data(self, data):
        #data should be in this format:
        #  [  (x1, y1, y2, ..., yn), (x2, y1, y2, ..., yn), ... ]
        data = data.replace("nan", "0.0")
        data = zip(*json.JSONDecoder().decode(data))
        if data != []:
            self.set_from_data(*data)
                
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def json_properties(self):
        conc = np.insert(self._model_data_y, 0, self._model_data_x, axis=0).transpose()
        return {
            "data": "[" + ",".join(
                ["[" + ",".join(["%f" % val for val in row]) + "]" for row in conc]
            ) + "]",
        }

    def __reduce__(self):
        return (type(self), (), self.json_properties())

    def save_data(self, header, filename):
        f = open(filename, 'w')
        if self._model_data_y.shape[0] > 1:
            header = "%s - columns: %s" % (header, "2θ, Int., " + ", ".join(self._y_names))
        f.write("%s\n" % header)
        np.savetxt(f, np.insert(self._model_data_y, 0, self._model_data_x, axis=0).transpose(), fmt="%.8f")
        f.close()
        
    @staticmethod
    def parse_data(data, format="DAT", has_header=True):
        f = None
        close = False
        if type(data) is file:
            f = data
        elif type(data) is str:
            if format=="BIN":
                f = open(data, 'rb')
            else:
                f = open(data, 'r')
            close = True
        else:
            raise TypeError, "Wrong data type supplied for binary format, \
                must be either file or string, but %s was given" % type(data)

        if format=="DAT":
            while True:
                line = f.readline()
                #for line in f:
                if has_header:
                    has_header=False #skip header
                elif line != "":
                    yield map(float, line.replace(",",".").split())
                else:
                    break
        if format=="BIN":
            if f != None:
                import struct
                #seek data limits
                f.seek(214)
                stepx, minx, maxx = struct.unpack("ddd", f.read(24))
                nx = int((maxx-minx)/stepx)
                #read values                          
                f.seek(250)
                n = 0
                while n < nx:
                    y, = struct.unpack("H", f.read(2))
                    yield minx + stepx*n, float(y)
                    n += 1
                    
        #close file
        if close: f.close()

        
    def load_data(self, *args, **kwargs):
        if kwargs.get("clear", True):
            self.clear()
        if "clear" in kwargs: del kwargs["clear"]
        for x,y in XYListStore.parse_data(*args, **kwargs):
            self.append(x, y)
        
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY
    
    _y_from_user = lambda self, y_value: np.array(y_value, ndmin=2)
    def _y_to_user(self, y_value):
        try:
            return tuple(y_value)
        except TypeError:
            return (y_value,)
    def _get_subitr(self, index):
        x = self._model_data_x[index]
        y = tuple(self._y_to_user(self._model_data_y[:,index]))
        return (x,) + y
    
    def on_get_iter(self, path): #returns a rowref
        try:
            path = path[0]
            if path < self._model_data_x.size:
                itr = self._iters.get(path, None)
                if itr==None:
                    self._iters[path] = itr = (path,) + self._get_subitr(path)
                return itr
            else:
                return None
        except IndexError, msg:
            return None
            
    def invalidate_iters(self):
        self._iters.clear()
        _BaseObjectListStore.invalidate_iters(self)
        
    def set_value(self, itr, column, value):
        i = self.get_user_data(itr)[0]
        if i < self._model_data_x.size:
            if column == self.c_x:
                self._model_data_x[i] = value
            elif column >= self.c_y:
                self._model_data_y[column-1, i] = np.array(value)
            else:
                raise AttributeError
        else:
            raise IndexError
        self.row_changed((i,), itr)

    def on_get_value(self, rowref, column):
        i = rowref[0]
        if column == self.c_x:
            return self._model_data_x[i]
        elif column >= self.c_y:
            return self._model_data_y[column-1, i]
        else:
            raise AttributeError
                       
    def on_get_path(self, rowref):
        return (rowref[0],)

    def on_iter_next(self, rowref):
        i = rowref[0]
        return self.on_get_iter((i+1,))

    def on_iter_children(self, rowref):
        if rowref is not None:
            return None
        elif self._model_data_x and self._model_data_y and self._model_data_x.size > 0:
            return 0
        return None

    def on_iter_has_child(self, rowref):
        if rowref is not None:
            return False
        elif self._model_data_x and self._model_data_y and self._model_data_x.size > 0:
            return True
        return False

    def on_iter_n_children(self, rowref):
        if rowref:
            return 0
        return self._model_data_x.size

    def on_iter_nth_child(self, parent, n):
        if parent:
            return None
        if n < 0 or n >= self._model_data_x.size:
            return None
        return self.on_get_iter((n,))

    def on_iter_parent(self, rowref):
        return None
        
    def append(self, x, *y):
        self._model_data_x = np.append(self._model_data_x, x)
        if self._model_data_y.size == 0:
            self._model_data_y = self._y_from_user(y)
        else:
            self._model_data_y = np.append(self._model_data_y, self._y_from_user(y), axis=1)
        path = (self._model_data_x.size-1,)
        self._emit_added(path)
        return path
    
    def insert(self, pos, x, *y):
        self._model_data_x = np.insert(self._model_data_x, pos, x)
        self._model_data_y = np.insert(self._model_data_y, pos, self._y_from_user(y), axis=1)
        self._emit_added((pos,))
      
    def _emit_added(self, path):
        index = int(path[0])
        self.emit('item-inserted', self._get_subitr(index))
        itr = self.get_iter(path)
        self.invalidate_iters()
        self.row_inserted(path, itr)

    def remove_from_index(self, *indeces):
        if indeces != []:
            indeces = np.sort(indeces)[::-1]
            shape = self._model_data_x.shape
            for index in indeces:
                self.emit('item-removed', 0) #self._get_subitr(index))
                self._model_data_x = np.delete(self._model_data_x, index, axis=0)
                self._model_data_y = np.delete(self._model_data_y, index, axis=1)
                self.row_deleted((index,))
            self.invalidate_iters()

    def remove(self, itr):
        path = self.get_path(itr)
        self.remove_from_index(path[0])

    def clear(self):
        if self._model_data_x.shape[0] > 0:
            self.remove_from_index(*range(self._model_data_x.shape[0]))

    def set_from_data(self, data_x, *data_y, **kwargs):
        names = kwargs.get("names", None)
        tempx = np.array(data_x)
        tempy = np.array(data_y, ndmin=2)
        if tempx.shape[0] != tempy.shape[-1]:
            raise ValueError, "Shape mismatch: x and y data need to have compatible shapes!"
        self.clear()
        self._model_data_x = tempx
        self._model_data_y = tempy
        self._y_names = names
        for index in range(self._model_data_x.shape[0]):
            self._emit_added((index,))
        self.emit('columns-changed')
        
    def update_from_data(self, data_x, *data_y, **kwargs):
        names = kwargs.get("names", None)
        tempx = np.array(data_x)
        tempy = np.array(data_y, ndmin=2)
        if self._model_data_x.size > 0 and tempx.shape == self._model_data_x.shape and tempy.shape[1] == self._model_data_y.shape[1]:
            self._model_data_x = tempx
            if tempy.shape[0] == 1:
                self._model_data_y[0] = tempy[0]
                if names!=None: self._y_names = names
            else:
                self._model_data_y = tempy
                self._y_names = names
            self.emit('columns-changed')
        else:
            self.set_from_data(data_x, *data_y, **kwargs)
        
    def get_y_name(self, col_index):
        try:
            return self._y_names[col_index]
        except:
            return ""
        
    def get_raw_model_data(self):
        if self._model_data_x.size:
            return self._model_data_x, self._model_data_y[0]
        else:
            return np.array([], dtype=float), np.array([], dtype=float)
                
    def on_get_n_columns(self):
        return 1 + self._model_data_y.shape[0]

    def on_get_column_type(self, index):
        return float
                        
    def interpolate(self, *x_vals):
        column = kwargs.get("column", 0)
        f = interp1d(self._model_data_x, self._model_data_y.transpose()[column])
        return zip(x_vals, f(x_vals))
        
    pass #end of class
   
gobject.type_register(XYListStore)

