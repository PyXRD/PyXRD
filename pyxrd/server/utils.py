# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import sys, os, time, subprocess, platform
import signal
import atexit

pythonexe = "python3"
if platform.system() == "Windows":
    pythonexe = "python3w"

def kill_child(child_pid):
    if child_pid is None:
        pass
    else:
        os.kill(child_pid, signal.SIGTERM)

def start_script(local_script_name, auto_kill=True, log_file=None):
    global pythonexe
    
    if hasattr(sys, "frozen"):
        module_path = os.path.dirname(sys.executable)
    else:
        module_path = os.path.dirname(__file__)
    path = os.path.join(module_path, local_script_name)

    logging.info("Starting server using script: '%s', logging to '%s'" % (path, log_file))
    log_file = log_file if log_file is not None else os.devnull
    with open(log_file, 'w') as output:
        proc = subprocess.Popen([pythonexe, path], stdout=output)

    # Register this child pid to be killed when the parent dies:
    if auto_kill:
        atexit.register(kill_child, proc.pid)

    # Give it a sec
    time.sleep(1)
