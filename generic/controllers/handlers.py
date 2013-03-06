# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os
from warnings import warn

from gtkmvc.adapters import Adapter
from generic.views.validators import FloatEntryValidator
import settings

# Mapping of widget types to data_type, these need to match, and are also
# used to automatically populate the field if not passed in the init of PropIntel:
widget_types = [
    #defaults:
    ('scale', float),
    ('input', unicode),
    ('spin', int),
    ('custom', object),
    ('check', bool),
    
    #valid alternatives:
    ('float_input', float),
    ('input', float),
    #('custom', float),
    ('color', str),
    #('custom', str),
    ('list', object),
    ('tree', object),
    ('combo', object),
    ('input', object),

]    

# List of tuples containg a widget type and its handler, should not be modified
# directly, but using register_widget_handler decorator
widget_handlers = dict()

def register_handler(widget_type, override=True):
    """ Decorator used for registering default widget handlers """
    def wrapper(func):
        if not (widget_type in widget_handlers and not override):
            widget_handlers[widget_type] = func
            func.widget_type = widget_type
        return func
    return wrapper

@register_handler('scale')
def scale_widget_handler(ctrl, intel, widget_format):
    """ A handler for scale widgets (floats) """
    widget = None
    #First check if widget is already present:
    if widget_format % intel.name in ctrl.view:
        widget = ctrl.view[widget_format % intel.name]
    else:
        # if not create and add to the view:
        widget = ctrl.view.add_scale_widget(intel, widget_format=widget_format)
    #adapt the widget to the model property:
    adapter = Adapter(ctrl.model, intel.name)
    adapter.connect_widget(widget)
    ctrl.adapt(adapter)
    return True

@register_handler('color')
def color_widget_handler(ctrl, intel, widget_format):
    """ A handler for color widgets (string) """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(ctrl.view[widget_format % intel.name], getter=get_color_val)
    ctrl.adapt(ad)
    return True
    
@register_handler('float_input')    
def float_input_widget_handler(ctrl, intel, widget_format):
    """ Handler for float inputs (adds validation) """
    FloatEntryValidator(ctrl.view[widget_format % intel.name])
    ctrl.adapt(intel.name, widget_format % intel.name)
    return True
    
@register_handler('check')
@register_handler('input')
def default_widget_handler(ctrl, intel, widget_format):
    """ Default handler leaving everything to gtkmvc """
    ctrl.adapt(intel.name, widget_format % intel.name)
    return True
    
def get_color_val(widget):
    c = widget.get_color()
    return "#%02x%02x%02x" % (int(c.red_float*255), int(c.green_float*255), int(c.blue_float*255))
