#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import warnings
import argparse, os
import logging
logger = logging.getLogger(__name__)

try:
    import gtk
    gtk.gdk.threads_init() # @UndefinedVariable
except ImportError:
    pass

def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filename", nargs="?", default="",
        help="A PyXRD project filename"
    )
    parser.add_argument(
        "-s", "--script", default="",
        help="Can be used to pass a script containing a run() function"
    )
    parser.add_argument(
        "-d", "--debug", dest='debug', action='store_const',
        const=True, default=False,
        help='Run in debug mode'
    )
    parser.add_argument(
        "-c", "--clear-cache", dest='clear_cache', action='store_const',
        const=True, default=False,
        help='Clear the cache (only relevant if using filesystem cache)'
    )

    args = parser.parse_args()
    del parser # free some memory
    return args

def _setup_logging(debug, log_file, scripted=False):
    if not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file))

    if not scripted:
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename=log_file,
                            filemode='w')

        # Get root logger:
        logger = logging.getLogger()

        # Setup error stream:
        console = logging.StreamHandler()
        full = logging.Formatter("%(name)s - %(levelname)s: %(message)s")
        console.setFormatter(full)

        # Add console logger to the root logger:
        logger.addHandler(console)
    else:
        # Very basic output for the root object:
        logging.basicConfig(format='%(name)s - %(levelname)s: %(message)s')

def _apply_settings(no_gui, debug, clear_cache):

    from pyxrd.data import settings
    # apply settings
    settings.apply_runtime_settings(no_gui=no_gui, debug=debug)

    _setup_logging(settings.DEBUG, settings.LOG_FILENAME, no_gui)

    # clean out the file cache if asked and from time to time:
    if settings.CACHE == "FILE":
        from pyxrd.generic.caching import memory
        if clear_cache:
            def onerror(*args):
                # ignore errors if not debugging
                if not settings.DEBUG: pass
                else: raise
            memory.clear(onerror=onerror)
        else:
            from pyxrd.generic.io import get_size, sizeof_fmt
            size = get_size(memory.cachedir, settings.CACHE_SIZE)
            logging.info("Cache size is (at least): %s" % sizeof_fmt(size))
            if size > settings.CACHE_SIZE:
                memory.clear()

    return settings

def _run_user_script(args):
    """
        Runs the user script specified in the command-line arguments.
    """
    try:
        import imp
        user_script = imp.load_source('user_script', args.script)
    except any as err:
        err.args = "Error when trying to import %s: %s" % (args.script, err.args)
        raise
    user_script.run(args)

def _run_gui(args):

    # Display a splash screen showing the loading status...
    from pkg_resources import resource_filename # @UnresolvedImport
    from pyxrd.application.splash import SplashScreen
    from pyxrd import __version__

    filename = resource_filename(__name__, "application/icons/pyxrd.png")
    splash = SplashScreen(filename, __version__)

    # Check if this is already provided:
    splash.set_message("Parsing arguments ...")
    if not isinstance(args, argparse.ArgumentParser):
        args = _parse_args()

    # Run GUI:
    splash.set_message("Loading GUI ...")

    # Now we can load these:
    from pyxrd.data import settings
    from pyxrd.project.models import Project
    from pyxrd.application.models import AppModel
    from pyxrd.application.views import AppView
    from pyxrd.application.controllers import AppController
    from pyxrd.generic.gtk_tools.gtkexcepthook import plugin_gtk_exception_hook

    # Check if a filename was passed, if so try to load it
    project = None
    if args.filename != "":
        try:
            logging.info("Opening project: %s" % args.filename)
            project = Project.load_object(args.filename)
        except IOError:
            logging.info("Could not load project file %s: IOError" % args.filename)
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
    del args
    del project
    del splash

    # lets get this show on the road:
    gtk.main()

def run_main():
    """
        Parsers command line arguments and launches PyXRD accordingly.
    """

    # Setup & parse keyword arguments:
    args = _parse_args()

    # Apply settings
    settings = _apply_settings(bool(args.script), args.debug, args.clear_cache)

    try:
        if args.script:
            # Run the specified user script:
            _run_user_script(args)
        else:
            # Run the GUI:
            _run_gui(args)
    except:
        raise # re-raise the error
    finally:
        for finalizer in settings.FINALIZERS:
            finalizer()
