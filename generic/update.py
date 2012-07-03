import settings

import gtk

import urllib2
import os
import sys
from os.path import basename
from urlparse import urlsplit
from zipfile import ZipFile
import re

import threading
import random, time

def mycmp(version1, version2):
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
    return cmp(normalize(version1), normalize(version2))

class Updater(gtk.Dialog):

    def __init__(self, filename, *args, **kwargs):
        gtk.Dialog.__init__(self, "Updater", None, 0, (gtk.STOCK_EXECUTE,  gtk.RESPONSE_APPLY, 
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
        self.filename = filename
        self.tempfilename = 'data/last_version.zip'
        
    def response(self, widget, response_id):
        if response_id != gtk.RESPONSE_APPLY:
            gtk.main_quit()
            self.run = False
        else:
            self.bar.grab_add()

            print "Running Updater"
            
            try:
                response = urllib2.urlopen(settings.UPDATE_URL+self.filename)
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
                if self.run: #be sure download wasn't cancelled
                    print "Installing new version..."
                    self.update(0.0, "Installing new version...")
                    
                    zfile = ZipFile(self.tempfilename)
                    zfile.extractall()
                    zfile.close()

                    print "Done."
                    self.update(1.0, "Done.")
                    succes = True

                self.run = False
                self.update(0.0, "Cleaning...")
                print "Removing temporary file"
                os.remove(self.tempfilename)
                self.update(1.0, "Done.")
                
                if succes: #relaunch process
                    args = sys.argv[:]
                    print "Re-spawning %s" % " ".join(args)
                    args.insert(0, sys.executable)
                    if sys.platform == 'win32':
                        args = ['"%s"' % arg for arg in args]                
                    os.execv(sys.executable, args)
                    gtk.main_quit()
                    sys.exit(0)
            except URLError:
                print "Updater failed for url: %s" % settings.UPDATE_URL+self.filename
            else:
                raise #re-raise uncaught errors
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

    pass #end of class

def update():
    try:
        response = urllib2.urlopen(settings.UPDATE_URL+'version', timeout=3)
        html = response.read()
        last_version, filename = html.split("\n")[:2]
        if mycmp(last_version, settings.VERSION) >= 1:
            print "New version available (%s), now at (%s)" % (last_version, settings.VERSION)
            dialog = Updater(filename)
            dialog.show_all()
            gtk.main()
        else:
            print "Most recent version installed (%s), remote is (%s)" % (settings.VERSION, last_version)
    except:
        print "An error occured while trying to acces the update server, current version is (%s)" % (settings.VERSION,)
        



"""class Updater(threading.Thread):

    def __init__(self, bar, label, filename):
        threading.Thread.__init__(self)
        self.bar = bar
        self.label = label
        self.filename = filename
	
    def run(self):
        print "Running Updater"
        self.update_window(0.0, "Downloading new version...")

        response = urllib2.urlopen(settings.UPDATE_URL+self.filename)
        f = open('data/last_version.zip', 'wb')
        f.write(response.read())
        f.close()

        self.update_window(0.5, "Installing new version...")
        self.update_window(1.0, "Ready!")
	
        #gtk.threads_enter()	
        #gtk.main_quit()
        #gtk.threads_leave()
        
    def update_window(self, fraction, label):
        gtk.threads_enter()
        self.bar.set_fraction(fraction)
        self.label.set_text(label)
        while gtk.events_pending():
            gtk.main_iteration(False)
        gtk.threads_leave()
			
def update():
    response = urllib2.urlopen(settings.UPDATE_URL+'version')
    html = response.read()
    last_version, filename = html.split("\n")[:2]
    current_version = "0.3.3"
    if mycmp(last_version, current_version) >= 1:
        print "New version available"
        
        dialog = gtk.MessageDialog(
                    flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                    type=gtk.MESSAGE_WARNING,
                    buttons=gtk.BUTTONS_YES_NO,
                    message_format="A new version of PyXRD is available.\nDo you want to update now?")       
        response = dialog.run()
        dialog.destroy()
        if response in (gtk.RESPONSE_ACCEPT, gtk.RESPONSE_YES, gtk.RESPONSE_APPLY, gtk.RESPONSE_OK):
        
            #Window with progressbar & label
            window = gtk.Window()
            vbox = gtk.VBox()
            bar = gtk.ProgressBar()
            label = gtk.Label("")
            vbox.pack_start(bar)
            vbox.pack_start(label)
            window.add(vbox)
                       
            window.show_all()
    
            progress = dialog.get_data("progress")
         progress.set_text("Calculating....")
         progress.grab_add()

         while i < n:
             sleep(0.005)
             progress.set_fraction(i/(n - 1.0))
             i += 1

             while gtk.events_pending():
                 gtk.main_iteration_do(False)

         progress.set_fraction(0.0)
         progress.set_text("")
         progress.grab_remove()
    
            gtk.main()
        else:
            pass"""
