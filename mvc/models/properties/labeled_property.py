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

from mvc.support.utils import  rec_getattr, rec_setattr
from mvc.support.observables.value_wrapper import ValueWrapper
import inspect

class Mixable(object):
    """
    Base class that allows to mix-in any other new-style class
    passed in the constructor, using the mix_with keyword argument
    (tuple of class types).
    """

    def __init__(self, mix_with=None, *args, **kwargs):
        super(Mixable, self).__init__(*args, **kwargs)
        # Nifty hook so we can mix-in any other class:
        if mix_with is not None:
            name = type(self).__name__
            for klass in mix_with:
                name = "%s_%s" % (klass.__name__.replace("Mixin", ""), name)
            bases = tuple(mix_with) + (type(self),)
            self.__class__ = type(name, bases, {})

    pass #end of class

class LabeledProperty(Mixable):
    """
     Property descriptor base class to be used in combination with a
     ~:class:`mvc.models.Model` (sub)class.
     Expects it's label (attribute name) to be set or passed to __init__, for
     ~:class:`mvc.models.Model` (sub)class this is done automagically using
     its metaclass.
     
     Additional keyword arguments will be set as attributes on the descriptor.
     
     Some of these keywords have been given sane default values, even though
     they are not required for the implementation:
     
         - title = label
         - math_title = label
         - description = label
         - persistent (False)
         - store_private = (False)
         - visible (False)
         - data_type (object)
         - observable (True)
         - widget_type ('custom')
         
     To use this class, use it like the regular Property or property decorators.
     E.g.:
         attribute = LabeledProperty(...)
     or
         @LabeledProperty(...)
         def get_attribute(self):
             return self.attribute
             
     The setter function is expected to accept either a single argument (the 
     new value) or two arguments (the property descriptor instance and the new 
     value). Similarly, the getter and deleter function are expected to accept
     no arguments or a single argument (the property descriptor function instance).
    """

    #: The actual attribute name used to access the value on the class instance.
    _label = None
    @property
    def label(self): return self._label
    @label.setter
    def label(self, value):
        self._label = value
        # Wrap the underlying variable if needed
        # (e.g. if it's a list, tuple, dict, or other mutable class):
        if self.default is not None:
            self.default = ValueWrapper.wrap_value(self.label, self.default, verbose=bool(value == "specimens"))

    #: Whether this attribute is persistent (needs to be stored)
    persistent = False

    #: Either False (use the actual attribute), True (use the private attribute value) or
    #: the name of the attribute to use when storing this attribute (if persistent = True)
    store_private = False

    #: A short textual description of this attribute
    title = None

    #: A short MathText description of this attribute
    math_title = None

    #: A flag indicating whether this attribute is visible in a GUI
    visible = False

    #: A string describing what kind of GUI widget can be used to display the
    #: contents of this property. Check the :mod:`mvc.adapters` module.
    widget_type = 'custom'

    #: A flag indicating whether this attribute should be visible in a table GUI
    tabular = False

    #: The type of the value stored in the attribute, or in the case of a
    #: collection (i.e. lists, dicts and tuples) the type of the collection
    #: items.
    data_type = object

    #: A flag indicating whether this attribute can be observed for changes
    observable = True

    #: The default value for this property
    default = None

    #: Declaration index: used to allow sorting in order of declaration
    declaration_index = 0

    ############################################################################
    #    Generic private attribute getters and setters
    ############################################################################
    private_attribute_format = "_%(label)s"
    def _get_private_label(self):
        """ Private attribute label (holds the actual value on the model) """
        return self.private_attribute_format % { 'label': self.label }

    def _set(self, instance, value):
        """ Private setter """
        rec_setattr(instance, self._get_private_label(), value)

    def _get(self, instance):
        """ Private getter """
        return rec_getattr(instance, self._get_private_label(), self.default)

    ############################################################################
    #    Decorator calls:
    ############################################################################
    def __call__(self, fget):
        return self.getter(fget)

    def _inject_self(self, f):
        """ Injects self into the arguments of function `f`
           (first argument after self) """
        def wrapper(*args, **kwargs):
            return f(*(args[0] + (self,) + args[1:]), **kwargs)
        return wrapper

    def getter(self, fget):
        # Getter expects to be passed the descriptor
        if len(inspect.getargspec(fget).args) > 1:
            fget = self._inject_self(fget)
        self.fget = fget
        return self

    def setter(self, fset):
        # Setter expects to be passed the descriptor
        if len(inspect.getargspec(fset).args) > 2:
            fset = self._inject_self(fset)
        self.fset = fset
        return self

    def deleter(self, fdel):
        # Deleter expects to be passed the descriptor
        if len(inspect.getargspec(fdel).args) > 1:
            fdel = self._inject_self(fdel)
        self.fdel = fdel
        return self

    ############################################################################
    #    Initialization:
    ############################################################################
    def __init__(self, fget=None, fset=None, fdel=None, doc=None, default=None, label=None, mix_with=None, **kwargs):
        super(LabeledProperty, self).__init__(mix_with=mix_with)

        #Increment declaration counter
        LabeledProperty.declaration_index += 1
        self.declaration_index = LabeledProperty.declaration_index

        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

        self.label = self.math_title = self.title = self.description = label
        self.persistent_label = label
        self.default = default

        for key, value in kwargs.items():
            setattr(self, key, value)

    ############################################################################
    #    Comparison protocol:
    ############################################################################
    def __eq__(self, other):
        # Descriptors are equal if they describe the same attribute
        return other is not None and self.label == other.label

    def __hash__(self):
        return hash(self.label)

    def __neq__(self, other):
        # Descriptors are equal if they describe the same attribute
        return not self.__eq__(other)

    ############################################################################
    #    Descriptor protocol:
    ############################################################################
    def __get__(self, instance, owner):
        if instance is None:
            return self

        with instance._prop_lock:
            if self.fget is None:
                return self._get(instance)
            else:
                return self.fget(instance)

    def __set__(self, instance, value):
        with instance._prop_lock:

            # Get the old value
            old = getattr(instance, self.label)

            # Wrap the new value
            value = ValueWrapper.wrap_value(self.label, value, instance)

            # Set the new value
            if self.fset is None:
                self._set(instance, value)
            else:
                self.fset(instance, value)

            # Notify any observers
            if self.observable:
                # Check if we've really changed it, and send notifications if so:
                if type(instance).check_value_change(old, value):
                    instance._reset_property_notification(self, old)
                    pass

                # Notify any interested party we have set this property!
                if hasattr(instance, 'notify_property_value_change'):
                    instance.notify_property_value_change(self.label, old, value)

    def __delete__(self, instance):
        if self.fdel is None:
            raise AttributeError("Can't delete attribute `%s`!" % self.label)
        self.fdel(instance)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.label)

    pass #end of class
