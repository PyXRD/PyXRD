#!/usr/bin/env bash
# Copyright 2018 Mathijs Dumon
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# Exit when any process fails
set -e

# Get directory of filename, move into it and return the current dir
DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "${DIR}"

# CONFIG START

ARCH="i686"
BUILD_VERSION="0"

# CONFIG END

MISC="${DIR}"/misc
if [ "${ARCH}" = "x86_64" ]; then
    MINGW="mingw64"
else
    MINGW="mingw32"
fi

PYXRD_VERSION="0.0.0"
PYXRD_VERSION_DESC="UNKNOWN"

function set_build_root {
    BUILD_ROOT="$1"
    REPO_CLONE="${BUILD_ROOT}"/pyxrd
    MINGW_ROOT="${BUILD_ROOT}/${MINGW}"
}

set_build_root "${DIR}/_build_root"

function build_pacman {
    pacman --root "${BUILD_ROOT}" "$@"
}

function build_pip {
    "${BUILD_ROOT}"/"${MINGW}"/bin/python3.exe -m pip "$@"
}

function build_python {
    "${BUILD_ROOT}"/"${MINGW}"/bin/python3.exe "$@"
}

function build_compileall {
    MSYSTEM= build_python -m compileall -b "$@"
}

function install_pre_deps {
    pacman -S --needed --noconfirm p7zip git dos2unix \
        mingw-w64-"${ARCH}"-nsis wget intltool mingw-w64-"${ARCH}"-toolchain
}

function create_root {
    mkdir -p "${BUILD_ROOT}"

    mkdir -p "${BUILD_ROOT}"/var/lib/pacman
    mkdir -p "${BUILD_ROOT}"/var/log
    mkdir -p "${BUILD_ROOT}"/tmp

    build_pacman -Syu
    build_pacman --noconfirm -S base
}

