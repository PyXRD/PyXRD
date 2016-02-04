# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pkg_resources import resource_filename # @UnresolvedImport

from itertools import imap
from warnings import warn

import gtk
from mvc.view import View

from pyxrd.data import settings
from mvc.adapters.gtk_support.widgets import ScaleEntry
from pyxrd.generic.mathtext_support import create_image_from_mathtext
from pyxrd.generic.models.mathtext_support import get_string_safe

class BaseView(View):
    """
        Basic view providing some common code
        TODO attribute docs!
    """
    builder = ""
    modal = False
    resizable = True
    widget_format = "%s"

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
        if isinstance(top, gtk.Window):
            top.set_resizable(self.resizable)
            top.set_modal(self.modal)
        if self.parent:
            self.set_layout_mode(self.parent.current_layout_state)

    def create_mathtext_widget(self, text, fallback_text=""):
        try:
            widget = create_image_from_mathtext(text)
        except:
            if fallback_text: text = fallback_text
            widget = gtk.Label(text)
            widget.set_use_markup(True)
            widget.set_property('justify', gtk.JUSTIFY_CENTER)
        return widget

    def add_scale_widget(self, intel, widget_format="default_%s", container=None, enforce_range=True):
        if not isinstance(container, gtk.Widget):
            container = self[(container or "container_%s") % intel.name]
            if container == None:
                warn("Scale widget container not found for '%s'!" % intel.name, Warning)
                return None
        name = widget_format % intel.name
        child = container.get_child()
        if child is not None:
            container.remove(child)
        inp = ScaleEntry(intel.minimum, intel.maximum, enforce_range=enforce_range)
        self[name] = inp
        container.add(inp)
        inp.show_all()
        return inp

    def set_layout_mode(self, state):
        self.current_layout_state = state
        for action in self.layout_state_actions.get(state, []):
            parts = tuple(action.split("::", 1))
            command, group_name = parts
            widgets = []
            if group_name != "all":
                widget_names = self.widget_groups.get(group_name, [])
                widgets = imap(lambda name: self[name], widget_names)
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
                raise ValueError, "Unknown layout state command `%s`!" % command

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
        for w in self:
            if hasattr(self[w], 'get_toplevel'):
                return self[w].get_toplevel()
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
        if isinstance(container, gtk.ScrolledWindow) and not (type(new_child) in (gtk.TextView, gtk.TreeView, gtk.IconView, gtk.Viewport)):
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
        self[self.edit_view_container].set_size_request(sr[0] + 20, -1)

    def set_edit_view(self, view):
        if self._on_sr_id is not None and self.child_view is not None:
            self.child_view.disconnect(self._on_sr_id)
        self.edit_view = view
        self.child_view = view.get_top_widget()
        self._add_child_view(self.child_view, self[self.edit_view_container])
        if isinstance(self[self.edit_view_container], gtk.ScrolledWindow):
            sr = self.child_view.get_size_request()
            self[self.edit_view_container].set_size_request(sr[0], -1)
            self[self.edit_view_container].set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
            self._on_sr_id = self.child_view.connect("size-request", self.on_size_requested)


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
