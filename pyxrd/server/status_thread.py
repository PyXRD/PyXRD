import threading
import time

class StatusThread(threading.Thread):
    
    def __init__(self, interval, provider):
        """
            @param interval: In seconds: how often to update the status.
        """
        assert(interval > 0.1)
        self.interval = interval
        self.stop_requested = threading.Event()
        self.provider = provider
        threading.Thread.__init__(self)

    def run(self):
        while not self.stop_requested.isSet():
            time.sleep(self.interval)
            self.provider._update_status(self.provider._get_status())
                
    def stop(self):
        self.stop_requested.set()
        self.join()

    pass #end of class