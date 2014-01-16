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

import logging
logger = logging.getLogger(__name__)

# TODO move this elsewhere or make it dynamic
ALLOWED_TOOLKIT = 'gtk'

class AdapterRegistry(dict):
    """
        A dict which maps Adapter class types to the widget types they
        can handle. This relies on these classes being registered using
        the 'register' decorator also provided by this class.
    """
    def register_decorator(self):
        """
            Returns a decorator that will register Adapter classes.
        """
        return self.register

    def register(self, cls):
        if hasattr(cls, "widget_types") and hasattr(cls, "toolkit"):
            if cls.toolkit == ALLOWED_TOOLKIT: # FIXME
                logger.debug("Registering %s as handler for widget types '%s'" % (cls, cls.widget_types))
                for widget_type in cls.widget_types:
                    self[widget_type] = cls
        else:
            logger.debug("Ignoring %s as handler" % cls)
        return cls

    pass # end of class

adapter_registry = AdapterRegistry()
