# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import json

from traceback import print_exc
from collections import namedtuple

import numpy as np
from scipy.interpolate import interp1d

import gtk, gobject

from generic.io import storables, Storable, unicode_open as open
from generic.io.file_parsers import ASCIIParser
from base_models import BaseObjectListStore


Point = namedtuple('Point', ['x', 'y'], verbose=False)
Point.__columns__ = [
    ('x', float),
    ('y', float)
]

#TODO make handling multiple y-columns more transparent and consequent.
# Some methods now include this option while other expect only a single y value.
# The reason is mass-updating: if the data needs to be replaced with the same
# length, it is often faster to just replace it and then call the signals for
# each row or send a custom signal that allows to update the entire store...
# needs some thinking and planning to change this

@storables.register()
class XYListStore(BaseObjectListStore, Storable):
    """
        GenericTreeModel implementation that holds a list with X,Y values.
        Is specialized for handling large lists, and uses Numpy arrays 
        internally instead of a regular list. Has two columns X and Y.
        Also implements some additional signals, passing an (X,Y) tuple instead
        of an iter.
    """
    __store_id__ = "XYListStore"
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
        BaseObjectListStore.__init__(self, Point)
        Storable.__init__(self)
        self.set_property("leak-references", False)
        self._model_data_x = np.array([], dtype=float)
        self._model_data_y = np.zeros(shape=(0,0), dtype=float)
        self._y_names = []
        
        self._iters = dict()
        
        if data!=None:
            self._deserialize(data)
        else:
            self.set_from_data(np.array([], dtype=float), np.array([], dtype=float))
           
    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------
    def json_properties(self):
        return self._serialize()

    def __reduce__(self):
        return (type(self), (), self.json_properties())

    def save_data(self, header, filename):
        """
            Exports the data inside the XYListStore to the file 'filename' with
            the specified header in CSV format. Also includes column names.
            Employs the ASCIIParser's write method.
        """
        if self._model_data_y.shape[0] > 1:
            names = ["2θ", header] + (self._y_names or [])
            header = u",".join(names)
        ASCIIParser.write(filename, header, self._model_data_x, self._model_data_y)

    def _serialize(self):
        """
            Internal method, should normally not be used!
            If you want to write data to a file, use the save_data method instead!
        """
        conc = np.insert(self._model_data_y, 0, self._model_data_x, axis=0).transpose()
        return {
            "data": "[" + ",".join(
                ["[" + ",".join(["%f" % val for val in row]) + "]" for row in conc]
            ) + "]",
        }

    def _deserialize(self, data):
        """
            Internal method, should normally not be used!
            If you want to load data from a file, use the generic.io.file_parsers
            classes in combination with the load_data_from_generator instead!
            'data' argument should be a json string, containing a list of lists
            of x and y values, i.e.:
            [  [x1, x2, x3, ..., xn], [y11, y12, ..., y1n], ..., [ym1, ym2, ..., ymn] ]
            If there are n data points and m+1 columns.
        """
        data = data.replace("nan", "0.0")
        data = zip(*json.JSONDecoder().decode(data))
        if data != []:
            self.set_from_data(*data)
               
    def load_data_from_generator(self, generator, clear=True):
        """
            Loads data from an x,y generator by appending the values.
            This method does not allow to load multiple y values for now...
        """
        if clear: self.clear()
        for x, y in generator:
            self.append(x, y)
        
    # ------------------------------------------------------------
    #      Methods & Functions
    # ------------------------------------------------------------
    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY
    
    _y_from_user = lambda self, y_value: np.array(y_value, ndmin=2)
    """def _y_to_user(self, y_value):
        try:
            return tuple(y_value)
        except TypeError:
            return (y_value,)
    def _get_subitr(self, index):
        x = self._model_data_x[index]
        y = tuple(self._y_to_user(self._model_data_y[:,index]))
        return (x,) + y"""
    
    def on_get_iter(self, path): #returns a rowref
        try:
            i = path[0]
            if i >=0 and i < self._model_data_x.size:
                self._iters[i] = itr = self._iters.get(i, (i,))
                return itr
            else:
                return None
        except IndexError, msg:
            return None
        
    def invalidate_iters(self):
        self._iters.clear()
        BaseObjectListStore.invalidate_iters(self)
        
    def set_value(self, itr, column, value):
        i, = self.get_user_data(itr)
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

    def on_get_value(self, i, column):
        if column == self.c_x:
            return self._model_data_x[i]
        elif column >= self.c_y:
            return self._model_data_y[column-1, i]
        else:
            raise AttributeError
                       
    def on_get_path(self, i):
        return i

    def on_iter_next(self, i):
        return self.on_get_iter((i[0]+1,))

    def on_iter_children(self, i):
        if i is not None:
            return None
        elif self._model_data_x and self._model_data_y and self._model_data_x.size > 0:
            return 0
        return None

    def on_iter_has_child(self, i):
        if i is not None:
            return False
        elif self._model_data_x and self._model_data_y and self._model_data_x.size > 0:
            return True
        return False

    def on_iter_n_children(self, i):
        if i is not None:
            return 0
        return self._model_data_x.size

    def on_iter_nth_child(self, i, n):
        if i is not None:
            return None
        if n < 0 or n >= self._model_data_x.size:
            return None
        return self.on_get_iter((n,))

    def on_iter_parent(self, i):
        return None
        
    def on_get_n_columns(self):
        return 1 + self._model_data_y.shape[0]

    def on_get_column_type(self, index):
        return float
        
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
        self.emit('item-inserted', (self._model_data_x[index], tuple(self._model_data_y[:,index])))
        itr = self.get_iter(path)
        self.row_inserted(path, itr)

    def remove_from_index(self, *indeces):
        if indeces != []:
            indeces = np.sort(indeces)[::-1]
            shape = self._model_data_x.shape
            for index in indeces:
                self.emit('item-removed', 0)
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
            raise ValueError, "Shape mismatch: x (shape = %s) and y (shape = %s) data need to have compatible shapes!" % (tempx.shape, tempy.shape)
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
                
    def get_y_at_x(self, x, column=0):
        """ 
            Get the (interpolated) value for the y-column 'column' for
            a given x value
        """
        if self._model_data_x.size:
            return np.interp(x, self._model_data_x, self._model_data_y[column])
        else:
            return 0
                        
    def interpolate(self, *x_vals):
        column = kwargs.get("column", 0)
        f = interp1d(self._model_data_x, self._model_data_y.transpose()[column])
        return zip(x_vals, f(x_vals))
        
    pass #end of class
    
gobject.type_register(XYListStore)
