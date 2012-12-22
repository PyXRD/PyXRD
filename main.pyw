#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import warnings
import argparse, sys, os
import gtk

import settings

import generic.gtkexcepthook
from generic.loggers import PyXRDLogger
from generic.update import update

from project.models import Project
from application.models import AppModel
from application.views import AppView
from application.controllers import AppController

if __name__ == "__main__":

    #setup & parse keyword arguments:
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs="?", default="", help="A PyXRD project filename", )
    parser.add_argument("-s", "--script", default="", help="Can be used to pass a script containing a run() function")
    args = parser.parse_args()
    del parser #free some memory

    #start our logging service, prints to stdout and errors.log file
    PyXRDLogger.start_logging()

    #check for updates
    update()

    #apply settings
    settings.apply_runtime_settings(args.script)

    if args.script: #SCRIPT
        try:
            import imp
            user_script = imp.load_source('user_script', args.script)
        except:
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