function extract_installer {
    [ -z "$1" ] && (echo "Missing arg"; exit 1)

    mkdir -p "$BUILD_ROOT"
    7z x -o"$MINGW_ROOT" "$1"
    rm -rf "$MINGW_ROOT"/'$PLUGINSDIR' "$MINGW_ROOT"/*.txt "$MINGW_ROOT"/*.nsi
}

function install_deps {

    # We don't use the fontconfig backend, and this skips the lengthy
    # cache update step during package installation
    export MSYS2_FC_CACHE_SKIP=1

    build_pacman --noconfirm -S \
        git \
        mingw-w64-"${ARCH}"-gdk-pixbuf2 \
        mingw-w64-"${ARCH}"-gtk3 \
        mingw-w64-"${ARCH}"-python3 \
		mingw-w64-"${ARCH}"-python3-setuptools \
        mingw-w64-"${ARCH}"-python3-gobject \
		mingw-w64-"${ARCH}"-python3-cffi \
        mingw-w64-"${ARCH}"-python3-cairo \
        mingw-w64-"${ARCH}"-python3-pip \
        mingw-w64-"${ARCH}"-python3-pytest \
		mingw-w64-"${ARCH}"-python3-numpy \
		mingw-w64-"${ARCH}"-python3-scipy \
		mingw-w64-"${ARCH}"-python3-dateutil \
		mingw-w64-"${ARCH}"-python3-pyparsing \
		mingw-w64-"${ARCH}"-python3-cycler \
		mingw-w64-"${ARCH}"-python3-kiwisolver \
		mingw-w64-"${ARCH}"-freetype \
		mingw-w64-"${ARCH}"-libpng \
		mingw-w64-"${ARCH}"-qhull
	build_pacman --noconfirm -U \
		"$MISC"/mingw-w64-i686-python3-matplotlib-2.2.2-1-any.pkg.tar.xz

    PIP_REQUIREMENTS="\
Pyro4>=4.41
deap>=1.0.1
ez_setup
cairocffi"

    build_pip install --upgrade \
        --force-reinstall $(echo "$PIP_REQUIREMENTS" | tr ["\\n"] [" "])
		
    build_pacman --noconfirm -Rdds \
        mingw-w64-"${ARCH}"-shared-mime-info \
        mingw-w64-"${ARCH}"-tk \
        mingw-w64-"${ARCH}"-tcl

    build_pacman --noconfirm -Rdds mingw-w64-"${ARCH}"-python2 || true

    build_pacman -S --noconfirm mingw-w64-"${ARCH}"-python3-setuptools
	
}

function install_pyxrd {
    [ -z "$1" ] && (echo "Missing arg"; exit 1)

    rm -Rf "${REPO_CLONE}"
    git clone "${DIR}"/.. "${REPO_CLONE}"

	# checkout correct version
    (cd "${REPO_CLONE}" && git checkout "$1") || exit 1

	# install it
	(cd "${REPO_CLONE}" && build_pip install . || exit 1)
    #build_python "${REPO_CLONE}"/setup.py install

    # Create launchers
    PYXRD_VERSION=$(MSYSTEM= build_python -c \
        "from pyxrd import __version__; import sys; sys.stdout.write(__version__)")
    PYXRD_VERSION_DESC="$PYXRD_VERSION"
	
    if [ "$1" = "master" ]
    then
        local GIT_REV=$(git rev-list --count HEAD)
        local GIT_HASH=$(git rev-parse --short HEAD)
        PYXRD_VERSION_DESC="$PYXRD_VERSION-rev$GIT_REV-$GIT_HASH"
    fi
	
    python3 "${MISC}"/create-launcher.py \
        "${PYXRD_VERSION}" "${MINGW_ROOT}"/bin

	# Copy over theme:
	cp -Rf "$MISC"/gtk-3.0 	"$MINGW_ROOT"/share/
	cp -Rf "$MISC"/themes 	"$MINGW_ROOT"/share/
	"${MINGW_ROOT}"/bin/gtk-update-icon-cache-3.0.exe \
        "${MINGW_ROOT}"/share/themes/Windows8
		
	# Compile python files
    build_compileall -d "" -f -q "$(cygpath -w "${MINGW_ROOT}")"
	
}

function cleanup_before {
    ## these all have svg variants
    #find "${MINGW_ROOT}"/share/icons -name "*.symbolic.png" -exec rm -f {} \;

    ## remove some larger ones
    rm -Rf "${MINGW_ROOT}/share/icons/Adwaita/512x512"
    rm -Rf "${MINGW_ROOT}/share/icons/Adwaita/256x256"
    rm -Rf "${MINGW_ROOT}/share/icons/Adwaita/96x96"
    rm -Rf "${MINGW_ROOT}/share/icons/Adwaita/48x48"
    "${MINGW_ROOT}"/bin/gtk-update-icon-cache-3.0.exe \
        "${MINGW_ROOT}"/share/icons/Adwaita

    # remove some gtk demo icons
    find "${MINGW_ROOT}"/share/icons/hicolor -name "gtk3-*" -exec rm -f {} \;
    "${MINGW_ROOT}"/bin/gtk-update-icon-cache-3.0.exe \
        "${MINGW_ROOT}"/share/icons/hicolor

    # python related, before installing pyxrd
    rm -f "${MINGW_ROOT}"/lib/python3.*/lib-dynload/_tkinter*
    find "${MINGW_ROOT}"/lib/python3.* -type d  \( -iname "test*" ! \( -path "*testing*" ! -path "*testing/tests*" \) \) \
        -prune -exec rm -rf {} \;
    find "${MINGW_ROOT}"/lib/python3.* -type d -name "*_test*" \
        -prune -exec rm -rf {} \;

    find "${MINGW_ROOT}"/bin -name "*.pyo" -exec rm -f {} \;
    find "${MINGW_ROOT}"/bin -name "*.pyc" -exec rm -f {} \;
    find "${MINGW_ROOT}" -type d -name "__pycache__" -prune -exec rm -rf {} \;

    build_compileall -d "" -f -q "$(cygpath -w "${MINGW_ROOT}")"
    find "${MINGW_ROOT}" -name "*.py" -exec rm -f {} \;
}

