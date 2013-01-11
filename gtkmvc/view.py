#  Author: Roberto Cavada <roboogle@gmail.com>
#  Modified by: Guillaume Libersat <glibersat AT linux62.org>
#
#  Copyright (c) 2005 by Roberto Cavada
#  Copyright (c) 2007 by Guillaume Libersat
#
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

from gtkmvc.controller import Controller
from gtkmvc.support.log import logger
from gtkmvc.support.exceptions import ViewError

import gtk
import sys

try:
    from gtk import glade as gtkglade
    __glade_is_available__ = True
except ImportError: __glade_is_available__ = False

try:
    from gtk import Builder
    __builder_is_available__ = True
except ImportError: __builder_is_available__ = False

# verbose message
if not __glade_is_available__ or not __builder_is_available__:
    logger.warn({(False, False) : "both glade and gtk.Builder are not available: relying only on manual widgets in views",
              (False, True) : "gtk.Builder is not available, relying on manual and glade based views only", 
              (True, False) : "glade is not available, relying on manual and gtk.Builder based views only", 
}[(__builder_is_available__, __glade_is_available__)])
    pass
    
import types
# ----------------------------------------------------------------------

class View (object):
    glade = None
    top=None
    builder=None
    
    def __init__(self, glade=None, top=None,
                 parent=None, 
                 builder=None):
        """
        Only the first three may be given as positional arguments. If an
        argument is empty a class attribute of the same name is used. This
        does not work for *parent*.

        *glade* is a path to an XML file defining widgets in libglade format.
        
           .. deprecated:: 1.99.1

        *builder* is a path to an XML file defining widgets in GtkBuilder
        format.

           .. versionadded:: 1.99.1

        *top* is a string or a list of strings containing the names of our top
        level widgets. When using libglade only their children are loaded.

        *parent* is used to call :meth:`set_parent_view`.

        The last two only work if *glade* or *builder* are used, not if you
        intend to create widgets later from code.

        .. deprecated:: 1.99.1
           In future versions the functionality will be split into the new class
           :class:`ManualView` and its child :class:`BuilderView`.
        """
        if isinstance(glade, Controller):
            raise NotImplementedError("This version of GTKMVC does not"
                " support the 1.2 API")
        if isinstance(builder, Controller):
            raise NotImplementedError("This version of GTKMVC does not"
                " support the 1.99.0 API")
        if parent and not isinstance(parent, View):
            raise NotImplementedError("This version of GTKMVC does not"
                " support the unreleased first GtkBuilder API")

        self.manualWidgets = {}
        self.autoWidgets = {}
        self.__autoWidgets_calculated = False
        
        self.glade_xmlWidgets = []
        
        # Sets a callback for custom widgets
        if __glade_is_available__:
            gtkglade.set_custom_handler(self._custom_widget_create)
            pass

        if top: _top = top
        else: _top = self.top
        if type(_top) == types.StringType or _top is None:
            wids = (_top,)
        else: wids = _top  # Already a list or tuple

        # retrieves XML objects from glade
        if glade: _glade = glade
        else: _glade = self.glade

        if _glade is not None:
            if not __glade_is_available__:
                raise ViewError("Module gtk.glade was required, but not available")
            for wid in wids:
                self.glade_xmlWidgets.append(gtkglade.XML(_glade, wid))
                pass
            pass

        # retrieves objects from builder if available
        if builder: _builder = builder
        else: _builder = self.builder
        if _builder is not None:
            if not __builder_is_available__:
                raise ViewError("gtk.Builder was used, but is not available")

            # if the user passed a Builder, use it as it is, otherwise
            # build one
            if isinstance(_builder, gtk.Builder):
                self._builder = _builder
            else:
                self._builder = gtk.Builder()
                self._builder.add_from_file(_builder)
                pass
            pass
        else: self._builder = None # no gtk builder
            
        # top widget list or singleton:
        if _top is not None:
            if len(wids) > 1:
                self.m_topWidget = []
                for i in range(0, len(wids)):
                    self.m_topWidget.append(self[wids[i]])
                    pass
            else: self.m_topWidget = self[wids[0]]
        else:  self.m_topWidget = None
       
        if parent is not None: self.set_parent_view(parent)

        return
       
    def __getitem__(self, key):
        """
        Return the widget named *key*, or ``None``.
        
        .. note::
        
           In future versions this will likely change to raise ``KeyError``.
        """
        wid = None

        # first try with manually-added widgets:
        if self.manualWidgets.has_key(key):
            wid = self.manualWidgets[key]
            pass

        if wid is None:
            # then try with glade and builder, starting from memoized 
            if self.autoWidgets.has_key(key): wid = self.autoWidgets[key]
            else:
                # try with glade
                for xml in self.glade_xmlWidgets:
                    wid = xml.get_widget(key)
                    if wid is not None:
                        self.autoWidgets[key] = wid
                        break
                    pass

                # try with gtk.builder                
                if wid is None and self._builder is not None:
                    wid = self._builder.get_object(key)
                    if wid is not None:
                        self.autoWidgets[key] = wid
                        pass
                    pass                            
                pass
            pass
        
        return wid
    
    def __setitem__(self, key, wid):
        """
        Add a widget. This overrides widgets of the same name that were loaded
        fom XML. It does not affect GTK container/child relations.
        
        If no top widget is known, this sets it.
        """
        self.manualWidgets[key] = wid
        if (self.m_topWidget is None): self.m_topWidget = wid
        return

    def show(self):
        """
        Call `show()` on each top widget or `show_all()` if only one is known. 
        Otherwise does nothing.
        """
        top = self.get_top_widget()
        if type(top) in (types.ListType, types.TupleType):
            for t in top:
                if t is not None: t.show()
                pass
        elif (top is not None): top.show_all()
        return
        
        
    def hide(self):
        """
        Call `hide_all()` on all known top widgets.
        """
        top = self.get_top_widget()
        if type(top) in (types.ListType, types.TupleType):
            for t in top:
                if t is not None: t.hide_all()
                pass
        elif top is not None: top.hide_all()
        return

    def get_top_widget(self):
        """
        Return a widget or list of widgets.
        """
        return self.m_topWidget

    def set_parent_view(self, parent_view):
        """
        Set ``self.``:meth:`get_top_widget` transient for 
        ``parent_view.get_top_widget()``.
        """
        top = self.get_top_widget()
        if type(top) in (types.ListType, types.TupleType):
            for t in top:
                if t is not None and hasattr(t, "set_transient_for"):
                    t.set_transient_for(parent_view.get_top_widget())
                    pass
                pass
        elif (top is not None) and hasattr(top, "set_transient_for"):
            top.set_transient_for(parent_view.get_top_widget())
            pass
        
        return

    def set_transient(self, transient_view):
        """
        Set ``transient_view.get_top_widget()`` transient for
        ``self.``:meth:`get_top_widget`.
        """
        top = self.get_top_widget()
        if type(top) in (types.ListType, types.TupleType):
            for t in top:
                if t is not None:
                    transient_view.get_top_widget().set_transient_for(t)
                    pass
                pass
        elif (top is not None):
            transient_view.get_top_widget().set_transient_for(top)
            pass
        return

    # Finds the right callback for custom widget creation and calls it
    # Returns None if an undefined or invalid  handler is found
    def _custom_widget_create(self, glade, function_name, widget_name,
                              str1, str2, int1, int2):
        # This code was kindly provided by Allan Douglas <zalguod at
        # users.sourceforge.net>
        if function_name is not None:
            handler = getattr(self, function_name, None)
            if handler is not None: return handler(str1, str2, int1, int2)
            pass        
        return None

    def __iter__(self):
        """
        Return an iterator over widgets added with :meth:`__setitem__` and
        those loaded from XML.
        
        .. note::
           In case of name conflicts this yields widgets that are not 
           accessible via :meth:`__getitem__`.
        """
        # precalculates if needed
        self.__extract_autoWidgets()

        import itertools
        for i in itertools.chain(self.manualWidgets, self.autoWidgets): yield i
        return

    def __extract_autoWidgets(self):
        """Extract autoWidgets map if needed, out of the glade
        specifications and gtk builder"""
        if self.__autoWidgets_calculated: return

        if __glade_is_available__:
            for xml in self.glade_xmlWidgets:
                for wid in xml.get_widget_prefix(""):
                    wname = gtkglade.get_widget_name(wid)
                    if wname not in self.autoWidgets:
                        self.autoWidgets[wname] = wid
                        pass                    
                    pass
                pass
            pass

        if self._builder is not None:
            for wid in self._builder.get_objects():
                # General workaround for issue
                # https://bugzilla.gnome.org/show_bug.cgi?id=607492
                try: name = gtk.Buildable.get_name(wid)
                except TypeError: continue
                
                if name in self.autoWidgets and self.autoWidgets[name] != wid:
                    raise ViewError("Widget '%s' in builder also found in glade specification" % name)

                self.autoWidgets[name] = wid
                pass
            pass
        
        self.__autowidgets_calculated = True
        return
    
    pass # end of class View
