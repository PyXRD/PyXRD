#!/usr/bin/env bash
# Copyright 2016 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

set -e

function main {
    pacman --noconfirm -Suy

	# GTK deps:
    pacman --noconfirm -S --needed \
        git mingw-w64-i686-gdk-pixbuf2 \
        mingw-w64-i686-gtk3 \
        base-devel mingw-w64-i686-toolchain

	#Python and related deps:	
	
    pacman --noconfirm -S --needed \
        mingw-w64-i686-python3 \
		mingw-w64-i686-python3-setuptools \
        mingw-w64-i686-python3-gobject \
		mingw-w64-i686-python3-cffi \
        mingw-w64-i686-python3-cairo \
        mingw-w64-i686-python3-pip \
        mingw-w64-i686-python3-pytest \
		mingw-w64-i686-python3-numpy \
		mingw-w64-i686-python3-scipy \
		mingw-w64-i686-python3-dateutil \
		mingw-w64-i686-python3-pyparsing \
		mingw-w64-i686-python3-cycler \
		mingw-w64-i686-python3-kiwisolver \
		mingw-w64-i686-freetype \
		mingw-w64-i686-libpng \
		mingw-w64-i686-qhull
		
	# Matplotlib requires some special treatment:
	# cd misc/mingw-w64-python-matplotlib
	# MMINGW_INSTALLS=mingw64 makepkg-mingw -sLfcCi --noconfirm
	# cd ../..
	# Kept the packaged version, we need to update this from time to time using the above
	
	pacman --noconfirm -U misc/mingw-w64-i686-python3-matplotlib-2.2.2-1-any.pkg.tar.xz
	
	pip3 install --user cairocffi deap Pyro4\>\=4.41
}

main;
