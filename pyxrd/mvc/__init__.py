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

# FIXME clean this mess up

"""
Shortcuts are provided to the following classes defined in submodules:

.. class:: Model
   :noindex:
.. class:: TreeStoreModel
   :noindex:
.. class:: ListStoreModel
   :noindex:
.. class:: TextBufferModel
   :noindex:
.. class:: ModelMT
   :noindex:
.. class:: Controller
   :noindex:
.. class:: View
   :noindex:
.. class:: Observer
   :noindex:
.. class:: Observable
   :noindex:

"""

__all__ = ["Model",
           "ModelMT",
           "Controller", "View", "Observer",
           "Observable",
           "PropIntel", "OptionPropIntel", "UUIDPropIntel", "AliasPropIntel",
           "observable", "observer", "adapters", # packages
           ]

__version = (1, 99, 1)

# Load this so logging is properly set up
import logging
logger = logging.getLogger(__name__)

# visible classes
from .models import *
try:
    from .model import TreeStoreModel, ListStoreModel, TextBufferModel
except ImportError:
    pass
else:
    __all__ += [ "TreeStoreModel", "ListStoreModel", "TextBufferModel" ]

try:
    from .controller import Controller
    from .view import View
except ImportError:
    pass

from .observer import Observer
from .support.observables import Observable, Signal

# visible modules
import support, observer, adapters

def get_version():
    """
    Return the imported version of this framework as a tuple of integers.
    """
    return __version