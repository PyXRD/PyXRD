#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from traceback import print_exc
import warnings
import argparse, sys, os
import gtk

import settings

import generic.gtkexcepthook
from generic.loggers import PyXRDLogger
from generic.update import update

if __name__ == "__main__":
    #setup & parse keyword arguments:
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs="?", default="", help="A PyXRD project filename", )
    parser.add_argument("-s", "--script", default="", help="Can be used to pass a script containing a run() function")
    parser.add_argument("-t", "--test", dest='test', action='store_const',
        const=True, default=False,
        help='Runs the tests for PyXRD')
    parser.add_argument("-c", "--clear-cache", dest='clear_cache', action='store_const',
        const=True, default=False, help='Clear the cache (only relevant if using filesystem cache)')
    args = parser.parse_args()
    del parser #free some memory

    if args.test:
        #run the test framework and leave:
        del sys.argv[1]
        from tests import run_all_tests
        run_all_tests()
    else:
        #start our logging service, prints to stdout and errors.log file
        PyXRDLogger.start_logging()
    
        #check for updates
        update()

        #apply settings
        settings.apply_runtime_settings(args.script)
        
        #clean out the file cache if asked and from time to time:
        if settings.CACHE == "FILE":
            from generic.caching import memory        
            if args.clear_cache:
                memory.clear()
            else:
                from generic.io import get_size, sizeof_fmt
                size = get_size(memory.cachedir)
                print "Cache size is:", sizeof_fmt(size)
                if size > settings.CACHE_SIZE:
                    memory.clear()
        
        #now we can load these:    
        from project.models import Project
        from application.models import AppModel
        from application.views import AppView
        from application.controllers import AppController

        if args.script: #SCRIPT
            try:
                import imp
                user_script = imp.load_source('user_script', args.script)
            except:
                if settings.DEBUG: print_exc()
                raise ImportError, "Error when trying to import %s" % args.script
            user_script.run(args)
        else: #GUI
        
            #check if a filename was passed, if so try to load it
            project = None
            if args.filename!="":
                try:
                    print "Opening: %s" % args.filename
                    project = Project.load_object(args.filename)
                except IOError:
                    print 'Could not load file %s: IOError' % args.filename
        
            #disable unity overlay scrollbars as they cause bugs with modal windows
            os.environ['LIBOVERLAY_SCROLLBAR'] = '0'
            os.environ['UBUNTU_MENUPROXY'] = ""
                
            if not settings.DEBUG:
                warnings.simplefilter('ignore', Warning)            
                
            #init threads
            gtk.gdk.threads_init()

            #setup MVC:
            m = AppModel(project=project)
            v = AppView()
            c = AppController(m, v)
            del project
            
            #lets get this show on the road:
            gtk.gdk.threads_enter()
            gtk.main()
            gtk.gdk.threads_leave()
        
        #stop the logger:
        PyXRDLogger.stop_logging()
