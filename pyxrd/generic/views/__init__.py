# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

from pkg_resources import resource_filename # @UnresolvedImport
from warnings import warn

import gi
gi.require_version('Gtk', '3.0')  # @UndefinedVariable
from gi.repository import Gtk  # @UnresolvedImport

from mvc.view import View
from mvc.adapters.gtk_support.widgets import ScaleEntry

from pyxrd.data import settings
from pyxrd.generic.mathtext_support import get_string_safe

class BaseView(View):
    """
        Basic view providing some common code
        TODO attribute docs!
    """
    builder = ""
    modal = False
    resizable = True
    widget_format = "%s"
    container_format = "container_%s"

    # A mapping of layout states and actions to be taken when switching to them.
    # Actions should be of the form `action::widget_group`, where the action is one
    # of either hide or show and the widget_group is a key in the `widget_groups`
    # mapping, with the value being the list of widgets to apply the action on to.
    current_layout_state = "FULL"
    layout_state_actions = {
        'FULL': [
            'show::full_mode_only'
        ],
        'VIEWER': [
            'hide::full_mode_only'
        ]
    }
    widget_groups = { }

    def __init__(self, *args, **kwargs):
        super(BaseView, self).__init__(*args, **kwargs)
        self.parent = kwargs.get("parent", None)
        top = self.get_toplevel()
        if isinstance(top, Gtk.Window):
            top.set_resizable(self.resizable)
            top.set_modal(self.modal)
        if self.parent:
            self.set_layout_mode(self.parent.current_layout_state)

    def create_mathtext_widget(self, text, fallback_text=""):
        # TODO move these to a separate controller namespace module!
        try:
            from pyxrd.generic.mathtext_support import create_image_from_mathtext
            widget = create_image_from_mathtext(text)
        except:
            if fallback_text: text = fallback_text
            widget = Gtk.Label(label=text)
            widget.set_use_markup(True)
            widget.set_justify(Gtk.Justification.CENTER)
        return widget

    def _get_widget_container(self, prop):
        return self[self.container_format % prop.label]

    def _add_widget_to_container(self, widget, container):
        if container is not None:
            child = container.get_child()
            if child is not None:
                container.remove(child)
            container.add(widget)
        widget.show_all()
        return widget

    def add_widget(self, prop, *args, **kwargs):
        method = {
           str: self.add_entry_widget,
           float: self.add_scale_widget,
        }.get(prop.data_type, None)
        if method is not None:
            return method(prop, *args, **kwargs)

    def add_scale_widget(self, prop, enforce_range=True):
        # Create the widget:        
        inp = ScaleEntry(prop.minimum, prop.maximum, enforce_range=enforce_range)
        inp.set_tooltip_text(prop.title)
        self[self.widget_format % prop.label] = inp
            
        # Add & return the widget
        return self._add_widget_to_container(inp, self._get_widget_container(prop))

    def add_entry_widget(self, prop):
        # Create the widget:        
        inp = Gtk.Entry()
        inp.set_tooltip_text(prop.title)
        self[self.widget_format % prop.label] = inp

        # Add & return the widget
        return self._add_widget_to_container(inp, self._get_widget_container(prop))

    def create_input_table(self, table, props, num_columns = 1, widget_callbacks=[]):
        """
            Places widgets (returned by the widget_callbacks) in the given table
            for each property in props. The widget groups (i.e. list of widgets 
            returned by the callbacks for a single property) can be placed in a
            multi-column layout by increasing the num_columns value.
        """
        # total number of properties
        num_props = len(props)
        # number of widgets in each column
        column_width = len(widget_callbacks)
        # 2D array of widgets (each row is a group of widgets returned for a property)
        widgets = [[None for _ in range(column_width)] for _ in range(num_props)]  
        
        # The actual number of rows needed in the table
        num_table_rows = int(num_props / num_columns)
        # The actual number of columns needed in the table
        num_table_columns = num_columns*column_width
        
        # Resize the table widget accordingly
        table.resize(num_table_rows,  num_table_columns)          

        for i, prop in enumerate(props): # i = 0, 1, 2, 3, ...
            # Calculate the column: column_index = 0, cw, 2*cw, 3*cw, ...
            column_index = (i % num_columns) * column_width                
            for widget_index in range(column_width):
                # Create the widget:
                widget = widget_callbacks[widget_index](prop)
                
                # Store it for the return value:
                widgets[i][widget_index] = widget
                
                # Calculate where to place the widget:
                column_offset = column_index + widget_index
                row_offset = int(i / num_columns)
                
                # Attach it to the table               
                table.attach(
                    widget,
                    column_offset, column_offset + 1,
                    row_offset, row_offset + 1,
                    xpadding=2, ypadding=2
                )
        return widgets

    def set_layout_mode(self, state):
        self.current_layout_state = state
        for action in self.layout_state_actions.get(state, []):
            parts = tuple(action.split("::", 1))
            command, group_name = parts
            widgets = []
            if group_name != "all":
                widget_names = self.widget_groups.get(group_name, [])
                widgets = map(lambda name: self[name], widget_names)
            else:
                widgets = self._builder.get_objects()

            if command == "show":
                for widget in widgets:
                    try:
                        widget.set_no_show_all(False)
                        widget.show_all()
                    except AttributeError:
                        pass
            elif command == "hide":
                for widget in widgets:
                    try:
                        widget.set_no_show_all(True)
                        widget.set_visible(False)
                    except AttributeError:
                        pass
            else:
                raise ValueError("Unknown layout state command `%s`!" % command)

    def show_all(self, *args, **kwargs):
        self.show(*args, **kwargs)

    def present(self):
        toplevel = self.get_toplevel()
        toplevel.set_resizable(self.resizable)
        toplevel.set_modal(self.modal)
        toplevel.show_all()
        toplevel.present()
        self.show()

    def get_toplevel(self):        
        for w in [self.top,] + list(self):
            try:
                return self[w].get_toplevel()
            except AttributeError:
                pass
            else:
                break # just for ref

