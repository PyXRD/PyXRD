# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import gtk

from gtkmvc.adapters import Adapter
from generic.controllers.utils import StoreAdapter, ComboAdapter
from generic.views.validators import FloatEntryValidator
from generic.views.widgets import ScaleEntry

widget_handlers = {}

def adjustment_widget_handler(ctrl, intel, widget):
    """ A handler for an expander widget (boolean) """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=gtk.Adjustment.get_value,
        setter=gtk.Adjustment.set_value,
        signal="value-changed"
    )
    return ad
widget_handlers['spin'] = adjustment_widget_handler

def expander_widget_handler(ctrl, intel, widget):
    """ A handler for an expander widget (boolean) """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=lambda w: not w.get_expanded(), setter=gtk.Expander.set_expanded,
        signal="activate"
    )
    return ad
widget_handlers['expander'] = expander_widget_handler

def toggle_widget_handler(ctrl, intel, widget):
    """ A handler for a toggle widget (boolean) """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=gtk.ToggleButton.get_active, setter=gtk.ToggleButton.set_active,
        signal="toggled"
    )
    return ad
widget_handlers['toggle'] = toggle_widget_handler

def check_menu_widget_handler(ctrl, intel, widget):
    """ A handler for a check menu widget (boolean) """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=gtk.CheckMenuItem.get_active, setter=gtk.CheckMenuItem.set_active,
        signal="toggled"
    )
    return ad
widget_handlers['check_menu'] = check_menu_widget_handler

def entry_widget_handler(ctrl, intel, widget):
    """ A handler for an entry widget (text-like) """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=gtk.Entry.get_text, setter=gtk.Entry.set_text,
        wid_type=str, signal="changed"
    )
    return ad
widget_handlers['entry'] = entry_widget_handler

def float_entry_widget_handler(ctrl, intel, widget):
    """ A handler for a float entry widget (adds float validation) """
    FloatEntryValidator(widget) # TODO integrate this...
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=gtk.Entry.get_text, setter=gtk.Entry.set_text,
        wid_type=str, signal="changed"
    )
    return ad
widget_handlers['float_entry'] = float_entry_widget_handler

def scale_widget_handler(ctrl, intel, widget):
    """ A handler for scale widgets (floats) """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=ScaleEntry.get_value, setter=ScaleEntry.set_value,
        wid_type=float
    )
    return ad
widget_handlers['scale'] = scale_widget_handler

def label_widget_handler(ctrl, intel, widget):
    """ A handler for a label widget (text-like) """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=gtk.Label.get_text, setter=gtk.Label.set_text,
        wid_type=str
     )
    return ad
widget_handlers['label'] = label_widget_handler

def arrow_widget_handler(ctrl, intel, widget):
    """ A handler for an arrow widget """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=lambda a: a.get_property("arrow-type"), setter=lambda a, v: a.set(v, a.get_property("shadow-type"))
    )
    return ad
widget_handlers['arrow'] = arrow_widget_handler

def get_color_val(widget):
    c = widget.get_color()
    return "#%02x%02x%02x" % (int(c.red_float * 255), int(c.green_float * 255), int(c.blue_float * 255))

def set_color_val(widget, value):
    col = gtk.gdk.color_parse(value)
    widget.set_color(col)

def color_button_widget_handler(ctrl, intel, widget):
    """ A handler for color widgets (string) """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=get_color_val, setter=set_color_val,
        signal="color-set"
    )
    return ad
widget_handlers['color'] = color_button_widget_handler

def color_selection_widget_handler(ctrl, intel, widget):
    """ A handler for color widgets (string) """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=get_color_val, setter=gtk.ColorSelection.set_current_color,
        signal="color-set"
    )
    return ad
widget_handlers['color-selection'] = color_selection_widget_handler

def text_view_handler(ctrl, intel, widget):
    """ Handler for gtk.TextView widgets """
    ad = StoreAdapter(ctrl.model, intel.name, gtk.TextView.set_buffer)
    ad.connect_widget(widget)
    return ad
widget_handlers['text_view'] = text_view_handler

def tree_view_handler(ctrl, intel, widget):
    """ Handler for gtk.TreeView widgets """
    get_tree_model = getattr(ctrl, 'get_%s_tree_model' % intel.name, None)
    set_tree_model = getattr(ctrl, 'set_%s_tree_model' % intel.name, gtk.TreeView.set_model)
    setup_tree_view = getattr(ctrl, 'setup_%s_tree_view' % intel.name, None)

    ad = StoreAdapter(ctrl.model, intel.name, set_tree_model, get_tree_model)
    ad.connect_widget(widget)
    if callable(setup_tree_view): setup_tree_view(ad._get_store(), widget)

    return ad
widget_handlers['tree_view'] = tree_view_handler

def combo_handler(ctrl, intel, widget):
    ad = ComboAdapter(ctrl.model, intel.name, "_%ss" % intel.name)
    ad.connect_widget(widget)
    setup_combo = getattr(ctrl, 'setup_%s_combo' % intel.name, None)
    if callable(setup_combo): setup_combo(intel, widget)
    return ad
widget_handlers['combo'] = combo_handler

def file_chooser_widget_handler(ctrl, intel, widget):
    """ A handler for a file chooser widgets (string) """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=gtk.FileChooserButton.get_filename, setter=gtk.FileChooserButton.set_filename,
        signal="file-set"
     )
    return ad
widget_handlers['file'] = file_chooser_widget_handler

def link_button_widget_handler(ctrl, intel, widget):
    """ A handler for a link (url) widget (string) """
    ad = Adapter(ctrl.model, intel.name)
    ad.connect_widget(
        widget,
        getter=gtk.LinkButton.get_uri, setter=gtk.LinkButton.set_uri,
        signal="clicked"
    )
    return ad
widget_handlers['link'] = link_button_widget_handler
