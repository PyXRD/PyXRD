# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.gtkmvc.model_base import * # @UnusedWildImport

GTK_AVAILABLE = False
try:
    from pyxrd.gtkmvc.model_gtk import TreeStoreModel, ListStoreModel, TextBufferModel # @UnusedImport
    GTK_AVAILABLE = True
except ImportError:
    pass # ignore missing GTK