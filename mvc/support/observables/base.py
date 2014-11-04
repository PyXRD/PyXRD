# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#  Copyright (C) 2005 by Tobias Weber
#  Copyright (C) 2005 by Roberto Cavada <roboogle@gmail.com>
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

class ObsWrapperBase (object):
    """
    This class is a base class wrapper for user-defined classes and
    containers like lists, maps, signals, etc.
    """

    def __init__(self):
        # all model instances owning self (can be multiple due to
        # inheritance). Each element of the set is a pair (model,
        # property-name)
        self.__models = set()
        return

    def __add_model__(self, model, prop_name):
        """Registers the given model to hold the wrapper among its
        properties, within a property whose name is given as well"""
        ref = weakref.ref(model)
        self.__models.add((ref, prop_name))
        return

    def __remove_model__(self, model, prop_name):
        """Unregisters the given model, to release the wrapper. This
        method reverts the effect of __add_model__"""
        delete_models = set()
        for ref, prop_name in self.__models:
            if ref() == model and prop_name == prop_name:
                delete_models.add((ref, prop_name))
        self.__models -= delete_models
        return

    def __get_models__(self):
        delete_models = set()
        for ref, prop_name in self.__models:
            model = ref()
            if model is not None:
                yield model, prop_name
            else:
                delete_models.add((ref, prop_name))
        self.__models -= delete_models

    def _notify_method_before(self, instance, name, args, kwargs):
        for m, n in self.__get_models__():
            m.notify_method_before_change(n, instance, name,
                                          args, kwargs)
            pass
        return

    def _notify_method_after(self, instance, name, res_val, args, kwargs):
        for m, n in self.__get_models__():
            m.notify_method_after_change(n, instance, name, res_val,
                                         args, kwargs)
            pass
        return

    pass # end of class