class TitleView(BaseView):
    """
        Mix-in that provides title support for views.
        The class attribute 'title' can be set, if so, this class will
        attempt to set the title attribute upon initialization unless it is 'None'. 
    """
    title = None

    def __init__(self, *args, **kwargs):
        super(TitleView, self).__init__(*args, **kwargs)
        if self.title is not None: self.set_title(self.title)

    def set_title(self, title):
        self.title = title
        self.get_toplevel().set_title(title)

    pass # end of class

class FormattedTitleView(TitleView):
    """
        Mix-in that provides a formatted title support for views.
        The 'title_format' class attribute should be set to a string format
        containing a single string (%s) specifier. When set_title is called, 
        only that part of the string is updated.
    """
    title_format = "%s"
    title = ""

    def set_title(self, title, *args, **kwargs):
        self.title = title
        self.get_toplevel().set_title(self.title_format % self.title)

    pass # end of class

class HasChildView(object):
    """
        Mixin that provides a function to add childviews to containers
    """
    def _add_child_view(self, new_child, container):
        child = container.get_child()
        if child is not None:
            container.remove(child)
        if isinstance(container, Gtk.ScrolledWindow) and not (type(new_child) in (Gtk.TextView, Gtk.TreeView, Gtk.IconView, Gtk.Viewport)):
            container.add_with_viewport(new_child)
        else:
            container.add(new_child)
        new_child.show_all()
        return new_child

    pass # end of class

class DialogView(HasChildView, TitleView):
    """
        Generalised view for editing stuff with an OK button
    """
    builder = resource_filename(__name__, "glade/edit_dialog.glade")
    top = "window_edit_dialog"
    container_widget = "edit_child_box"

    # These should be overriden by the subclass:
    subview_builder = ""
    subview_toplevel = None

    def __init__(self, container_widget=None, subview_builder=None, subview_toplevel=None, *args, **kwargs):
        self.container_widget = container_widget or self.container_widget
        self.subview_builder = subview_builder or self.subview_builder
        self.subview_toplevel = subview_toplevel or self.subview_toplevel
        super(DialogView, self).__init__(*args, **kwargs)
        self._builder.add_from_file(self.subview_builder)
        self._add_child_view(self[self.subview_toplevel], self[self.container_widget])
        return


