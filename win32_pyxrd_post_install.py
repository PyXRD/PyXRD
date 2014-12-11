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

try:
    # When this script is run from inside the bdist_wininst installer,
    # file_created() and directory_created() are additional builtin
    # functions which write lines to Python23\pywin32-install.log. This is
    # a list of actions for the uninstaller, the format is inspired by what
    # the Wise installer also creates.
    file_created
    is_bdist_wininst = True
except NameError:
    is_bdist_wininst = False # we know what it is not - but not what it is :)
    def file_created(file):
        pass

try:
    create_shortcut
except NameError:
    # Create a function with the same signature as create_shortcut provided
    # by bdist_wininst
    def create_shortcut(path, description, filename,
                        arguments="", workdir="", iconpath="", iconindex=0):
        import pythoncom
        from win32com.shell import shell, shellcon

        ilink = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None,
                                           pythoncom.CLSCTX_INPROC_SERVER,
                                           shell.IID_IShellLink)
        ilink.SetPath(path)
        ilink.SetDescription(description)
        if arguments:
            ilink.SetArguments(arguments)
        if workdir:
            ilink.SetWorkingDirectory(workdir)
        if iconpath or iconindex:
            ilink.SetIconLocation(iconpath, iconindex)
        # now save it.
        ipf = ilink.QueryInterface(pythoncom.IID_IPersistFile)
        ipf.Save(filename, 0)

    # Support the same list of "path names" as bdist_wininst.
    def get_special_folder_path(path_name):
        import pythoncom
        from win32com.shell import shell, shellcon

        for maybe in """
            CSIDL_COMMON_STARTMENU CSIDL_STARTMENU CSIDL_COMMON_APPDATA
            CSIDL_LOCAL_APPDATA CSIDL_APPDATA CSIDL_COMMON_DESKTOPDIRECTORY
            CSIDL_DESKTOPDIRECTORY CSIDL_COMMON_STARTUP CSIDL_STARTUP
            CSIDL_COMMON_PROGRAMS CSIDL_PROGRAMS CSIDL_PROGRAM_FILES_COMMON
            CSIDL_PROGRAM_FILES CSIDL_FONTS""".split():
            if maybe == path_name:
                csidl = getattr(shellcon, maybe)
                return shell.SHGetSpecialFolderPath(0, csidl, False)
        raise ValueError("%s is an unknown path ID" % (path_name,))

DESKTOP_FOLDER = get_special_folder_path("CSIDL_COMMON_DESKTOPDIRECTORY") # @UndefinedVariable
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
