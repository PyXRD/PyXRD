#  -------------------------------------------------------------------------
#  Author: Roberto Cavada <roboogle@gmail.com>
#
#  Copyright (C) 2010 by Roberto Cavada
#  Copyright (C) 2010 by Tobias Weber
#  pygtkmvc is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  pygtkmvc is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor,
#  Boston, MA 02110, USA.
#
#  For more information on pygtkmvc see <http://pygtkmvc.sourceforge.net>
#  or email to the author Roberto Cavada <roboogle@gmail.com>.
#  Please report bugs to <roboogle@gmail.com>.
#  -------------------------------------------------------------------------


# ----------------------------------------------------------------------
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

        self.__models.add((model, prop_name))
        return

    def __remove_model__(self, model, prop_name):
        """Unregisters the given model, to release the wrapper. This
        method reverts the effect of __add_model__"""
        self.__models.discard((model, prop_name))
        return

    def __get_models__(self): return self.__models

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


# ----------------------------------------------------------------------
class ObsWrapper (ObsWrapperBase):
    """
    Base class for wrappers, like user-classes and sequences. 
    """

    def __init__(self, obj, method_names):
        ObsWrapperBase.__init__(self)

        self._obj = obj
        self.__doc__ = obj.__doc__

        # Creates a derived class which is a singleton which self is
        # going to be an instance of. All method_names are then
        # wrapped within it.
        # See http://stackoverflow.com/questions/1022499/emulating-membership-test-in-python-delegating-contains-to-contained-object
        d = dict((name, self.__get_wrapper(name)) for name in method_names)
        self.__class__ = type(self.__class__.__name__, (self.__class__,), d)
        return

    def __get_wrapper(self, name):
        def _wrapper_fun(self, *args, **kwargs):
            self._notify_method_before(self._obj, name, args, kwargs)
            res = getattr(self._obj, name)(*args, **kwargs)
            self._notify_method_after(self._obj, name, res, args, kwargs)
            return res
        return _wrapper_fun

    # For all fall backs
    def __getattr__(self, name): return getattr(self._obj, name)
    def __repr__(self): return self._obj.__repr__()
    def __str__(self): return self._obj.__str__()

    pass # end of class


# ----------------------------------------------------------------------
class ObsSeqWrapper (ObsWrapper):
    def __init__(self, obj, method_names):
        ObsWrapper.__init__(self, obj, method_names)

        for _m in "lt le eq ne gt ge len iter".split():
            meth = "__%s__" % _m
            assert hasattr(self._obj, meth), "Not found method %s in %s" % (meth, str(type(self._obj)))
            setattr(self.__class__, meth, getattr(self._obj, meth))
            pass
        return

    def __setitem__(self, key, val):
        self._notify_method_before(self._obj, "__setitem__", (key, val), {})
        res = self._obj.__setitem__(key, val)
        self._notify_method_after(self._obj, "__setitem__", res, (key, val), {})
        return res

    def __delitem__(self, key):
        self._notify_method_before(self._obj, "__delitem__", (key,), {})
        res = self._obj.__delitem__(key)
        self._notify_method_after(self._obj, "__delitem__", res, (key,), {})
        return res

    def __getitem__(self, key):
        return self._obj.__getitem__(key)

    pass # end of class


# ----------------------------------------------------------------------
class ObsMapWrapper (ObsSeqWrapper):
    def __init__(self, m):
        methods = ("clear", "pop", "popitem", "update",
                   "setdefault")
        ObsSeqWrapper.__init__(self, m, methods)
        return
    pass # end of class


# ----------------------------------------------------------------------
class ObsListWrapper (ObsSeqWrapper):
    def __init__(self, l):
        methods = ("append", "extend", "insert",
                   "pop", "remove", "reverse", "sort")
        ObsSeqWrapper.__init__(self, l, methods)

        for _m in "add mul".split():
            meth = "__%s__" % _m
            assert hasattr(self._obj, meth), "Not found method %s in %s" % (meth, str(type(self._obj)))
            setattr(self.__class__, meth, getattr(self._obj, meth))
            pass
        return

    def __radd__(self, other): return other.__add__(self._obj)
    def __rmul__(self, other): return self._obj.__mul__(other)

    pass # end of class



# ----------------------------------------------------------------------
class ObsUserClassWrapper (ObsWrapper):
    def __init__(self, user_class_instance, obs_method_names):
        ObsWrapper.__init__(self, user_class_instance, obs_method_names)
        return
    pass # end of class



