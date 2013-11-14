# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

try:
    import gtk
except ImportError:
    from pyxrd.generic import dummy_gtk as gtk

class BaseObjectListStore(gtk.GenericTreeModel):
    """
        Base mixin for creating GenericTreeModel implementations for lists of
        objects. It maps the columns of the store with properties of the object.
        If the PyGTK modules are not available (e.g. on a headless HPC cluster),
        a dummy gtk module is loaded. Not all (GTK) functionality is enabled in that case.
    """

    # PROPERTIES
    _columns = None # list of tuples (name, type)
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
        return gtk.TREE_MODEL_LIST_ONLY

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

    pass # end of class
