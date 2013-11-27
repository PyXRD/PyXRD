# coding=UTF-8
# ex:ts=4:sw=4:et=on
from warnings import warn

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

# Mapping of widget types to data_type.
# These are here to constrain certain widget types to certain data types.
# For some widgets this does not make sense (e.g. combo boxes)
# as these can be mapped to virtually any type. In those case use the string "*"
# to indicate these are all-round widget types.
# This map is also used to populate the widget_type field in the PropIntel instances
# if the user did not provide one explicitly. All-round widget types are ignored
# for the automatic mapping.
import types

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
    ('tree_view', types.ObjectType),
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
    
    label = "" # TODO what about dynamic labels?
    # For this to work, we need to replace all PropIntels 
    # with a copy on which we can set the instance in which they're contained.
    # Otherwise we're re-setting the container everytime a new instance is created! 

    inh_name = None
    stor_name = None

    minimum = None
    maximum = None
    
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

    def __eq__(self, other):
        return other is not None and self.name == other.name

    def __neq__(self, other):
        return other is not None and self.name != other.name

    def _get_default_widget_type(self):
        for wid, tp in widget_types:
            if tp == self.data_type:
                return wid

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
    
    def __create_accesors__(self, prop, existing_getter=None, existing_setter=None):
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
    
    
    