#! python
# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os
import sys
import shutil
from pkg_resources import resource_filename # @UnresolvedImport
import pyxrd

DESKTOP_FOLDER = get_special_folder_path("CSIDL_DESKTOPDIRECTORY") # @UndefinedVariable
NAME = 'PyXRD.lnk'

if sys.argv[1] == '-install':
    create_shortcut(# @UndefinedVariable
        os.path.join(sys.prefix, 'pythonw.exe'), # Program
        'Run PyXRD', # Description
        NAME, # Filename
        os.path.join(sys.prefix, 'Scripts/PyXRD-script.pyw'), # Arguments
        '', # Work dir
        resource_filename("pyxrd.application", "icons/pyxrd.ico") # icon path
    )
    # move shortcut from current directory to DESKTOP_FOLDER
    shutil.move(os.path.join(os.getcwd(), NAME),
                os.path.join(DESKTOP_FOLDER, NAME))
    # tell windows installer that we created another
    # file which should be deleted on uninstallation
    file_created(os.path.join(DESKTOP_FOLDER, NAME)) # @UndefinedVariable

if sys.argv[1] == '-remove':
    pass
    # This will be run on uninstallation. Nothing to do.
