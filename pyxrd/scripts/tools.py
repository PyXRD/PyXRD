#!/usr/bin/python
# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

"""
    Tools for making scripting easier
"""

def reload_settings(clear_script=True):
    """
        This will reload the PyXRD settings after clearing the script path from
        the command line arguments. This allows to run the GUI when needed.
    """
    import sys
    from copy import copy

    # Make a copy to prevent errors
    args = copy(sys.argv)
    for i, arg in enumerate(args):
        if arg == "-s":
            # Clear the next key (contains the script name
            del sys.argv[i + 1]
            # Clear the flag
            del sys.argv[i]
            # Exit the loop
            break

    from pyxrd.data import settings
    settings.SETTINGS_APPLIED = False # clear this flag to reload settings
    settings.initialize() # reload settings

def launch_gui(project=None):
    """ Launches the GUI, you should run reload_settings before calling this! """
    from pyxrd.core import _run_gui
    _run_gui(project=project) # launch gui