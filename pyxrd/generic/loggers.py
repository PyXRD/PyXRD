# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import sys
import os
from pyxrd.data import settings
import logging

class PyXRDLogger(object):
    ready = False

    def __init__(self, filename):
        object.__init__(self)
        self.saveout = sys.stdout
        self.saveerr = sys.stderr

        sys.stdout = self
        sys.stderr = self
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        self.logfile = file(filename, 'w')

        self.logger = logging.getLogger("gtkmvc")
        hdlr = logging.StreamHandler(self)
        self.logger.addHandler(hdlr)
        self.ready = True
        if settings.DEBUG:
            self.logger.setLevel(logging.DEBUG)

    def write(self, text):
        if self.ready:
            self.saveout.write(text)
            # self.logfile.write(text)
            # self.logfile.flush()
            # os.fsync(self.logfile.fileno())

    def close(self):
        if self.ready:
            self.saveout.close()
            self.logfile.flush()
            os.fsync(self.logfile.fileno())
            self.logfile.close()
            self.ready = False

    def flush(self):
        if self.ready:
            self.logfile.flush()

    def restore(self):
        sys.stdout = self.saveout
        sys.stderr = self.saveerr

    @classmethod
    def start_logging(cls):
        cls.writer = PyXRDLogger(settings.LOG_FILENAME)

    @classmethod
    def stop_logging(cls):
        cls.writer.restore()

    # def __del__(self):
    #    self.close()
    #    object.__del__(self)
