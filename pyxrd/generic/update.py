# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

import urllib2
import os
import sys
from zipfile import ZipFile
import re

import logging
logger = logging.getLogger(__name__)

import gtk

from pyxrd.data import settings

###
# TODO use PyPI!
# Separate update from view...

def mycmp(version1, version2):
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
    return cmp(normalize(version1), normalize(version2))

class Updater(gtk.Dialog):

    def __init__(self, updates, *args, **kwargs):
        gtk.Dialog.__init__(self, "Updater", None, 0, (gtk.STOCK_EXECUTE, gtk.RESPONSE_APPLY,
                     gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE), *args, **kwargs)

        self.set_border_width(10)
        self.connect("response", self.response)
        self.connect("destroy", self.cancel)

        self.box = self.get_child()

        self.label = gtk.Label("A new version of PyXRD is available.\nDo you want to update now?")
        self.box.pack_start(self.label, False, False, 10)

        self.bar = gtk.ProgressBar()
        self.bar.set_size_request(-1, 30)
        self.box.pack_start(self.bar, False, False, 10)

        self.set_data("progress", self.bar)

        self.run = True
        self.updates = updates
        # Get the filename of the latest version:
        self.filename = updates[0][1]
        self.tempfilename = 'data/latest_version.zip'
        self.currfilename = 'data/current_version.zip'

    def response(self, widget, response_id):
        if response_id != gtk.RESPONSE_APPLY:
            gtk.main_quit()
            self.run = False
        else:
            self.bar.grab_add()

            logger.info("Running Updater")

            try:
                response = urllib2.urlopen(settings.UPDATE_URL + self.filename)
                f = open(self.tempfilename, 'w+b')
                total_size = float(response.info().getheader('Content-Length').strip())
                bytes_so_far = 0
                chunk_size = 8192
                while self.run:
                    chunk = response.read(chunk_size)
                    bytes_so_far += len(chunk)
                    if not chunk:
                        break

                    f.write(chunk)
                    self.update(float(bytes_so_far) / total_size, "Downloading new version...")
                f.close()

                succes = False
                if self.run: # be sure download wasn't cancelled
                    # Delete files, if a current zip file is present:
                    if os.path.exists(self.currfilename):
                        logger.info("Removing old files...")
                        self.update(0.0, "Removing old files...")
                        zfile = ZipFile(self.currfilename)
                        names = zfile.namelist()
                        n = len(names)
                        dirs = []
                        for i, name in enumerate(names):
                            if not name.startswith("data/"): # keep old data
                                if os.path.isdir(name):
                                    dirs.append(name)
                                else:
                                    try: os.remove(name)
                                    except: pass
                                # also remove compiled files (if they exist):
                                if name.endswith(".py"):
                                    try: os.remove("%sc" % name)
                                    except: pass
                                self.update(float(i) / float(n), "Removing old files...")
                        n = len(dirs)
                        for i, name in enumerate(dirs):
                            try: os.rmdir(name)
                            except: pass
                            self.update(float(i) / float(n), "Removing old directories...")

                    logger.info("Installing new files...")
                    self.update(0.0, "Installing new files...")

                    zfile = ZipFile(self.tempfilename)
                    zfile.extractall()
                    zfile.close()

                    logger.info("Update done.")
                    self.update(1.0, "Done.")
                    succes = True

                self.run = False
                self.update(0.0, "Cleaning...")
                logger.info("Removing temporary files...")
                os.rename(self.tempfilename, self.currfilename)

                self.update(1.0, "Done.")

                if succes: # relaunch process
                    args = sys.argv[:]
                    logger.info("Re-spawning %s" % " ".join(args))
                    args.insert(0, sys.executable)
                    if sys.platform == 'win32':
                        args = ['"%s"' % arg for arg in args]
                    os.execv(sys.executable, args)
                    gtk.main_quit()
                    sys.exit(0)
            except urllib2.URLError:
                logger.info("Updater failed for url: %s" % settings.UPDATE_URL + self.filename)
            else:
                raise # re-raise uncaught errors
            self.bar.grab_remove()

        self.destroy()
        gtk.main_quit()

    def update(self, fraction, label):
        self.bar.set_fraction(fraction)
        self.bar.set_text(label)
        while gtk.events_pending():
            gtk.main_iteration_do(False)

    def cancel(self, *args, **kwargs):
        if self.run:
            self.run = False
        return False

    pass # end of class

def update():
    try:
        response = urllib2.urlopen(settings.UPDATE_URL + 'upgrades', timeout=5)
        html = response.read()
        updates = map(lambda s: s.split(), html.split("\n"))
        last_version, filename = updates[0][0], updates[0][1]
        if mycmp(last_version, settings.VERSION) >= 1:
            logger.info("New version available (%s), now at (%s)" % (last_version, settings.VERSION))
            dialog = Updater(updates)
            dialog.show_all()
            gtk.main()
        else:
            logger.info("Most recent version installed (%s), remote is (%s)" % (settings.VERSION, last_version))
    except:
        logger.critical("An error occurred while trying to access the update server, current version is (%s)" % (settings.VERSION,))


