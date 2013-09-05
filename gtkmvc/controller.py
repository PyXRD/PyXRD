#  Author: Roberto Cavada <roboogle@gmail.com>
#
#  Copyright (c) 2005 by Roberto Cavada
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

import gtk

from gtkmvc.observer import Observer
from gtkmvc.support.log import logger
from gtkmvc.support.exceptions import TooManyCandidatesError

import types
import gobject

class Controller (Observer):

    ___user_props = None
    _controller_scope_aplied = False
    @property
    def __user_props(self):
        assert(not (self.auto_adapt_included != None and self.auto_adapt_excluded != None))
        if not self._controller_scope_aplied:
            props = self.model.get_properties()
            if self.auto_adapt_included != None:
                self.___user_props = self.___user_props.union(set(filter(lambda p: p not in self.auto_adapt_included, props)))
            elif self.auto_adapt_excluded != None:
                self.___user_props = self.___user_props.union(set(filter(lambda p: p in self.auto_adapt_excluded, props)))
            self._controller_scope_aplied = True
        return self.___user_props

    @__user_props.setter
    def __user_props(self, value):
        return # ignore
        self.___user_props = set(value)

    def __init__(self, model, view, spurious=False, auto_adapt=False):
        """
        Two positional and two optional keyword arguments.
        
        *model* will have the new instance registered as an observer.
        It is made available as an attribute.
        
        *view* may contain signal connections loaded from XML. The handler
        methods have to exist in this class.
        
        *spurious* denotes whether notifications in this class will be called
        if a property of *model* is set to the same value it already has.
        
        *auto_adapt* denotes whether to call :meth:`adapt` with no arguments
        as part of the view registration process.

        View registration consists of connecting signal handlers,
        :meth:`register_view` and :meth:`register_adapters`, and is scheduled
        with the GTK main loop. It happens as soon as possible but after the
        constructor returns. When it starts *view* is available as an
        attribute.
        """
        # In 1.99.0 the third parameter was optional. Now the interpreter will
        # raise if it isn't given.
        if view in (True, False):
            raise NotImplementedError("This version of GTKMVC does not"
                " support the 1.2 API")

        Observer.__init__(self, model, spurious)

        self.model = model
        self.view = None
        self.__adapters = []
        # set of properties explicitly adapted by the user:
        self.___user_props = set()
        self.__auto_adapt = auto_adapt

        gobject.idle_add(self._idle_register_view, view, priority=gobject.PRIORITY_HIGH)
        return

    def _idle_register_view(self, view):
        """Internal method that calls register_view"""
        assert(self.view is None)
        self.view = view

        self.__autoconnect_signals()

        self.register_view(view)
        self.register_adapters()
        if self.__auto_adapt: self.adapt()
        return False

    def register_view(self, view):
        """
        This does nothing. Subclasses can override it to connect signals
        manually or modify widgets loaded from XML, like adding columns to a
        TreeView. No super call necessary.
        
        *view* is a shortcut for ``self.view``.
        """
        assert(self.model is not None)
        assert(self.view is not None)
        return

    def register_adapters(self):
        """
        This does nothing. Subclasses can override it to create adapters.
        No super call necessary.
        """
        assert(self.model is not None)
        assert(self.view is not None)
        return

    def adapt(self, *args):
        """
        There are four ways to call this:

        .. method:: adapt()
           :noindex:

           Take properties from the model for which ``adapt`` has not yet been
           called, match them to the view by name, and create adapters fitting
           for the respective widget type.
           
           That information comes from :mod:`gtkmvc.adapters.default`.
           See :meth:`_find_widget_match` for name patterns.

           .. versionchanged:: 1.99.1
              Allow incomplete auto-adaption, meaning properties for which no
              widget is found.

        .. method:: adapt(ad)
           :noindex:
        
           Keep track of manually created adapters for future ``adapt()``
           calls.
        
           *ad* is an adapter instance already connected to a widget.

        .. method:: adapt(prop_name)
           :noindex:

           Like ``adapt()`` for a single property.

           *prop_name* is a string.

        .. method:: adapt(prop_name, wid_name)
           :noindex:

           Like ``adapt(prop_name)`` but without widget name matching.
           
           *wid_name* has to exist in the view.
        """

        # checks arguments
        n = len(args)
        if n not in range(3): raise TypeError("adapt() takes 0, 1 or 2 arguments (%d given)" % n)

        if n == 0:
            adapters = []
            props = self.model.get_properties()
            # matches all properties not previoulsy adapter by the user:
            for prop_name in filter(lambda p: p not in self.__user_props, props):
                try: wid_name = self._find_widget_match(prop_name)
                except TooManyCandidatesError, e:
                    # multiple candidates, gives up
                    raise e
                except ValueError, e:
                    # no widgets found for given property, continue after emitting a warning
                    if e.args:
                        logger.warn(e[0])
                    else:
                        logger.warn("No widget candidates match property '%s'"
                            % prop_name)
                else:
                    logger.debug("Auto-adapting property %s and widget %s" % \
                                     (prop_name, wid_name))
                    adapters += self.__create_adapters__(prop_name, wid_name)
                    pass
                pass

        elif n == 1: # one argument
            from gtkmvc.adapters.basic import Adapter

            if isinstance(args[0], Adapter): adapters = (args[0],)

            elif isinstance(args[0], types.StringType):
                prop_name = args[0]
                wid_name = self._find_widget_match(prop_name)
                adapters = self.__create_adapters__(prop_name, wid_name)
                pass
            else: raise TypeError("Argument of adapt() must be either an Adapter or a string")

        else: # two arguments
            if not (isinstance(args[0], types.StringType) and isinstance(args[1], types.StringType)):
                raise TypeError("Arguments of adapt() must be two strings")

            # retrieves both property and widget, and creates an adapter
            prop_name, wid_name = args
            adapters = self.__create_adapters__(prop_name, wid_name)
            pass

        for ad in adapters:
            self.__adapters.append(ad)
            # remember properties added by the user
            if n > 0: self.__user_props.add(ad.get_property_name())
            pass

        return

    def _find_widget_match(self, prop_name):
        """
        Used to search ``self.view`` when :meth:`adapt` is not given a widget 
        name.
        
        *prop_name* is the name of a property in the model.
        
        Returns a string with the best match. Raises
        :class:`TooManyCandidatesError` or ``ValueError`` when nothing is
        found.

        Subclasses can customise this. No super call necessary. The default
        implementation converts *prop_name* to lower case and allows prefixes
        like ``entry_``.
        """
        names = []
        for wid_name in self.view:
            # if widget names ends with given property name: we skip
            # any prefix in widget name
            if wid_name.lower().endswith(prop_name.lower()): names.append(wid_name)
            pass

        if len(names) == 0:
            raise ValueError("No widget candidates match property '%s': %s" % \
                                 (prop_name, names))

        if len(names) > 1:
            raise TooManyCandidatesError("%d widget candidates match property '%s': %s" % \
                                             (len(names), prop_name, names))

        return names[0]


    # performs Controller's signals auto-connection:
    def __autoconnect_signals(self):
        """This is called during view registration, to autoconnect
        signals in glade file with methods within the controller"""
        dic = {}
        for name in dir(self):
            method = getattr(self, name)
            if (not callable(method)): continue
            assert(not dic.has_key(name)) # not already connected!
            dic[name] = method
            pass

        # autoconnects glade in the view (if available any)
        for xml in self.view.glade_xmlWidgets: xml.signal_autoconnect(dic)

        # autoconnects builder if available
        if self.view._builder is not None:
            self.view._builder.connect_signals(dic)
            pass

        return


    def __create_adapters__(self, prop_name, wid_name):
        """
        Private service that looks at property and widgets types,
        and possibly creates one or more (best) fitting adapters
        that are returned as a list.
        """
        from gtkmvc.adapters.basic import Adapter, RoUserClassAdapter
        from gtkmvc.adapters.containers import StaticContainerAdapter

        res = []

        wid = self.view[wid_name]
        if wid is None: raise ValueError("Widget '%s' not found" % wid_name)

        # Decides the type of adapters to be created.
        if isinstance(wid, gtk.Calendar):
            # calendar creates three adapter for year, month and day
            ad = RoUserClassAdapter(self.model, prop_name,
                                    lambda d: d.year,
                                    lambda d, y: d.replace(year=y),
                                    spurious=self.accepts_spurious_change())
            ad.connect_widget(wid, lambda c: c.get_date()[0],
                              lambda c, y: c.select_month(c.get_date()[1], y),
                              "day-selected")
            res.append(ad) # year

            ad = RoUserClassAdapter(self.model, prop_name,
                                    lambda d: d.month,
                                    lambda d, m: d.replace(month=m),
                                    spurious=self.accepts_spurious_change())
            ad.connect_widget(wid, lambda c: c.get_date()[1] + 1,
                              lambda c, m: c.select_month(m - 1, c.get_date()[0]),
                              "day-selected")
            res.append(ad) # month

            ad = RoUserClassAdapter(self.model, prop_name,
                                    lambda d: d.day,
                                    lambda d, v: d.replace(day=v),
                                    spurious=self.accepts_spurious_change())
            ad.connect_widget(wid, lambda c: c.get_date()[2],
                              lambda c, d: c.select_day(d),
                              "day-selected")
            res.append(ad) # day
            return res


        try: # tries with StaticContainerAdapter
            ad = StaticContainerAdapter(self.model, prop_name,
                                        spurious=self.accepts_spurious_change())
            ad.connect_widget(wid)
            res.append(ad)

        except TypeError:
            # falls back to a simple adapter
            ad = Adapter(self.model, prop_name,
                         spurious=self.accepts_spurious_change())
            ad.connect_widget(wid)
            res.append(ad)
            pass

        return res


    pass # end of class Controller
