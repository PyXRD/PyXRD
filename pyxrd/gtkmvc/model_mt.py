#  Author: Roberto Cavada <roboogle@gmail.com>
#
#  Copyright (c) 2006 by Roberto Cavada
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


from pyxrd.gtkmvc.model import Model
from pyxrd.gtkmvc.support import metaclasses

try: import threading as _threading
except ImportError: import dummy_threading as _threading

try:
    import gobject
    import gtk
except ImportError:
    GOBJECT_AVAILABLE = False
    GTK_AVAILABLE = False
else:
    GOBJECT_AVAILABLE = True
    GTK_AVAILABLE = True
    if hasattr(gobject, "threads_init"): gobject.threads_init()
    else: gtk.threads_init()


class ModelMT (Model):
    """A base class for models whose observable properties can be
    changed by threads different than gtk main thread. Notification is
    performed by exploiting the gtk idle loop only if needed,
    otherwise the standard notification system (direct method call) is
    used. In this model, the observer is expected to run in the gtk
    main loop thread."""

    __metaclass__ = metaclasses.ObservablePropertyMetaMT

    __hold_back_notifications__ = False
    __stored_notifications__ = []

    @staticmethod
    def release_stored_notifications():

        for self, observer, method, args, kwargs in ModelMT.__stored_notifications__:
            Model.__notify_observer__(self, observer, method,
                                             *args, **kwargs)
        ModelMT.__stored_notifications__ = [] # clear variable

    @staticmethod
    def hold_back_notifications():
        """
            If a massive number of notification is triggered by a single piece of code,
            wrap it in hold_back_notifications() and unhold_back_notifications()
            calls to hold them back until all properties have been set.
            The last call will release the stored calls by calling
            release_stored_notifications.
        """
        ModelMT.__hold_back_notifications__ = True

    @staticmethod
    def unhold_back_notifications():
        ModelMT.release_stored_notifications()
        ModelMT.__hold_back_notifications__ = False

    def __init__(self):
        Model.__init__(self)
        self.__observer_threads = {}
        self._prop_lock = _threading.RLock() # @UndefinedVariable
        return

    def register_observer(self, observer):
        Model.register_observer(self, observer)
        self.__observer_threads[observer] = _threading.currentThread() # @UndefinedVariable
        return

    def unregister_observer(self, observer):
        Model.unregister_observer(self, observer)
        del self.__observer_threads[observer]
        return

    # ---------- Notifiers:

    def __notify_observer__(self, observer, method, *args, **kwargs):
        """This makes a call either through the gtk.idle list or a
        direct method call depending whether the caller's thread is
        different from the observer's thread"""

        assert self.__observer_threads.has_key(observer)
        global GOBJECT_AVAILABLE
        # FIXME: we need some way to call these on the main thread without relying on gobject...
        if not GOBJECT_AVAILABLE or _threading.currentThread() == self.__observer_threads[observer]: # @UndefinedVariable
            # standard call

            if self.__hold_back_notifications__:
                self.__stored_notifications__.append((
                    self, observer, method, args, kwargs))
                return
            else:
                return Model.__notify_observer__(
                    self, observer, method, *args, **kwargs)

        # multi-threading call
        gobject.idle_add(self.__idle_callback, observer, method, args, kwargs)
        return

    def __idle_callback(self, observer, method, args, kwargs):
        method(*args, **kwargs)
        return False


    pass # end of class

if GTK_AVAILABLE:
    # ----------------------------------------------------------------------
    class TreeStoreModelMT (ModelMT, gtk.TreeStore):
        """Use this class as base class for your model derived by
        gtk.TreeStore"""
        __metaclass__ = metaclasses.ObservablePropertyGObjectMetaMT

        def __init__(self, column_type, *args):
            ModelMT.__init__(self)
            gtk.TreeStore.__init__(self, column_type, *args)
            return
        pass


    # ----------------------------------------------------------------------
    class ListStoreModelMT (ModelMT, gtk.ListStore):
        """Use this class as base class for your model derived by
        gtk.ListStore"""
        __metaclass__ = metaclasses.ObservablePropertyGObjectMetaMT

        def __init__(self, column_type, *args):
            ModelMT.__init__(self)
            gtk.ListStore.__init__(self, column_type, *args)
            return
        pass


    # ----------------------------------------------------------------------
    class TextBufferModelMT (ModelMT, gtk.TextBuffer):
        """Use this class as base class for your model derived by
        gtk.TextBuffer"""
        __metaclass__ = metaclasses.ObservablePropertyGObjectMetaMT

        def __init__(self, table=None):
            ModelMT.__init__(self)
            gtk.TextBuffer.__init__(self, table)
            return
        pass
