# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.
        
def project_run(projectf, stop_processing, methods):
    """
        A target function for multiprocessing purposes.
        Takes a project JSON string, a stop_processing event and
        a list of (method_class, args) tuples as arguments.
    """
    import settings
    settings.CACHE = None #disable caching, things that won't change should already be cached at this point.
    if not settings.SETTINGS_APPLIED:
        settings.apply_runtime_settings(False)
    
    from project.models import Project
    try:
        from cStringIO import StringIO
    except:
        from StringIO import StringIO
    
    f = StringIO()
    f.write(projectf)
    project = Project.load_object(f)

    methods = [
        method_class(*(args + (project,))) for method_class, args in methods
    ]

    while not stop_processing.is_set():
        for method in methods:
            method()
            
    for method in methods:
        method.clean()
        
    del project
    del methods
