import threading
import time
import sys
import ctypes
class pthread(threading.Thread):
    def __init__(self, func, args) -> None:
        super().__init__()
        self.func=func
        self.args=args
    def run(self):
        self.func(*self.args)
    def get_id(self):
 
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
  
    def raise_exception(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        
class Task:
    def __init__(self, func, args, thread=1, delay=0.1, daemon=True) -> None:
        self.connect=0
        self.count=0
        self.stop=False
        self.end=False
        self.thread=thread
        self.func=func
        self.args=args
        self.delay=delay
        self.daemon=daemon
        self.lock=threading.Lock()
        self.connectLock=threading.Lock()
    def start(self):
        try:
            while(self.loop()):
                continue
            while not self.end:
                time.sleep(self.delay)
        except (KeyboardInterrupt, SystemExit) as e:
            self.stop=True
            print("KeyboardInterrupt: Exiting...")
            sys.exit()
    def startAsync(self):
        self.daemon=False
        while(self.loop()):
            continue
    def loop(self):
        if self.stop:
            if self.connect==0:
                self.end=True
            return False    
        if self.connect>=self.thread:
            return False
        with self.connectLock:
            self.connect+=1
            count=self.count
            self.count+=1
        try:
            t=threading.Thread(target=self.run, args=(count, ))
            t.daemon=True if self.daemon else False
            t.start()
            return True
        except (KeyboardInterrupt, SystemExit) as e:
            self.stop = True
            self.end = True
            raise e
    def run(self, count):
        if self.func(*self.args)==False:
            with self.connectLock:
                self.connect-=1
            self.stop=True
            if self.connect==0:
                self.end=True
            return
        with self.connectLock:
            self.connect-=1
        self.loop()