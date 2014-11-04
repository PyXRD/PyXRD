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

from contextlib import contextmanager

from ..support.utils import not_none
from ..observers import Observer
from ..models import Model, PropIntel
from .abstract_adapter import AbstractAdapter

class ModelAdapter(Observer, AbstractAdapter):
    """
        Model-side implementation of the _AbstractAdapter interface.
    """

    # Mode-side property handling:
    _prop_read = None
    _prop_write = None
    _value_error = None

    @property
    def property_name(self):
        """Returns the property name the adapter is connected to"""
        return self._prop.name

    _ignoring_notifs = False
    @contextmanager
    def _ignore_notifications(self):
        """Context manager to temporarily (and exception-safe) ignore
        property changed notifications (e.g. when we're setting the model
        from the widget and vice versa)"""
        self._ignoring_notifs = True
        yield
        self._ignoring_notifs = False

    def __init__(self, *args, **kwargs):
        """
        Abstract class that implements the model side of the adapter.
        For a fully implemented class check the corresponding widget toolkit
        modules. 

        This class handles only assignments to properties. For other
        kinds of setting (e.g. user-defined classes used as
        observable properties, containers, etc.) use other types of
        Adapters derived from this class.
        
        Controller is the controller creating this Adapter.
        Prop is either a PropIntel instance taken from the controller's
        model, or a 'dotted string' describing a property from the controller's
        model. E.g. it is possible to pass: a.b.c which will then result in 
        property c from attribute b from attribute a from the controller's
        model to be observed. This way nested properties can also be handled.
        
        prop_{read, write} are two optional functions that apply
        custom modifications to the value of the property after
        reading and before setting it on the model (e.g. transforming a float
        to a string and vice-versa). Both take a value and must return a
        transformed value.
        
        value_error can be a function to be called when a ValueError exception
        occurs while trying to set an invalid value for the property on the
        model. The function will receive: the adapter, the property name and
        the value coming from the widget that offended the model.

        spurious controls if the adapter should receive spurious
        changes from the model (see spuriousness in class Observer for
        further information).
        """
        controller = args[0]
        prop = args[1]
        widget = args[2]

        prop_read = kwargs.pop("prop_read", None)
        prop_write = kwargs.pop("prop_write", None)
        value_error = kwargs.pop("value_error", None)
        spurious = kwargs.get("spurious", False)

        # First parse (optional) property strings:
        prop, self._model = self._parse_prop(prop, controller.model)

        # Call base __init__'s:
        super(ModelAdapter, self).__init__(*args, **kwargs)

        # Mode-side property handling:
        self._prop_read = not_none(prop_read, self._prop_read)
        self._prop_write = not_none(prop_write, self._prop_write)
        self._value_error = not_none(value_error, self._value_error)

        # Connect the model
        self._connect_model()
        return

    # ----------------------------------------------------------------------
    #  Model connecting & disconnecting:
    # ----------------------------------------------------------------------
    def _parse_prop(self, prop, model):
        """Parses (optional) prop strings for the given model"""
        if not isinstance(prop, PropIntel):
            parts = prop.split(".")
            if len(parts) > 1:
                # identifies the model
                models = parts[:-1]
                for name in models:
                    model = getattr(model, name)
                    if not isinstance(model, Model):
                        raise TypeError(
                            "Attribute '%s' was expected to be a " +
                            "Model, but found: '%s'" % (name, model))
                prop = model.Meta.get_prop_intel_by_name(parts[-1])
            else: prop = parts[0]
        return prop, model

    def _connect_model(self):
        """Used internally to connect the property into the model, and
        register self as a value observer for that property"""

        # prop is inside model?
        if not hasattr(self._model, self._prop.name):
            raise ValueError("Attribute '" + self._prop.name +
                             "' not found in model " + str(self._model))

        # is it observable?
        if self._prop.observable:
            self.observe(self._on_prop_changed, self._prop.name, assign=True)
            self.observe_model(self._model)

    def _on_prop_changed(self, *args, **kwargs):
        """Called by the observation code, when the value in the
        observed property is changed"""
        if not self._ignoring_notifs:
            self.update_widget()

    def _disconnect_model(self, model=None):
        # disconnects the model
        model = not_none(self._model, model)
        if model is not None:
            self.relieve_model(self._model)
            self._model = None

    # ----------------------------------------------------------------------
    #  Model-side reading and writing
    # ----------------------------------------------------------------------
    def _get_property_value(self):
        """Private method that returns the property value currently stored
        in the model, without transformations."""
        return getattr(self._model, self._prop.name)

    def _set_property_value(self, val):
        """Private method that sets the property value stored in the model,
        without transformations."""
        return setattr(self._model, self._prop.name, val)

    def _read_property(self, *args):
        """Returns the (possibly transformed) property value stored in the 
        model"""
        if self._prop_read: return self._prop_read(self._get_property_value(*args))
        return self._get_property_value(*args)

    def _write_property(self, value, *args):
        """Sets the value of property. The given value is transformed
        using the prop_write function passed to the constructor.
        An attempt at casting the value to the property type is also made."""
        raw_value = value
        try:
            # transform if needed:
            if self._prop_write: value = self._prop_write(value)

            # set the property, ignore updates:
            with self._ignore_notifications():
                self._set_property_value(value, *args)

        except ValueError:
            # let the user handle the error if he wants that:
            if self._value_error:
                self._value_error(self, self._prop.name, raw_value)
            else:
                raise

    pass # end of class
