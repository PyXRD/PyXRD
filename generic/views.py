# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk
from gtkmvc.view import View

"""
    Basic view providing some common code
"""
class BaseView(View):
    builder = ""
    
    def __init__(self, *args, **kwargs):
        #strip parent from args:
        if "parent" in kwargs:
            self.parent = kwargs["parent"]
            if not hasattr(self, "set_transient_for"): del kwargs["parent"]
        View.__init__(self, *args, **kwargs)
         
    """def show(self, *args, **kwargs): 
        if title != None: self.set_title(title)
        View.show(self)"""
        
    def show_all(self, *args, **kwargs):
        self.show(*args, **kwargs)
        
    def present(self):
        self.get_toplevel().show_all()
        self.get_toplevel().present()
        
    def get_toplevel(self):
        for w in self:
            return self[w].get_toplevel()
            break #just for ref
       
"""
    Mixin that provides title support for views
"""
class TitleView():
    title = None

    def __init__(self):
        if self.title!=None: self.set_title(self.title)

    def set_title(self, title):
        self.title = title
        self.get_toplevel().set_title(title)

"""
    Mixin that provides a function to add childviews to containers
"""
class HasChildView():
    def _add_child_view(self, view, container):
        child = container.get_child()
        if child is not None:
            container.remove(child)
            #child.destroy()
        container.add(view.get_top_widget())
        view.show_all()
        return view

"""
    Generalised view for editing stuff with an OK button
"""
class DialogView(BaseView, TitleView):
    builder = "generic/glade/edit_dialog.glade"
    top = "window_edit_dialog"
    container_widget = "edit_child_box"
    
    #These should be overriden by the subclass:
    subview_builder = ""
    subview_toplevel = None
        
    def __init__(self, container_widget=None, subview_builder=None, subview_toplevel=None, **kwargs):
        BaseView.__init__(self, **kwargs)
        TitleView.__init__(self)
        self.container_widget = container_widget or self.container_widget
        self.subview_builder = subview_builder or self.subview_builder
        self.subview_toplevel = subview_toplevel or self.subview_toplevel
        self.setup_subview()
        return

    def setup_subview(self):
        self._builder.add_from_file(self.subview_builder)
        child = self[self.container_widget].get_child()
        if child is not None:
            self[self.container_widget].remove(child)
        child = self[self.subview_toplevel]
        self[self.container_widget].add(child)
        
"""
    Generalised view for editing objects inside an ObjectListStore (using a customisable child view)
"""
class ObjectListStoreView(DialogView, TitleView, HasChildView):
    subview_builder = "generic/glade/object_store.glade"
    subview_toplevel = "edit_object_store"
    
    edit_view = None
    edit_view_container = "vwp_edit_object"
    
    extra_widget_builder = None
    extra_widget_toplevel = ""
    
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
        if widget != None:
            self["extra_box"].add(widget)
    
    _none_view = None
    @property
    def none_view(self):
        if self._none_view == None:
             self._none_view = NoneView()
        return self._none_view
    
    def __init__(self, edit_view_container=None, load_label=None, save_label=None, **kwargs):
        DialogView.__init__(self, **kwargs)
        TitleView.__init__(self)
        self.edit_view_container = edit_view_container or self.edit_view_container
        self.load_label = load_label or self.load_label
        self.save_label = save_label or self.save_label
        self.extra_widget_box = self["extra_box"]
        if self.extra_widget_builder != None:
            self._builder.add_from_file(self.extra_widget_builder)
            self.extra_widget = self._builder.get_object(self.extra_widget_toplevel)
        return

    def set_edit_view(self, view):
        self.edit_view = view
        return self._add_child_view(view, self[self.edit_view_container])
        
class NoneView(BaseView):
    builder = "generic/glade/none.glade"
    top = "lbl_caption"
    caption_widget = "lbl_caption"

    def __init__(self, label="Nothing selected.", **kwargs):
        BaseView.__init__(self, **kwargs)
        self._label = self[self.caption_widget]
        #self.label = label
        
    _label = None
    @property
    def label(self):
        return self._label.get_label()
    
    @label.setter
    def label(self, value):
        self._label.set_label(value)
