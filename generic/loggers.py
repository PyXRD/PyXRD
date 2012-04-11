import sys
import os
import settings
import logging

class PyXRDLogger(): 
    def __init__(self, filename): 
        self.saveout = sys.stdout
        self.saveerr = sys.stderr

        sys.stdout = self 
        sys.stderr = self
        self.logfile = file(filename, 'w') 
        
        self.logger = logging.getLogger("gtkmvc")
        hdlr = logging.StreamHandler(self)
        self.logger.addHandler(hdlr)
        #if settings.DEBUG:
        #    self.logger.setLevel(logging.DEBUG)
        
    def write(self, text): 
        self.saveout.write(text) 
        self.logfile.write(text) 
        self.logfile.flush()
        os.fsync(self.logfile.fileno())
        
    def close(self): 
        self.saveout.close() 
        self.logfile.flush()
        os.fsync(self.logfile.fileno())
        self.logfile.close()
    
    def restore(self):
        sys.stdout = self.saveout
        sys.stderr = self.saveerr
    
    @classmethod
    def start_logging(cls):
        cls.writer = PyXRDLogger(settings.LOG_FILENAME) 

    @classmethod
    def stop_logging(cls):
        cls.writer.restore()
