#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

if __name__ == "__main__":

    from generic.loggers import PyXRDLogger
    PyXRDLogger.start_logging()

    from generic.update import update
    update()
    
    from application.models import AppModel
    from application.views import AppView
    from application.controllers import AppController
    import settings
    import gtk
        
    settings.apply_runtime_settings()
    
    gtk.gdk.threads_init()

    import sys
    project = None
    if (len(sys.argv) > 1) and sys.argv[1]!="":
        from project.models import Project
        filename = sys.argv[1]
        try:
            print "Opening: %s" % filename
            project = Project.load_object(filename)
        except IOError as e:
            print 'Could not load file: IOError'

    m = AppModel(project=project)
    v = AppView()
    c = AppController(m, v)
    
        
    gtk.main()
    PyXRDLogger.stop_logging()
