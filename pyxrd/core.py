#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import multiprocessing

from traceback import print_exc
import warnings
import argparse, os

try:
    import gtk
except ImportError:
    pass

def _worker_initializer(*args):
    from pyxrd.data import settings
    if settings.CACHE == "FILE":
        settings.CACHE = "FILE_FETCH_ONLY"
    settings.apply_runtime_settings(no_gui=True)

def _initialize_pool():
    # Set this up before we do anything else,
    # creates 'clean' subprocesses
    return multiprocessing.Pool(maxtasksperchild=100, initializer=_worker_initializer)

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

def _check_for_updates():
    from pyxrd.generic.update import update
    update()

def _apply_settings(args, pool):
    from pyxrd.data import settings
    # apply settings
    settings.apply_runtime_settings(no_gui=args.script, debug=args.debug, pool=pool)

    # clean out the file cache if asked and from time to time:
    if settings.CACHE == "FILE":
        from pyxrd.generic.caching import memory
        if args.clear_cache:
            memory.clear()
        else:
            from pyxrd.generic.io import get_size, sizeof_fmt
            size = get_size(memory.cachedir, settings.CACHE_SIZE)
            print "Cache size is (at least):", sizeof_fmt(size)
            if size > settings.CACHE_SIZE:
                memory.clear()

def _run_user_script(args):
    """
        Runs the user script specified in the command-line arguments.
    """
    from pyxrd.data import settings
    try:
        import imp
        user_script = imp.load_source('user_script', args.script)
    except:
        if settings.DEBUG: pass
        print_exc()
        raise ImportError, "Error when trying to import %s" % args.script
    user_script.run(args)

def _close_pool(pool):
    print "Closing pool ..."
    # Close the pool:
    pool.close()
    pool.join()

def _run_gui(args, splash=None):
    # Now we can load these:
    from pyxrd.data import settings
    from pyxrd.project.models import Project
    from pyxrd.application.models import AppModel
    from pyxrd.application.views import AppView
    from pyxrd.application.controllers import AppController
    from pyxrd.generic.gtk_tools.gtkexcepthook import plugin_gtk_excepthook

    # Initialize threads

    # Check if a filename was passed, if so try to load it
    project = None
    if args.filename != "":
        try:
            print "Opening: %s" % args.filename
            project = Project.load_object(args.filename)
        except IOError:
            print 'Could not load file %s: IOError' % args.filename
            # FIXME the user should be informed of this in a dialog...

    # Disable unity overlay scrollbars as they cause bugs with modal windows
    os.environ['LIBOVERLAY_SCROLLBAR'] = '0'
    os.environ['UBUNTU_MENUPROXY'] = ""

    if not settings.DEBUG:
        warnings.simplefilter('ignore', Warning)

    # Close splash screen
    if splash: splash.close()

    # Nice GUI error handler:
    plugin_gtk_excepthook()

    # setup MVC:
    m = AppModel(project=project)
    v = AppView()
    AppController(m, v)

    # Free this before continuing
    del args
    del project
    del splash

    # lets get this show on the road:
    gtk.main()

def run_user_script(args=None):

    # Check if this is already provided:
    if not isinstance(args, argparse.ArgumentParser):
        args = _parse_args()

    # Initialize multiprocessing pool:
    pool = _initialize_pool()

    # start our logging service, prints to stdout and errors.log file
    from pyxrd.generic.loggers import PyXRDLogger
    PyXRDLogger.start_logging()

    # Apply settings
    _apply_settings(args, pool)

    # Run user script:
    try:
        _run_user_script(args)
    except:
        raise # re-raise the error
    finally:
        _close_pool(pool)

    PyXRDLogger.stop_logging()

def run_gui(args=None):

    # Display a splash screen showing the loading status...
    from pkg_resources import resource_filename # @UnresolvedImport
    from pyxrd.generic.views.splash import SplashScreen
    from pyxrd import __version__
    filename = resource_filename(__name__, "application/icons/pyxrd.png")
    splash = SplashScreen(filename, __version__)

    # Check if this is already provided:
    splash.set_message("Parsing arguments ...")
    if not isinstance(args, argparse.ArgumentParser):
        args = _parse_args()

    # Initialize multiprocessing pool:
    splash.set_message("Initializing pool ...")
    pool = _initialize_pool()

    # Start our logging service, prints to stdout and errors.log file
    splash.set_message("Setting up logger ...")
    from pyxrd.generic.loggers import PyXRDLogger
    PyXRDLogger.start_logging()

    # Check for updates
    splash.set_message("Checking for updates ...")
    _check_for_updates()

    # Apply settings
    splash.set_message("Applying settings ...")
    _apply_settings(args, pool)

    # Run GUI:
    splash.set_message("Loading GUI ...")
    try:
        _run_gui(args, splash)
    except:
        raise # re-raise the error
    finally:
        _close_pool(pool)

    # Stop the logger:
    PyXRDLogger.stop_logging()

def run_main():
    """
        Parsers command line arguments and launches PyXRD accordingly.
    """

    # Setup & parse keyword arguments:
    args = _parse_args()

    if args.script:
        # Run the specified user script:
        run_user_script(args)
    else:
        # Run the GUI:
        run_gui(args)
