#  -------------------------------------------------------------------------
#  Author: Roberto Cavada <roboogle@gmail.com>
#
#  Copyright (C) 2008 by Roberto Cavada
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
#  -------------------------------------------------------------------------

import new
from gtkmvc import Model
from noconflict import get_noconflict_metaclass

class ModelFactory (object):
    """This factory constructs classes for models. Use it to build
    the classes to derive your own models"""
    
    __memoized = {}

    @staticmethod
    def __fix_bases(base_classes, have_mt):
        """This function check whether base_classes contains a Model
        instance. If not, choose the best fitting class for
        model. Furthermore, it makes the list in a cannonical
        ordering form in a way that ic can be used as memoization
        key"""
        fixed = list(base_classes)
        contains_model = False
        for b in fixed:
            if isinstance(fixed, Model): contains_model = True; break
            pass

        # adds a model when user is lazy
        if not contains_model:
            if have_mt:
                from gtkmvc.model_mt import ModelMT
                fixed.insert(0, ModelMT)
            else: fixed.insert(0, Model)
            pass

        class ModelFactoryWrap (object):
            __metaclass__ = get_noconflict_metaclass(tuple(fixed), (), ())
            def __init__(self, *args, **kwargs): pass
            pass
        
        fixed.append(ModelFactoryWrap)
        fixed.sort()
        return tuple(fixed)

    @staticmethod
    def make(base_classes=(), have_mt=False):
        """Use this static method to build a model class that
        possibly derives from other classes. If have_mt is True,
        then returned class will take into account multi-threading
        issues when dealing with observable properties."""
        
        good_bc = ModelFactory.__fix_bases(base_classes, have_mt)
        print "Base classes are:", good_bc
        key = "".join(map(str, good_bc))
        if ModelFactory.__memoized.has_key(key):
            return ModelFactory.__memoized[key]

        cls = new.classobj('', good_bc, {'__module__': '__main__', '__doc__': None})
        ModelFactory.__memoized[key] = cls
        return cls

    #__
    #make = staticmethod(make)

    pass # end of class
