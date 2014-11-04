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

from .base import Observer

class DictObserver(Observer):
    """
        An observer that wraps the in-instance changes of a dict to on_inserted
        and on_deleted handlers.
    """

    _deleted = []

    def __init__(self, on_inserted, on_deleted, prop_name, model=None, spurious=False):
        super(DictObserver, self).__init__(model=model, spurious=spurious)
        self.on_inserted = on_inserted
        self.on_deleted = on_deleted

        self.observe(self.on_prop_mutation_before, prop_name, before=True)
        self.observe(self.on_prop_mutation_after, prop_name, after=True)

    def on_prop_mutation_before(self, model, prop_name, info):
        if info.method_name in ("__setitem__", "__delitem__", "pop", "setdefault"):
            key = info.args[0]
            if key in info.instance:
                self._deleted.append(info.instance[key])

        if info.method_name == "update":
            if len(info.args) == 1:
                iterable = info.args[0]
            elif len(info.kwargs) > 0:
                iterable = info.kwargs
            if hasattr(iterable, "iteritems"):
                iterable = iterable.iteritems()
            for key, value in iterable: # @UnusedVariable
                if key in info.instance:
                    self._deleted.append(info.instance[key])

        if info.method_name == "clear":
            self._deleted.extend(info.instances.values())

    def on_prop_mutation_after(self, model, prop_name, info):

        if self._deleted:
            for old_item in self._deleted:
                self.on_deleted(old_item)
            self._deleted = []

        if info.method_name == "popitem":
            old_item = info.result[1]
            self.on_deleted(old_item)

    pass # end of class