class ObjectListStoreViewMixin(HasChildView):
    edit_view = None
    edit_view_container = "vwp_edit_object"

    extra_widget_builder = None
    extra_widget_toplevel = ""

    treeview_widget = "edit_objects_treeview"

    @property
    def treeview(self):
        return self[self.treeview_widget]

    @property
    def load_label(self):
        return self["button_load_object"].get_label()

    @load_label.setter
    def load_label(self, value):
        self["button_load_object"].set_label(value)

    @property
    def save_label(self):
        return self["button_save_object"].get_label()

    @save_label.setter
    def save_label(self, value):
        self["button_save_object"].set_label(value)

    @property
    def extra_widget(self):
        return self.extra_widget_box.get_child()

    @extra_widget.setter
    def extra_widget(self, widget):
        child = self.extra_widget_box.get_child()
        if child:
            self.extra_widget_box.remove(child)
        if widget is not None:
            self["extra_box"].add(widget)

    _none_view = None
    @property
    def none_view(self):
        return NoneView()

    def set_selection_state(self, value):
        """
            Sets the state of the view to correspond with the number of currently
            selected objects. Value is either None or a number indicating the number of selected objects.
        """
        self["button_del_object"].set_sensitive(value is not None)
        self["button_save_object"].set_sensitive(value is not None)

    def __init__(self, edit_view_container=None, display_buttons=True, load_label=None, save_label=None, **kwargs):
        self.edit_view_container = edit_view_container or self.edit_view_container
        self.load_label = load_label or self.load_label
        self.save_label = save_label or self.save_label

        if not display_buttons:
            self["vbox_objects"].remove(self["table_data"])

        self.extra_widget_box = self["extra_box"]
        if self.extra_widget_builder is not None:
            self._builder.add_from_file(self.extra_widget_builder)
            self.extra_widget = self._builder.get_object(self.extra_widget_toplevel)
        return

    _on_sr_id = None
    def on_size_requested(self, *args):
        sr = self.child_view.size_request()
        self[self.edit_view_container].set_size_request(sr.height + 20, -1)

    def set_edit_view(self, view):
        if self._on_sr_id is not None and self.child_view is not None:
            self.child_view.disconnect(self._on_sr_id)
        self.edit_view = view
        self.child_view = view.get_top_widget()
        self._add_child_view(self.child_view, self[self.edit_view_container])
        if isinstance(self[self.edit_view_container], Gtk.ScrolledWindow):
            sr = self.child_view.get_size_request()
            self[self.edit_view_container].set_size_request(sr[0], -1)
            self[self.edit_view_container].set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            self._on_sr_id = self.child_view.connect("size-allocate", self.on_size_requested)


        return self.edit_view

class ObjectListStoreView(ObjectListStoreViewMixin, DialogView):
    """
        Generalised view for editing objects inside an ObjectListStore (using a customisable child view)
         - Standalone version (inside a DialogView)
    """
    subview_builder = resource_filename(__name__, "glade/object_store.glade")
    subview_toplevel = "edit_object_store"

    def __init__(self, edit_view_container=None, display_buttons=True, load_label=None, save_label=None, **kwargs):
        DialogView.__init__(self, **kwargs)
        ObjectListStoreViewMixin.__init__(self, edit_view_container=edit_view_container, display_buttons=display_buttons, load_label=load_label, save_label=save_label, **kwargs)

class ChildObjectListStoreView(ObjectListStoreViewMixin, BaseView):
    """
        Generalised view for editing objects inside an ObjectListStore (using a customisable child view)
         - Child version (to be embedded by a controller)
    """
    edit_view_container = "frame_object_param"

    builder = resource_filename(__name__, "glade/object_store.glade")
    top = "edit_object_store"

    def __init__(self, edit_view_container=None, display_buttons=True, load_label=None, save_label=None, **kwargs):
        BaseView.__init__(self, **kwargs)
        ObjectListStoreViewMixin.__init__(self, edit_view_container=edit_view_container, display_buttons=display_buttons, load_label=load_label, save_label=save_label, **kwargs)

        self["frm_objects_tv"].set_size_request(150, 150)

class InlineObjectListStoreView(BaseView):
    builder = resource_filename(__name__, "glade/inline_ols.glade")
    top = "edit_item"

    @property
    def treeview(self):
        return self['tvw_items']

    @property
    def del_item_widget(self):
        return self['btn_del_item']

    @property
    def add_item_widget(self):
        return self['btn_add_item']

    @property
    def export_items_widget(self):
        return self['btn_export_item']

    @property
    def import_items_widget(self):
        return self['btn_import_item']

    @property
    def type_combobox_widget(self):
        return self['cmb_add_type']

class NoneView(BaseView):
    builder = resource_filename(__name__, "glade/none.glade")
    top = "lbl_caption"
    caption_widget = "lbl_caption"

    def __init__(self, label=None, **kwargs):
        BaseView.__init__(self, **kwargs)
        self._label = self[self.caption_widget]
        if label is not None: self.label = label

    _label = None
    @property
    def label(self):
        return self._label.get_label()

    @label.setter
    def label(self, value):
        self._label.set_label(value)
