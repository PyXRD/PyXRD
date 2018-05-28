# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#  Copyright (C) 2005 by Roberto Cavada <roboogle@gmail.com>
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

import logging
from mvc.support.gui_loop import add_idle_call
logger = logging.getLogger(__name__)

from .observers import Observer
from .support.exceptions import TooManyCandidatesError

class Controller(Observer):

    auto_adapt = True
    auto_adapt_included = None
    auto_adapt_excluded = None

    register_lazy = True

    __adapters = None
    __parsed_user_props = None
    _controller_scope_aplied = False

    @property
    def __user_props(self):
        assert not (self.auto_adapt_included is not None and self.auto_adapt_excluded is not None), \
            "Controller '%s' has set both auto_adapt_included and auto_adapt_excluded!" % self
        assert self.model is not None, \
            "Controller '%s' has None as model! Did you forget to pass it as a keyword argument?" % self
        if not self._controller_scope_aplied:
            props = [prop.label for prop in self.model.Meta.all_properties]
            if self.auto_adapt_included is not None:
                self.__parsed_user_props = self.__parsed_user_props.union(set([p for p in props if p not in self.auto_adapt_included]))
            elif self.auto_adapt_excluded is not None:
                self.__parsed_user_props = self.__parsed_user_props.union(set([p for p in props if p in self.auto_adapt_excluded]))
            self._controller_scope_aplied = True
        return self.__parsed_user_props

    @__user_props.setter
    def __user_props(self, value):
        return # ignore
        self.__parsed_user_props = set(value)


    _model = None
    def _get_model(self):
        return self._model
    def _set_model(self, model):
        if self._model is not None:
            self._clear_adapters()
            self.relieve_model(self._model)
        self._model = model
        if self._model is not None:
            self.observe_model(self._model)
            if self.view is not None:
                self.register_adapters()
                if self.auto_adapt: self.adapt()
    def _del_model(self):
        del self._model
        self._model = None
    model = property(_get_model, _set_model, _del_model)

    __view = None
    def _get_view(self):
        return self.__view
    def _set_view(self, view):
        if self.__view != view:
            self.__view = view
            if self.__view is not None:
                if self.register_lazy:
                    add_idle_call(self._idle_register_view, self.__view)
                else:
                    self._idle_register_view(self.__view)
    def _del_view(self):
        self.__view = None
    view = property(_get_view, _set_view, _del_view, "This controller's view")

    def __init__(self, *args, **kwargs):
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
        
        Subclasses can also override either the `auto_adapt_included` or
        `auto_adapt_excluded` class attributes. These should be either None or
        contain a list of properties to exclude (or include) from auto
        adaptation for this controller. If not specified, all properties are
        adapted if auto_adapt is True.
        """

        # set of properties explicitly adapted by the user:
        self.__adapters = []
        self.__parsed_user_props = set()

        # Some general keyword arguments:
        self.parent = kwargs.pop("parent", None)
        self.auto_adapt = kwargs.pop("auto_adapt", self.auto_adapt)
        self.register_lazy = kwargs.pop("register_lazy", self.register_lazy)

        # Pop the view, keep the model as we pass it down to the observer
        _view = kwargs.pop("view", None)
        _model = kwargs.get("model", None)

        # Init base classes
        super(Controller, self).__init__(*args, **kwargs)

        # Set model (will register controller as observer)
        self.model = _model
        # Set view (will register & adapt to view)
        self.view = _view

        return

    def _idle_register_view(self, view):
        """Internal method that calls register_view"""
        assert(self.view is not None)
        if self.model is not None:
            self.__autoconnect_signals()

            self.register_view(self.view)
            self.register_adapters()
            if self.auto_adapt: self.adapt()
            return False
        else:
            return True

    def _clear_adapters(self):
        """Clears & disconnects all adapters from this controller"""
        if self.__adapters:
            for ad in self.__adapters:
                ad.disconnect()
            self.__adapters[:] = []

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
           
           That information comes from :mod:`mvc.adapters.default`.
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
        if n not in list(range(3)): raise TypeError("adapt() takes 0, 1 or 2 arguments (%d given)" % n)

        if n == 0:
            adapters = []
            props = self.model.Meta.get_viewable_properties()
            # matches all properties not previously adapted by the user:
            for prop in [p for p in props if p.label not in self.__user_props]:
                try: wid_name = self._find_widget_match(prop)
                except TooManyCandidatesError as e:
                    # multiple candidates, gives up
                    raise e
                except ValueError as e:
                    # no widgets found for given property, continue after emitting a warning
                    if e.args:
                        logger.warn(e[0])
                    else:
                        logger.warn("No widget candidates match property '%s'"
                            % prop.label)
                else:
                    logger.debug("Auto-adapting property %s and widget %s" % \
                                     (prop.label, wid_name))
                    adapters += self.__create_adapters__(prop, wid_name)
                    pass
                pass

        elif n == 1: # one argument
            from .adapters import AbstractAdapter

            if isinstance(args[0], AbstractAdapter): adapters = (args[0],)

            elif isinstance(args[0], str):
                prop = getattr(type(self.model), args[0])
                wid_name = self._find_widget_match(prop)
                adapters = self.__create_adapters__(prop, wid_name)
                pass
            else: raise TypeError("Argument of adapt() must be either an Adapter or a string")

        else: # two arguments
            if not (isinstance(args[0], str) and isinstance(args[1], str)):
                raise TypeError("Arguments of adapt() must be two strings")

            # retrieves both property and widget, and creates an adapter
            prop_name, wid_name = args #@UnusedVariable
            adapters = self.__create_adapters__(prop, wid_name)
            pass

        for ad in adapters:
            self.__adapters.append(ad)
            # remember properties added by the user
            if n > 0: self.__user_props.add(ad.get_property_name())
            pass

        return

    def _find_widget_match(self, prop):
        """
        Checks if the view has defined a 'widget_format' attribute (e.g. 
        "view_%s") If so, it uses this format to search for the widget in 
        the view, if not it takes the *first* widget with a name ending with the
        property name.
        """

        widget_name = None
        widget_format = getattr(self.view, 'widget_format', "%s")

        if widget_format:
            widget_name = widget_format % prop.label
            widget = self.view[widget_name]
            if widget is None: # not in view
                if prop is not None and prop.widget_type == 'scale':
                    self.view.add_scale_widget(prop)
                else:
                    widget_name = None

        else:
            for wid_name in self.view:
                if wid_name.lower().endswith(prop.label.lower()):
                    widget_name = wid_name
                    break

        if widget_name == None:
            logger.setLevel(logging.INFO)
            raise ValueError("No widget candidates match property '%s'" % prop.label)

        return widget_name

    # performs Controller's signals auto-connection:
    def __autoconnect_signals(self):
        """This is called during view registration, to autoconnect
        signals in glade file with methods within the controller"""
        dic = {}
        for name in dir(self):
            method = getattr(self, name)
            if (not callable(method)): continue
            assert(name not in dic) # not already connected!
            dic[name] = method
            pass

        # Auto connect builder if available:
        if self.view._builder is not None:
            self.view._builder.connect_signals(dic)
            pass

        return

    def _get_handler_list(self):
        from .adapters import AdapterRegistry

        # Add default widget handlers:
        local_handlers = {}
        adapter_registry = AdapterRegistry.get_selected_adapter_registry()
        local_handlers.update(adapter_registry)

        # Override with class instance widget handlers:
        for widget_type, handler in self.widget_handlers.items():
            if isinstance(handler, str):
                self.widget_handlers[widget_type] = getattr(self, handler)
        local_handlers.update(self.widget_handlers)

        return local_handlers

    def __create_adapters__(self, prop, wid_name):
        """
            Private service that looks at property and widgets types,
            and possibly creates one or more (best) fitting adapters
            that are returned as a list.
        """
        try:
            logger.debug("Adapting property %s to widget names '%s'" % (prop.label, wid_name))
            if prop.visible:

                wid = self.view[wid_name]
                if wid == None:
                    raise ValueError("Widget '%s' not found in view '%s' by controller '%s'" % (wid_name, self.view, self))

                local_handlers = self._get_handler_list()

                handler = local_handlers.get(prop.widget_type)
                ad = handler(self, prop, wid)

                return [ad]
            else:
                return []
        except BaseException as error:
            raise RuntimeError("Unhandled error in '%s'.__create_adapters__ for property '%s' and widget '%s'!" % (type(self), prop.label, wid_name)) from error

    pass # end of class Controller
