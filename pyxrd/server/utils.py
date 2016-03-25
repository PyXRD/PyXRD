# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import logging
logger = logging.getLogger(__name__)

import sys, os, time, subprocess
import signal
import atexit

def kill_child(child_pid):
    if child_pid is None:
        pass
    else:
        os.kill(child_pid, signal.SIGTERM)

def start_script(local_script_name, auto_kill=True, log_file=None):
    encoding = sys.getfilesystemencoding()
    if hasattr(sys, "frozen"):
        module_path = os.path.dirname(unicode(sys.executable, encoding))
    else:
        module_path = os.path.dirname(unicode(__file__, encoding))
    path = os.path.join(module_path, local_script_name)

    logging.info("Starting server using script: '%s', logging to '%s'" % (path, log_file))
    log_file = log_file if log_file is not None else os.devnull
    with open(log_file, 'w') as output:
        proc = subprocess.Popen(["python", path], stdout=output)

    # Register this child pid to be killed when the parent dies:
    if auto_kill:
        atexit.register(kill_child, proc.pid)

    # Give it a sec
    time.sleep(1)
