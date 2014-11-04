# coding=UTF-8
# ex:ts=4:sw=4:et=on
#  -------------------------------------------------------------------------
#  Copyright (C) 2014 by Mathijs Dumon <mathijs dot dumon at gmail dot com>
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

import importlib
import logging
logger = logging.getLogger(__name__)

from ..settings import TOOLKIT
from ..support.idle_call import IdleCallHandler

class ToolkitRegistry(dict):
    """
        Dict subclass used to store all AdapterRegistry's.
        Keys are toolkit names, values are AdapterRegistry instances
    """
    
    # These will be loaded automatically when this module is first loaded:
    toolkit_modules = [
        ".gtk_support"
    ]
    selected_toolkit = None

    def get_or_create_registry(self, toolkit_name):
        if not toolkit_name in self:
            adapter_registry = AdapterRegistry()
            self.register(toolkit_name, adapter_registry)
        return self[toolkit_name]

    def register(self, toolkit_name, adapter_registry):
        self[toolkit_name] = adapter_registry

    def select_toolkit(self, toolkit_name):
        if not toolkit_name in self:
            raise ValueError, "Cannot select unknown toolkit '%s'" % toolkit_name
        else:
            self.selected_toolkit = toolkit_name
            tkar = self.get_selected_adapter_registry()
            IdleCallHandler.set_idle_handler(self, tkar.idle_handler)

    def get_selected_adapter_registry(self):
        if self.selected_toolkit is None:
            raise ValueError, "No toolkit has been selected!"
        else:
            return self[self.selected_toolkit]

class AdapterRegistry(dict):
    """
        A dict which maps Adapter class types to the widget types they
        can handle. This relies on these classes being registered using
        the 'register' decorator also provided by this class.
    """

    toolkit_registry = ToolkitRegistry()
    idle_handler = None

    @classmethod
    def get_selected_adapter_registry(cls):
        return cls.toolkit_registry.get_selected_adapter_registry()

    @classmethod
    def get_adapter_for_widget_type(cls, widget_type):
        return cls.toolkit_registry.get_selected_adapter_registry()[widget_type]

    @classmethod
    def register_decorator(cls):
        """
            Returns a decorator that will register Adapter classes.
        """
        return cls.register

    @classmethod
    def register(cls, adapter_cls):
        if hasattr(adapter_cls, "widget_types") and hasattr(adapter_cls, "toolkit"):
            adapter_registry = cls.toolkit_registry.get_or_create_registry(adapter_cls.toolkit)
            logger.debug("Registering %s as handler for widget types '%s' in toolkit '%s'" % (adapter_cls, adapter_cls.widget_types, adapter_cls.toolkit))
            for widget_type in adapter_cls.widget_types:
                adapter_registry[widget_type] = adapter_cls
        else:
            logger.debug("Ignoring '%s' as handler: no 'toolkit' or 'widget_types' defined" % adapter_cls)
        return adapter_cls

    pass # end of class

for toolkit_module in ToolkitRegistry.toolkit_modules:
    if toolkit_module.startswith('.'):
        package = __name__.rpartition('.')[0]
        try:
            # Import and load toolkit module:
            tk_mod = importlib.import_module(toolkit_module, package=package)
            tk_mod.load(AdapterRegistry.toolkit_registry)
        except ImportError:
            logger.warning("Could not load toolkit support module '%s'" % (toolkit_module,))

AdapterRegistry.toolkit_registry.select_toolkit(TOOLKIT)