function cleanup_after {
    # delete translations we don't support
    #for d in "${MINGW_ROOT}"/share/locale/*/LC_MESSAGES; do
    #    if [ ! -f "${d}"/pyxrd.mo ]; then
    #        rm -Rf "${d}"
    #    fi
    #done

    find "${MINGW_ROOT}" -regextype "posix-extended" -name "*.exe" -a ! \
        -iregex ".*/(pyxrd|python)[^/]*\\.exe" \
        -exec rm -f {} \;

    rm -Rf "${MINGW_ROOT}"/libexec
    rm -Rf "${MINGW_ROOT}"/share/gtk-doc
    rm -Rf "${MINGW_ROOT}"/include
    rm -Rf "${MINGW_ROOT}"/var
    rm -Rf "${MINGW_ROOT}"/etc
    rm -Rf "${MINGW_ROOT}"/share/zsh
    rm -Rf "${MINGW_ROOT}"/share/pixmaps
    rm -Rf "${MINGW_ROOT}"/share/gnome-shell
    rm -Rf "${MINGW_ROOT}"/share/dbus-1
    rm -Rf "${MINGW_ROOT}"/share/gir-1.0
    rm -Rf "${MINGW_ROOT}"/share/doc
    rm -Rf "${MINGW_ROOT}"/share/man
    rm -Rf "${MINGW_ROOT}"/share/info
    rm -Rf "${MINGW_ROOT}"/share/mime
    rm -Rf "${MINGW_ROOT}"/share/gettext
    rm -Rf "${MINGW_ROOT}"/share/libtool
    rm -Rf "${MINGW_ROOT}"/share/licenses
    rm -Rf "${MINGW_ROOT}"/share/appdata
    rm -Rf "${MINGW_ROOT}"/share/aclocal
    rm -Rf "${MINGW_ROOT}"/share/vala
    rm -Rf "${MINGW_ROOT}"/share/readline
    rm -Rf "${MINGW_ROOT}"/share/xml
    rm -Rf "${MINGW_ROOT}"/share/bash-completion
    rm -Rf "${MINGW_ROOT}"/share/common-lisp
    rm -Rf "${MINGW_ROOT}"/share/emacs
    rm -Rf "${MINGW_ROOT}"/share/gdb
    rm -Rf "${MINGW_ROOT}"/share/libcaca
    rm -Rf "${MINGW_ROOT}"/share/gettext
    rm -Rf "${MINGW_ROOT}"/share/libgpg-error
    rm -Rf "${MINGW_ROOT}"/share/p11-kit
    rm -Rf "${MINGW_ROOT}"/share/pki
    rm -Rf "${MINGW_ROOT}"/share/thumbnailers
    rm -Rf "${MINGW_ROOT}"/share/nghttp2
    rm -Rf "${MINGW_ROOT}"/share/fontconfig
    rm -Rf "${MINGW_ROOT}"/share/gettext-*
    rm -Rf "${MINGW_ROOT}"/share/installed-tests

    find "${MINGW_ROOT}"/share/glib-2.0 -type f ! \
        -name "*.compiled" -exec rm -f {} \;

    rm -Rf "${MINGW_ROOT}"/lib/cmake
    rm -Rf "${MINGW_ROOT}"/lib/gettext
    rm -Rf "${MINGW_ROOT}"/lib/gtk-3.0
    rm -Rf "${MINGW_ROOT}"/lib/p11-kit
    rm -Rf "${MINGW_ROOT}"/lib/pkcs11
    rm -Rf "${MINGW_ROOT}"/lib/ruby
    rm -Rf "${MINGW_ROOT}"/lib/engines

    rm -f "${MINGW_ROOT}"/bin/libharfbuzz-icu-0.dll
    rm -Rf "${MINGW_ROOT}"/lib/python2.*

    find "${MINGW_ROOT}" -name "*.a" -exec rm -f {} \;
    find "${MINGW_ROOT}" -name "*.whl" -exec rm -f {} \;
    find "${MINGW_ROOT}" -name "*.h" -exec rm -f {} \;
    find "${MINGW_ROOT}" -name "*.la" -exec rm -f {} \;
    find "${MINGW_ROOT}" -name "*.sh" -exec rm -f {} \;
    find "${MINGW_ROOT}" -name "*.jar" -exec rm -f {} \;
    find "${MINGW_ROOT}" -name "*.def" -exec rm -f {} \;
    find "${MINGW_ROOT}" -name "*.cmd" -exec rm -f {} \;
    find "${MINGW_ROOT}" -name "*.cmake" -exec rm -f {} \;
    find "${MINGW_ROOT}" -name "*.pc" -exec rm -f {} \;
    find "${MINGW_ROOT}" -name "*.desktop" -exec rm -f {} \;
    find "${MINGW_ROOT}" -name "*.manifest" -exec rm -f {} \;
    find "${MINGW_ROOT}" -name "*.pyo" -exec rm -f {} \;

    find "${MINGW_ROOT}"/bin -name "*-config" -exec rm -f {} \;
    find "${MINGW_ROOT}" -regex ".*/bin/[^.]+" -exec rm -f {} \;
    find "${MINGW_ROOT}" -regex ".*/bin/[^.]+\\.[0-9]+" -exec rm -f {} \;

    find "${MINGW_ROOT}" -name "gtk30-properties.mo" -exec rm -rf {} \;
    find "${MINGW_ROOT}" -name "gettext-tools.mo" -exec rm -rf {} \;
    find "${MINGW_ROOT}" -name "libexif-12.mo" -exec rm -rf {} \;
    find "${MINGW_ROOT}" -name "xz.mo" -exec rm -rf {} \;
    find "${MINGW_ROOT}" -name "libgpg-error.mo" -exec rm -rf {} \;

    find "${MINGW_ROOT}" -name "old_root.pem" -exec rm -rf {} \;
    find "${MINGW_ROOT}" -name "weak.pem" -exec rm -rf {} \;

    find "${MINGW_ROOT}"/bin -name "*.pyo" -exec rm -f {} \;
    find "${MINGW_ROOT}"/bin -name "*.pyc" -exec rm -f {} \;
    find "${MINGW_ROOT}" -type d -name "__pycache__" -prune -exec rm -rf {} \;

	# I think this breaks things for me:
    build_python "${MISC}/depcheck.py" --delete

    find "${MINGW_ROOT}" -type d -empty -delete
}

