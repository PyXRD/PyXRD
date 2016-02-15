#!/usr/bin/python

# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import os, sys
from pyxrd.project.models import Project


def run(args):
    # generates a project file containing the phases as described by the Sybilla XML output:
    if args and args.filename != "":
        # Import:
        project = Project.create_from_sybilla_xml(args.filename)

        # Save this right away:
        project_filename = "%s/%s" % (os.path.dirname(args.filename), os.path.basename(args.filename).replace(".xml", ".pyxrd", 1))

        from pyxrd.file_parsers.json_parser import JSONParser
        JSONParser.write(project, project_filename, zipped=True)

        # Relaunch processs
        args = [sys.argv[0], project_filename, ]
        args.insert(0, sys.executable)
        if sys.platform == 'win32':
            args = ['"%s"' % arg for arg in args]
        os.execv(sys.executable, args)
        sys.exit(0)

