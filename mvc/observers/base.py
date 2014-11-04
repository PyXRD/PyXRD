# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
#  Copyright (C) 2006 by Roberto Cavada <roboogle@gmail.com>
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

from ..support import decorators

import inspect

class NTInfo (dict):
    """
    A container for information attached to a notification.
    This class is a dictionary-like object used:

    1. As class when defining notification methods in observers, as it
       contains the flags identifying the notification types.

    2. As class instance as parameter when a notification methods is
       called in observers.


    **Notification Type Flags**
    
    Notification methods are declared either statically or dynamically 
    through :meth:`Observer.observe`. In both cases the type of the
    notification is defined by setting to `True` some flags. Flags can
    be set in any combination for multi-type notification
    methods. Flags are:

    assign
       For notifications issued when OPs are assigned.
    before
       For notifications called before a modifying method is called.
    after
       For notifications called after a modifying method is called.
    signal
       For notifications called when a signal is emitted.

    
    **Instance content**

    Instances of class `NTInfo` will be received as the last argument
    (`info`) of any notification method::

      def notification_method(self, model, name, info)

    NTInfo is a dictionary (with some particular behaviour added)
    containing some information which is independent on the
    notification type, and some other information wich depends on the
    notification type.


    **Common to all types**

    For all notification types, NTInfo contains:

    model
       the model containing the observable property triggering the
       notification. `model` is also passed as first argument of the
       notification method.

    prop_name
       the name of the observable property triggering the notification. `name`
       is also passed as second argument of the notification method.
      
    Furthermore, any keyword argument not listed here is copied
    without modification into `info`.

    There are further information depending on the specific
    notification type:

    **For Assign-type**

    assign
       flag set to `True`

    old
       the value that the observable property had before being
       changed.

    new
       the new value that the observable property has been
       changed to.


    **For Before method call type**

    before
       flag set to `True`

    instance
       the object instance which the method that is being called belongs to.

    method_name
       the name of the method that is being called. 

    args
       tuple of the arguments of the method that is being called. 

    kwargs
       dictionary of the keyword arguments of the method that
       is being called.


    **For After method call type**

    after
       flag set to `True`

    instance
       the object instance which the method that has been 
       called belongs to.

    method_name
       the name of the method that has been called. 

    args
       tuple of the arguments of the method that has been called. 

    kwargs
       dictionary of the keyword arguments of the method that
       has been called.

    result
       the value returned by the method which has been called. 

    **For Signal-type**

    signal
       flag set to `True`

    arg
       the argument which was optionally specified when invoking
       emit() on the signal observable property.

    **Information access**

    The information carried by a NTInfo instance passed to a
    notification method can be retrieved using the instance as a
    dictionary, or accessing directly to the information as an
    attribute of the instance. For example::
       
       # This is a multi-type notification
       @Observer.observe("op1", assign=True, hello="Ciao")
       @Observer.observe("op2", after=True, before=True)
       def notify_me(self, model, name, info):
           assert info["model"] == model # access as dict key
           assert info.prop_name == name # access as attribute

           if "assign" in info:
              assert info.old == info["old"]
              assert "hello" in info and "ciao" == info.hello
              print "Assign from", info.old, "to", info.new
           else:
              assert "before" in info or "after" in info
              assert "hello" not in info
              print "Method name=", info.method_name
              if "after" in info: print "Method returned", info.result    
              pass
              
           return   

    As already told, the type carried by a NTInfo instance can be
    accessed through boolean flags `assign`, `before`, `after` and
    `signal`. Furthermore, any other information specified at
    declaration time (keyword argument 'hello' in the previous
    example) will be accessible in the corresponding notification
    method.

    .. versionadded:: 1.99.1

    """

    # At least one of the keys in this set is required when constructing
    __ONE_REQUESTED = frozenset("assign before after signal".split())
    __ALL_REQUESTED = frozenset("model prop_name".split())

    def __init__(self, _type, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

        # checks the content provided by the user
        if not (_type in self and self[_type]):
            raise KeyError("flag '%s' must be set in given arguments" % _type)

        # all requested are provided by the framework, not the user
        assert NTInfo.__ALL_REQUESTED <= set(self)

        # now removes all type-flags not related to _type
        for flag in NTInfo.__ONE_REQUESTED:
            if flag != _type and flag in self: del self[flag]
            pass

        return

    def __getattr__(self, name):
        """
        All dictionary keys are also available as attributes.
        """
        try:
            return self[name]
        except KeyError:
            raise AttributeError("NTInfo object has no attribute '%s'.\n"
                                 "Existing attributes are: %s" % (name, str(self)))
        pass

    pass # end of class NTInfo
# ----------------------------------------------------------------------


class Observer (object):
    """
    .. note::

       Most methods in this class are used internally by the
       framework.  Do not override them in subclasses.
    """

    # this is internal
    _CUST_OBS_ = "__custom_observes__"
    # ----------------------------------------------------------------------


    @classmethod
    @decorators.good_decorator_accepting_args
    def observe(cls, *args, **kwargs):
        """
        Mark a method as recieving notifications. Comes in two flavours:

        .. method:: observe(name, **types)
           :noindex:

           A decorator living in the class. Can be applied more than once to
           the same method, provided the names differ.
           
           *name* is the property we want to be notified about as a string.
           
           *types* are boolean values denoting the types of
           notifications desired. At least one of the following has to be
           passed as True: assign, before, after, signal.

           Excess keyword arguments are passed to the method as part of the
           info dictionary.

        .. method:: observe(callable, name, **types)
           :noindex:

           An instance method to define notifications at runtime. Works as
           above.
           
           *callable* is the method to send notifications to. The effect will
           be as if this had been decorated.

        In all cases the notification method must take exactly three
        arguments: the model object, the name of the property that changed,
        and an :class:`NTInfo` object describing the change.

        .. warning::
      
           Due to limitation in the dynamic registration (in version
           1.99.1), declarations of dynamic notifications must occur
           before registering self as an observer of the models whose
           properties the notifications are supposed to be
           observing. A hack for this limitation, is to first relieve
           any interesting model before dynamically register the
           notifications, and then re-observe those models.

        .. versionadded:: 1.99.1
        """

        @decorators.good_decorator
        def _decorator(_notified):
            # marks the method with observed properties
            _list = getattr(_notified, Observer._CUST_OBS_, list())
            _list.append((name, kwargs))
            setattr(_notified, Observer._CUST_OBS_, _list)
            return _notified

        # handles arguments
        if args and isinstance(args[0], cls):
            # used as instance method, for declaring notifications
            # dynamically
            if len(args) != 3:
                raise TypeError("observe() takes exactly three arguments"
                                " when called (%d given)" % len(args))

            self = args[0]
            notified = args[1]
            name = args[2]

            assert isinstance(self, Observer), "Method Observer.observe " \
                "must be called with an Observer instance as first argument"
            if not callable(notified):
                raise TypeError("Second argument of observe() must be a callable")
            if type(name) != str:
                raise TypeError("Third argument of observe() must be a string")

            self.__register_notification(name, notified, kwargs)
            return None

        # used statically as decorator
        if len(args) != 1:
            raise TypeError("observe() takes exactly one argument when used"
                            " as decorator (%d given)" % len(args))
        name = args[0]
        if type(name) != str:
            raise TypeError("First argument of observe() must be a string")
        return _decorator
    # ----------------------------------------------------------------------


    def __init__(self, *args, **kwargs):
        """
        *model* is passed to :meth:`observe_model` if given.
        
        *spurious* indicates interest to be notified even when
        the value hasn't changed, like for: ::

         model.prop = model.prop

        .. versionadded:: 1.2.0
           Before that observers had to filter out spurious
           notifications themselves, as if the default was `True`. With
           :class:`~mvc.observable.Signal` support this is no longer
           necessary.
        """
        model = kwargs.pop("model", None)
        spurious = kwargs.pop("spurious", False)
        super(Observer, self).__init__(*args, **kwargs)

        # --------------------------------------------------------- #
        # This turns the decorator 'observe' an instance method
        def __observe(*args, **kwargs): self.__original_observe(self, *args, **kwargs)
        __observe.__name__ = self.observe.__name__
        __observe.__doc__ = self.observe.__doc__
        self.__original_observe = self.observe
        self.observe = __observe
        # --------------------------------------------------------- #

        self.__accepts_spurious__ = spurious

        # NOTE: In rev. 202 these maps were unified into
        #   __CUST_OBS_MAP only (the map contained pairs (method,
        #   args). However, this broke backward compatibility of code
        #   accessing the map through
        #   get_observing_methods. Now the informatio is split
        #   and the original information restored. To access the
        #   additional information (number of additional arguments
        #   required by observing methods) use the newly added methods.

        # Private maps: do not change/access them directly, use
        # methods to access them:
        self.__CUST_OBS_MAP = {} # prop name --> set of observing methods
        self.__CUST_OBS_KWARGS = {} # observing method --> flag

        processed_props = set() # tracks already processed properties

        # searches all custom observer methods
        for cls in inspect.getmro(type(self)):
            # list of (method-name, method-object, list of (prop-name, kwargs))
            meths = [ (name, meth, getattr(meth, Observer._CUST_OBS_))
                      for name, meth in cls.__dict__.iteritems()
                      if (inspect.isfunction(meth) and
                          hasattr(meth, Observer._CUST_OBS_)) ]

            # props processed in this class. This is used to avoid
            # processing the same props in base classes.
            cls_processed_props = set()

            # since this is traversed top-bottom in the mro, the
            # first found match is the one to care
            for name, meth, pnames_ka in meths:
                _method = getattr(self, name) # the most top avail method

                # WARNING! Here we store the top-level method in the
                # mro, not the (unbound) method which has been
                # declared by the user with the decorator.
                for pname, ka in pnames_ka:
                    if pname not in processed_props:
                        self.__register_notification(pname, _method, ka)
                        cls_processed_props.add(pname)
                        pass
                    pass
                pass

            # accumulates props processed in this class
            processed_props |= cls_processed_props
            pass # end of loop over classes in the mro

        if model is not None:
            self.observe_model(model)
        return

    def observe_model(self, model):
        """Starts observing the given model"""
        return model.register_observer(self)

    def relieve_model(self, model):
        """Stops observing the given model"""
        return model.unregister_observer(self)

    def accepts_spurious_change(self):
        """
        Returns True if this observer is interested in receiving
        spurious value changes. This is queried by the model when
        notifying a value change."""
        return self.__accepts_spurious__

    def get_observing_methods(self, prop_name):
        """
        Return a possibly empty set of callables registered with
        :meth:`observe` for *prop_name*.
        
        .. versionadded:: 1.99.1
           Replaces :meth:`get_custom_observing_methods`.
        """
        return self.__CUST_OBS_MAP.get(prop_name, set())

    # this is done to keep backward compatibility
    get_custom_observing_methods = get_observing_methods


    def get_observing_method_kwargs(self, prop_name, method):
        """
        Returns the keyword arguments which were specified when
        declaring a notification method, either statically of
        synamically with :meth:`Observer.observe`.

        *method* a callable that was registered with
        :meth:`observes`.
        
        :rtype: dict
        """
        return self.__CUST_OBS_KWARGS[(prop_name, method)]


    def remove_observing_method(self, prop_names, method):
        """
        Remove dynamic notifications.
        
        *method* a callable that was registered with :meth:`observe`.
        
        *prop_names* a sequence of strings. This need not correspond to any
        one `add` call.

        .. note::

           This can revert the effects of a decorator at runtime. Don't.
        """
        for prop_name in prop_names:
            _set = self.__CUST_OBS_MAP.get(prop_name, set())
            if method in _set: _set.remove(method)
            key = (prop_name, method)
            if key in self.__CUST_OBS_KWARGS: del self.__CUST_OBS_KWARGS[key]
            pass

        return

    def is_observing_method(self, prop_name, method):
        """
        Returns `True` if the given method was previously added as an
        observing method, either dynamically or via decorator.
        """
        return (prop_name, method) in self.__CUST_OBS_KWARGS


    def __register_notification(self, prop_name, method, kwargs):
        """Internal service which associates the given property name
        to the method, and the (prop_name, method) with the given
        kwargs dictionary. If needed merges the dictionary, if the
        given (prop_name, method) pair was already registered (in this
        case the last registration wins in case of overlapping.)

        If given prop_name and method have been already registered, a
        ValueError exception is raised."""

        key = (prop_name, method)
        if key in self.__CUST_OBS_KWARGS:
            raise ValueError("In %s method '%s' has been declared "
                             "to be a notification for property '%s' "
                             "multiple times (only one is allowed)." % \
                                 (self.__class__,
                                  method.__name__, prop_name))

        # fills the internal structures
        if not self.__CUST_OBS_MAP.has_key(prop_name):
            self.__CUST_OBS_MAP[prop_name] = set()
            pass
        self.__CUST_OBS_MAP[prop_name].add(method)

        self.__CUST_OBS_KWARGS[key] = kwargs
        return

    pass # end of class
# ----------------------------------------------------------------------
