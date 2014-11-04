# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#
#  mvc is a framework derived from the original pygtkmvc framework
#  hosted at: <http://sourceforge.net/projects/pygtkmvc/>
#
#  mvc is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  mvc is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor,
#  Boston, MA 02110, USA.
#  -------------------------------------------------------------------------

import weakref
from .base import Observer

class ListItemObserver(Observer):
    """
        An observer that observes a single item in a list and informs us of changes.
        The observed properties are defined in the list type's meta class by
        setting their PropIntel 'is_column' attribute to True.
    """

    _previous_model_ref = None
    @property
    def _previous_model(self):
        if self._previous_model_ref is not None:
            return self._previous_model_ref()
        else:
            return None
    @_previous_model.setter
    def _previous_model(self, value):
        self._previous_model_ref = weakref.ref(value, self.clear)

    def __init__(self, on_changed, model=None, spurious=False):
        super(ListItemObserver, self).__init__(spurious=spurious)
        self.on_changed = on_changed
        self.observe_model(model)

    def observe_model(self, model):
        if self._previous_model is not None:
            self.relieve_model(self._previous_model)
        if model is not None:
            for prop_name, data_type in model.Meta.get_column_properties():  # @UnusedVariable
                self.observe(self.on_prop_mutation, prop_name, assign=True)
            self._previous_model = model
            super(ListItemObserver, self).observe_model(model)

    def clear(self, *args):
        self.on_changed = None
        if len(args) == 0:
            self.observe_model(None)

    def on_prop_mutation(self, model, prop_name, info):
        if callable(self.on_changed):
            self.on_changed(model)

    pass # end of class