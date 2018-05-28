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

from distutils.version import LooseVersion

def _cmp (self, other):
    if isinstance(other, str):
        other = LooseVersion(other)

    stypes = map(lambda c: str if isinstance(c, str) else int, self.version)
    otypes = map(lambda c: str if isinstance(c, str) else int, other.version)
    
    for i, (stype, otype) in enumerate(zip(stypes, otypes)):
        if stype == str and otype == int:
            other.version[i] = str(other.version[i])
        if stype == int and otype == str:
            self.version[i] = str(self.version[i])
    
    if self.version == other.version:
        return 0
    if self.version < other.version:
        return -1
    if self.version > other.version:
        return 1
            
LooseVersion._cmp = _cmp