function build_installer {
	(cd "${MINGW_ROOT}"/lib/python3.*/site-packages/PyXRD/ && build_compileall -d "" -q -f -l .)

    cp misc/pyxrd.ico "${BUILD_ROOT}"
    (cd "$BUILD_ROOT" && makensis -NOCD -DVERSION="$PYXRD_VERSION_DESC" "${MISC}"/win_installer.nsi)

    mv "$BUILD_ROOT/pyxrd-LATEST.exe" "$DIR/pyxrd-$PYXRD_VERSION_DESC-installer.exe"
}

function build_portable_installer {
	(cd "${MINGW_ROOT}"/lib/python3.*/site-packages/PyXRD/ && build_compileall -d "" -q -f -l .)
	
    local PORTABLE="$DIR/pyxrd-$PYXRD_VERSION_DESC-portable"

    rm -rf "$PORTABLE"
    mkdir "$PORTABLE"
    cp "$MISC"/pyxrd.lnk "$PORTABLE"
    cp "$MISC"/README-PORTABLE.txt "$PORTABLE"/README.txt
    unix2dos "$PORTABLE"/README.txt
    mkdir "$PORTABLE"/config
    cp -RT "${MINGW_ROOT}" "$PORTABLE"/data

    rm -Rf 7zout 7z1604.exe
    7z a payload.7z "$PORTABLE"
    wget -P "$DIR" -c http://www.7-zip.org/a/7z1604.exe
    7z x -o7zout 7z1604.exe
    cat 7zout/7z.sfx payload.7z > "$PORTABLE".exe
    rm -Rf 7zout 7z1604.exe payload.7z "$PORTABLE"
}
