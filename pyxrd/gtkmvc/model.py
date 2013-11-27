# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.gtkmvc.model_base import * # @UnusedWildImport

try:
    from pyxrd.gtkmvc.model_mt import ModelMT # @UnusedImport
except ImportError:
    ModelMT = Model