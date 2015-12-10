#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import warnings
import os
import logging
logger = logging.getLogger(__name__)

try:
    import gtk
    import gobject
except ImportError:
    logger.warning("Could not import gtk or gobject!")
else:
    # Initialize multi-threading in gtk:
    gtk.gdk.threads_init() # @UndefinedVariable
    gobject.threads_init() # @UndefinedVariable

def _run_user_script():
    """
        Runs the user script specified in the command-line arguments.
    """
    from pyxrd.data import settings

    try:
        import imp
        user_script = imp.load_source('user_script', settings.ARGS.script)
    except any as err:
        err.args = "Error when trying to import %s: %s" % (settings.ARGS.script, err.args)
        raise
    user_script.run(settings.ARGS)

def _run_gui(project=None):

    # Display a splash screen showing the loading status...
    from pkg_resources import resource_filename # @UnresolvedImport
    from pyxrd.application.splash import SplashScreen
    from pyxrd import __version__

    filename = resource_filename(__name__, "application/icons/pyxrd.png")
    splash = SplashScreen(filename, __version__)

    # Run GUI:
    splash.set_message("Loading GUI ...")

    # Now we can load these:
    from pyxrd.data import settings
    from pyxrd.project.models import Project
    from pyxrd.application.models import AppModel
    from pyxrd.application.views import AppView
    from pyxrd.application.controllers import AppController
    from pyxrd.generic.gtk_tools.gtkexcepthook import plugin_gtk_exception_hook

    filename = settings.ARGS.filename #@UndefinedVariable

    # Check if a filename was passed, if so try to load it
    if filename != "":
        try:
            logging.info("Opening project: %s" % filename)
            project = Project.load_object(filename)
        except IOError:
            logging.info("Could not load project file %s: IOError" % filename)
            # FIXME the user should be informed of this in a dialog...

    # Disable unity overlay scrollbars as they cause bugs with modal windows
    os.environ['LIBOVERLAY_SCROLLBAR'] = '0'
    os.environ['UBUNTU_MENUPROXY'] = ""

    if not settings.DEBUG:
        warnings.filterwarnings(action='ignore', category=Warning)

    # Close splash screen
    if splash: splash.close()

    # Nice GUI error handler:
    gtk_exception_hook = plugin_gtk_exception_hook()

    # setup MVC:
    m = AppModel(project=project)
    v = AppView()
    AppController(m, v, gtk_exception_hook=gtk_exception_hook)

    # Free this before continuing
    del splash

    # lets get this show on the road:
    gtk.main()

def run_main():
    """
        Parsers command line arguments and launches PyXRD accordingly.
    """

    # Get settings
    from pyxrd.data import settings

    if settings.DEBUG:
        from pyxrd import stacktracer
        stacktracer.trace_start(
            "trace.html",
            interval=5, auto=True) # Set auto flag to always update file!

    try:
        if settings.ARGS.script:
            # Run the specified user script:
            _run_user_script()
        else:
            # Run the GUI:
            _run_gui()
    except:
        raise # re-raise the error
    finally:
        for finalizer in settings.FINALIZERS:
            finalizer()
        if settings.DEBUG: stacktracer.trace_stop()
