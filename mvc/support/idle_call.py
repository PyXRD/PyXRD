# coding=UTF-8
# ex:ts=4:sw=4:et:
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

__handler = None

class IdleCallHandler(object):
    """
        This is a simple work-around to make mvc more GUI toolkit agnostic.
        If the GUI toolkit has been chosen, `set_idle_handler` can be called
        passing a method that will idly handle these calls. Mainly used for
        events and notifications. 
    """
        
    @classmethod
    def call_idle(cls, method, *args):
        global __handler
        if __handler is None:
            method(*args)
            return None
        else:
            return __handler(method, *args)
        
    @classmethod
    def set_idle_handler(cls, self, handler):
        global __handler
        __handler = handler
    
    pass #end of class

def run_when_idle(func):
    """
        Decorator that can be used to run the decorated method idly on the GUI 
        main event loop.
    """
    def callback(*args):
        IdleCallHandler.call_idle(func, *args)
    return callback
    