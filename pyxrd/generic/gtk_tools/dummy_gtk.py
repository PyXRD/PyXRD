# coding=UTF-8
# ex:ts=4:sw=4:et

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from mvc.support.utils import get_new_uuid


__all__ = [
    "gobject",
    "GtkTreeIter",
    "GenericTreeModel"
    "TREE_MODEL_LIST_ONLY"
]

TREE_MODEL_LIST_ONLY = 0x00
TREE_MODEL_ITERS_PERSIST = 0x00

events_pending = lambda: False

class GtkTreeIter():
    def __init__(self, user_data, path=None):
        self.user_data = user_data
        self.path = path

    pass # end of class




class GenericTreeModel(object):
    __connected_signals__ = None

    def __init__(self):
        self.__connected_signals__ = {}

    def connect(self, signal_name, handler, *args):
        handlers = self.__connected_signals__.get(signal_name, {})
        handler_id = get_new_uuid()
        handlers[handler_id] = (handler, args)
        self.__connected_signals__[signal_name] = handlers
        return handler_id

    def disconnect(self, signal_name, handler_id):
        try:
            handlers = self.__connected_signals__.get(signal_name, {})
            del handlers[handler_id]
        except KeyError:
            pass
        return

    def emit(self, signal_name, args=()):
        handlers = self.__connected_signals__.get(signal_name, {})
        for id, (handler, user_args) in handlers.iteritems(): # @ReservedAssignment
            handler(self, *((args,) + user_args))
        pass

    def set_property(self, *args, **kwargs):
        pass

    def create_tree_iter(self, user_data):
        return GtkTreeIter(user_data)

    def get_path(self, itr):
        return self.on_get_path(itr.user_data)

    def get_iter(self, path):
        return self.create_tree_iter(self.on_get_iter(path))

    def row_inserted(self, path, itr):
        self.emit("row-inserted", (path, itr))

    def row_deleted(self, indeces):
        self.emit("row-deleted", (indeces,))

    def invalidate_iters(self):
        pass # TOD0!

    def iter_is_valid(self, itr):
        return True # TODO!

    def __len__(self):
        return len(self._model_data)

    pass # end of class
