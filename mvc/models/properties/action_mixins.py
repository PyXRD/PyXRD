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

from mvc.support.utils import rec_getattr

class SetActionMixin(object):
    """
    A descriptor mixin that will invoke a method on the instance
    owning this property after setting it.
    
    Expects two more keyword arguments to be passed to the property constructor:
        - set_action_name: a dotted string describing where to get the method
          from the instance
        - set_action_before: flag indicating whether this action should be 
          invoked before setting the property (default False) 
    """

    set_action_name = None
    set_action_before = False

    def __set__(self, instance, value):
        action = rec_getattr(instance, self.set_action_name, None)
        assert callable(action), "The action in a SetActionMixin (%s) should be callable!" % self.label
        if self.set_action_before: action()
        super(SetActionMixin, self).__set__(instance, value)
        if not self.set_action_before: action()


    pass # end of class

class GetActionMixin(object):
    """
    A descriptor mixin that will invoke a method on the instance
    owning this property before getting it.
    
    Expects two more keyword arguments to be passed to the property constructor:
        - get_action_name: a dotted string describing where to get the method
          from the instance
        - get_action_after: flag indicating whether this action should be 
          invoked after setting the property (default False) 
    """

    get_action_name = None
    get_action_after = False

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        action = rec_getattr(instance, self.get_action_name, None)
        assert callable(action), "The action in a GetActionMixin (%s) should be callable!" % self.label
        if self.get_action_after: action()
        value = super(GetActionMixin, self).__get__(instance, owner=owner)
        if not self.get_action_after: action()
        return value

    pass # end of class

