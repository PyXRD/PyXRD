# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from mvc.controller import Controller

from .status_bar_mixin import StatusBarMixin

class BaseController(StatusBarMixin, Controller):
    file_filters = ("All Files", "*.*")
    widget_handlers = {} # handlers can be string representations of a class method
    auto_adapt_included = None
    auto_adapt_excluded = None

    pass # end of class
