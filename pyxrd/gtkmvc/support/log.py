#  -------------------------------------------------------------------------
#  Author: Roberto Cavada <roboogle@gmail.com>
#
#  Copyright (C) 2010 by Roberto Cavada
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

"""
This module sets up the internal logging of the framework. By default errors
will be printed to STDERR while warnings won't be shown at all.

During development it is recommended that you run the following *after*
importing gtkmc. Remember to take it out before shipping your application. ::

 import logging
 logging.getLogger("gtkmvc").setLevel(logging.DEBUG)
"""

import logging

full = logging.Formatter("%(name)s - %(levelname)s: %(message)s")

stderr = logging.StreamHandler()
stderr.setFormatter(full)

logger = logging.getLogger("gtkmvc")
logger.addHandler(stderr)

logger.setLevel(logging.ERROR)

# 1.99.0 compatibility.
ch = stderr
