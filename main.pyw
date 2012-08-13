#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs="?", default="", help="A PyXRD project filename", )
    parser.add_argument("-n", "--no-gui", default=False, help="Do not start the GUI", action="store_true")
    parser.add_argument("-s", "--script", default="", help="Can be used to pass a script containing a run(project) function, implies -n")
    args = parser.parse_args()

    #start our logging service, prints to stdout and errors.log file
    from generic.loggers import PyXRDLogger
    PyXRDLogger.start_logging()

    #check for updates
    from generic.update import update
    update()

    #apply settings
    import settings
    settings.apply_runtime_settings(args.no_gui)

    #check if a filename was passed, if so try to load it
    from project.models import Project
    
    project = None
    if args.filename!="":
        try:
            print "Opening: %s" % args.filename
            project = Project.load_object(args.filename)
        except IOError:
            print 'Could not load file %s: IOError' % args.filename

    if args.no_gui or args.script:
        if project==None:
            print "No PyXRD project filename passed, exiting..."
        else:
            if args.script:
                try:
                    import imp
                    user_script = imp.load_source('user_script', args.script)
                except:
                    raise ImportError, "Error when trying to import run() from %s" % args.script
                user_script.run(project)
    else:
        #disable unity overlay scrollbars as they cause bugs with modal windows
        import sys, os
        os.environ['LIBOVERLAY_SCROLLBAR'] = '0'
       
        #after update, load our application modules
        from application.models import AppModel
        from application.views import AppView
        from application.controllers import AppController
        import gtk
            
        #init threads
        gtk.gdk.threads_init()

        #setup MVC:
        m = AppModel(project=project)
        v = AppView()
        c = AppController(m, v)
        
        #lets get this show on the road:
        gtk.gdk.threads_enter()
        gtk.main()
        gtk.gdk.threads_leave()
        
    #stop the logger:
    PyXRDLogger.stop_logging()
