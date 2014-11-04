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

from warnings import warn

# Mapping of widget types to data_type.
# These are here to constrain certain widget types to certain data types.
# For some widgets this does not make sense (e.g. combo boxes)
# as these can be mapped to virtually any type. In those case use the string "*"
# to indicate these are all-round widget types.
# This map is also used to populate the widget_type field in the PropIntel instances
# if the user did not provide one explicitly. All-round widget types are ignored
# for the automatic mapping.
import types

# TODO move the information in the list below
# into the toolkit specific adapters (that implement the 'widget_type' strings)
# make sure the adapter_registry stores this information in an easily accessible
# place so we can query what type of widget adapter we should use for a specific
# data type

widget_types = [
    # defaults:

    ('scale', types.FloatType), # Default for floats
    ('float_entry', types.FloatType),
    ('entry', types.FloatType),
    ('spin', types.FloatType),
    ('label', types.FloatType),

    ('entry', types.UnicodeType), # Default for strings
    ('entry', types.StringType), # Default for strings
    ('label', types.StringType),
    ('color', types.StringType),
    ('color-selection', types.StringType),
    ('file', types.StringType),
    ('link', types.StringType),
    ('text_view', types.StringType),

    ('spin', types.IntType), # Default for integers
    ('label', types.IntType),
    ('entry', types.IntType),

    ('toggle', types.BooleanType), # Default for booleans
    ('check_menu', types.BooleanType),
    ('expander', types.BooleanType),

    # ('arrow', gtk.ArrowType), # Default for arrows, not used for now

    ('custom', types.ObjectType), # Default for objects
    ('xy_list_view', types.ObjectType),
    ('object_list_view', types.ObjectType),
    ('object_tree_view', types.ObjectType),
    ('text_view', types.ObjectType),

    ('combo', "*"), # Final 'catch all'...
]

class PropIntel(object):
    """
        A property meta-data container
    """

    # Private property format (holds the actual value on the model)
    private_name_format = "_%(prop_name)s"
    def get_private_name(self):
        return self.private_name_format % { 'prop_name': self.name }

    # Public getter name format (to access private property)
    getter_format = "get_%(prop_name)s"
    def get_getter_name(self):
        return self.getter_format % { 'prop_name': self.name }

    # Public setter name format (to access private property)
    setter_format = "set_%(prop_name)s"
    def get_setter_name(self):
        return self.setter_format % { 'prop_name': self.name }

    refinement_info_format = "%(prop_name)s_ref_info"
    def get_refinement_info_name(self):
        return self.refinement_info_format % { 'prop_name': self.name }

    math_label = None
    text_label = None
    label = None

    ST = dict(
        storable=True
    )

    WID = dict(
        has_widget=True
    )

    COL = dict(
        is_column=True,
    )

    WID_COL = dict(
        has_widget=True,
        is_column=True
    )

    ST_WID = dict(
        has_widget=True,
        storable=True
    )

    ST_WID_COL = dict(
        has_widget=True,
        storable=True,
        is_column=True
    )

    REF_ST_WID = dict(
        refinable=True,
        has_widget=True,
        storable=True
    )

    inh_name = None
    inh_from = None
    stor_name = None

    minimum = 0.0
    maximum = 0.0

    is_column = False
    data_type = object # type of the value instance

    widget_type = 'input' # string description of the widget type
    widget_handler = None
    refinable = False
    storable = False
    observable = True
    has_widget = False

    def __init__(self, **kwargs):
        object.__init__(self)

        self.label = ""

        if "ctype" in kwargs:
            # deprecated and ignored!
            kwargs.pop("ctype")
            warn("The use of the keyword '%s' is deprecated for %s!" % ("ctype", type(self)), DeprecationWarning)

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        # check if the widget type matches with the data type:
        if 'widget_type' in kwargs:
            data_type = None
            for wid, tp in widget_types:
                tp = tp if tp != "*" else self.data_type
                if wid == self.widget_type and tp == self.data_type:
                    data_type = tp
            if data_type != self.data_type:
                raise AttributeError, "Data type '%s' does not match with widget type '%s'!" % (self.data_type, self.widget_type)
        else:
            # if the widget type is not explicitly set,
            # set manually:
            self.widget_type = self._get_default_widget_type()

    def expand(self, cls):
        if self.refinable:
            attr_name = self.get_refinement_info_name()
            new_prop = PropIntel(name=attr_name, data_type=object, storable=True)
            return [(attr_name, None)], [new_prop, ]
        else:
            return [], []

    def __eq__(self, other):
        return other is not None and self.name == other.name

    def __neq__(self, other):
        return other is not None and self.name != other.name

    def _get_default_widget_type(self):
        for wid, tp in widget_types:
            if tp == self.data_type:
                return wid

    def __repr__(self):
        return "PropIntel(name=%r, data_type=%r, observable=%r, storable=%r)" % (
            self.name, self.data_type, self.observable, self.storable)

    pass # end of class

class OptionPropIntel(PropIntel):
    """
        A property meta-data container for properties which have a
        value limited to a number of options
    """

    widget_type = "option_list"
    def _get_default_widget_type(self):
        return "option_list"

    def mapper(self, value):
        return self.data_type(value)
    options = []

    def expand(self, cls):
        new_attrs, new_props = super(OptionPropIntel, self).expand(cls)

        pr_prop = self.get_private_name()
        pr_optn = "%ss" % pr_prop
        getter_name = self.get_getter_name()
        setter_name = self.get_setter_name()

        # Add private attribute if not there yet:
        if not hasattr(cls, pr_prop):
            if self.default is not None:
                new_attrs.append((pr_prop, self.default))
            else:
                new_attrs.append((pr_prop, self.options.values()[0]))

        # Option list:
        new_attrs.append((pr_optn, self.options))

        # Wrap getter and setter:
        ex_getter = getattr(cls, getter_name, None)
        ex_setter = getattr(cls, setter_name, None)
        getter, setter = self._wrap_accesors(pr_prop, ex_getter, ex_setter)
        new_attrs.append((getter_name, getter))
        new_attrs.append((setter_name, setter))

        return new_attrs, new_props

    def _wrap_accesors(self, prop, existing_getter=None, existing_setter=None):
        def getter(model):
            if callable(existing_getter):
                return existing_getter(model)
            else:
                return getattr(model, prop)
        def setter(model, value):
            value = self.mapper(value)
            if value in self.options:
                if callable(existing_setter):
                    existing_setter(model, value)
                else:
                    setattr(model, prop, value)
            else:
                raise ValueError, "'%s' is not a valid value for %s!" % (value, prop)
        return getter, setter

    pass # end of class

class UUIDPropIntel(PropIntel):
    """
        A property meta-data container for a UUID property
    """

    def expand(self, cls):
        new_attrs, new_props = super(UUIDPropIntel, self).expand(cls)

        pr_prop = self.get_private_name()
        getter_name = self.get_getter_name()
        setter_name = self.get_setter_name()

        def get_uuid(self):
            """The unique user id (UUID) for this object"""
            return self._uuid

        def set_uuid(self, value):
            type(cls).object_pool.remove_object(self)
            self._uuid = value
            type(cls).object_pool.add_object(self)

        new_attrs.append((getter_name, get_uuid))
        new_attrs.append((setter_name, set_uuid))
        new_attrs.append((pr_prop, None))

        return new_attrs, new_props

    pass # end of class
