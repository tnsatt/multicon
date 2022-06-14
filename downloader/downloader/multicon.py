import os, sys
import shutil
import threading
import math, time
import copy
from ..utils import pthread, bar
from .core.common import DownloadItem, check, isResumable
from .core.util import makedir, err, getConnection, initHeader
from ..utils.r import (cut, formatFileSize, getSize, parseFilename, getRange, formatTime)

class RangeException(Exception):
    pass
def log(index, msg, debug=True):
    if not debug: return
    err("["+str(index)+"] "+str(msg))
    err("")
class ChunkItem:
    def __init__(self, begin, chunk, index, debug=False) -> None:
        self.index = index
        self.begin = begin
        self.size = 0
        self.chunk = chunk
        self.end=-1
        self.success = False
        self.done = False
        self.path = None
        self.stop=False
        self.current=0
        self.progress=None
        self.skip=False
        self.timestart = 0
        self.timeend = 0
        self.is_stop=None
        self.isTilEnd = False
        self.timeout= 5
        self.parent=None
        self.req= None
        self.ref= None
        self.child=None
        self.debug=debug
        self.ondone = None
        self.thread = None
        self.beforeread = None
        self.headers=None
        self.res_headers=None
    def status(self):
        return "["+str(self.index)+"] ["+\
            formatFileSize(self.begin)+" - "+formatFileSize(self.begin+self.size)+" - "+formatFileSize(self.begin+self.chunk)+"]"
    def download(self, url, dir):
        headers = self.headers
        if not headers: headers = {}
        if(self.chunk > 0):
            if self.isTilEnd:
                headers['Range'] = "bytes=" + str(self.begin if self.begin>0 else 0)+"-"
            else:
                self.end = self.begin+self.chunk-1
                headers['Range'] = "bytes=" + \
                    str(self.begin)+"-"+str(self.end)
        path = dir+"/"+str(self.index)
        log(self.index, "download ["+formatFileSize(self.begin)+"-"+formatFileSize(self.begin+self.chunk)+"]", self.debug)
        self.path = path
        try:
            res = self.down(url, path, headers=headers, timeout=self.timeout)
            log(self.index, "success ["+formatFileSize(self.begin)+"-"+formatFileSize(self.begin+self.chunk)+"]", self.debug)
        except RangeException as e:
            self.done = True
            raise e
        except Exception as e:
            if self.ondone:
                self.ondone(self)
            self.done = True
            self.success=False
            log(self.index, self.status()+(" stop " if self.stop else " ")+str(e), self.debug)
            raise e
        if self.ondone:
            self.ondone(self)
        self.done = True
        self.success = True
        return path
    def checkRange(self, headers):
        range = getRange(headers)
        if range==None:
            if self.begin>0: raise RangeException("Unknown Begin Range "+str(self.begin))
            return
        if self.begin!=range[0]:
            raise RangeException("Wrong Begin Range "+str(self.begin)+" ["+headers.get("Content-Range")+"]")
        # if self.end>=0 and self.end!=range[1]: raise RangeException("Wrong End Range "+str(self.end)+" ["+headers.get("Content-Range")+"]")
    def down(self, url, path, headers=None, timeout=0):
        headers = initHeader(headers)
        con = getConnection(url, headers=headers, timeout=timeout)
        self.req=con
        if hasattr(con, "raise_for_status"):
            con.raise_for_status()
        headersize=None
        step=8192
        cur = 0
        try:
            with open(path, "wb") as f:
                self.timestart = time.time()
                self.timeend = self.timestart + (self.chunk / (1024*1024) * 1)
                if hasattr(con, "read"):
                    self.res_headers = con.info()
                    headersize=getSize(self.res_headers, defVal=-1)
                    self.checkRange(self.res_headers)
                    if self.beforeread: self.beforeread(self)
                    while chunk:=con.read(min(step, self.chunk-cur) if self.chunk>0 else step):
                        if self.stop: raise Exception("Stopped")
                        f.write(chunk)
                        cur+=len(chunk)
                        if self.chunk>0 and cur>=self.chunk:
                            if not self.is_stop or self.is_stop(self)==True:
                                self.current=self.chunk
                                if self.progress: self.progress(self)
                                break
                        self.current=cur
                        if self.progress: self.progress(self)
                else:
                    self.res_headers = con.headers
                    headersize=getSize(self.res_headers, defVal=-1)
                    self.checkRange(self.res_headers)
                    if self.beforeread: self.beforeread(self)
                    for chunk in con.iter_content(min(step, self.chunk-cur) if self.chunk>0 else step):
                        if self.stop: raise Exception("Stopped")
                        f.write(chunk)
                        cur+=len(chunk)
                        if self.chunk>0 and cur>=self.chunk:
                            if not self.is_stop or self.is_stop(self):
                                self.current=self.chunk
                                if self.progress: self.progress(self)
                                break
                        self.current=cur
                        if self.progress: self.progress(self)
            self.size = cur
        except Exception as e:
            con.close()
            self.size = cur
            raise e
        finally:
            con.close()
        if os.path.exists(path) and self.size>=self.chunk:
            return path
        raise Exception("Download Failed")
class MultiConn:
    def __init__(self, url, dir, name=None, item=None, headers=None, max=8, chunkSize=4194304, debug=False, tilEnd=True) -> None:
        self.url = url
        self.dir = dir
        self.name = name
        self.path = None
        self.max = max
        if not (self.max > 0):
            self.max = 8
        self.headers = headers
        self.chunkSize = chunkSize
        self.count = self.index = self.i = 0
        self.total = 0
        self.size = self.currentSize = 0
        self.done=0
        self.end = False
        self.stop = False
        self.tempDir = None
        self.file = None
        self.list = []
        self.arr = []
        self.speed=0
        self.speedArr= []
        self.item = item
        self.connect = 0
        self.connectLock = threading.Lock()
        self.countLock = threading.Lock()
        self.threadLock = threading.Lock()
        self.writeLock = threading.Lock()
        self.retryLock = threading.Lock()
        self.listLock = threading.Lock()
        self.debug = debug
        self.range=[]
        self.error = None
        self.isTilEnd = tilEnd
        self.timestart = 0
        self.waitthread=None
        self.threadList={}
        self.resumable = False
        self.isClean=False
    def check_next(self, item):
        self.resumable = isResumable(item.res_headers) or getRange(item.res_headers)!=None
        if not self.resumable:
            self.deb("No Next After "+str(item.index))
            return
        newitem  = self.addmore()
        if not newitem: return
        newitem.beforeread = self.check_next
        self.start_new()
        self.deb("Next "+newitem.status())
    def start3(self):
        chunkSize =  math.floor(self.size/self.max)
            # self.chunkSize = max(self.chunkSize, chunkSize)
        self.chunkSize=chunkSize

        self.total = math.ceil(self.item.size/self.chunkSize)
        start=0
        for i in range(0, self.total-1):
            start = i*self.chunkSize
            item = ChunkItem(start, self.chunkSize, i)
            self.list.append(item)
            self.arr.append(i)
        lastIndex = self.total-1
        start = lastIndex*self.chunkSize
        item = ChunkItem(start, min(
            self.chunkSize, self.size-start), lastIndex)
        self.list.append(item)
        self.arr.append(lastIndex)
        self.i =lastIndex+1
        for i in range(0, self.max):
            item = self.start_new()
            if item == False:
                break
    def start2(self):
        item = ChunkItem(0, self.size, 0)
        self.list.append(item)
        for i in range(0, self.max):
            item = self.start_new()
            if item == False:
                break
    def start1(self):
        '''start new chunk after prev headers'''
        item = ChunkItem(0, self.size, 0)
        self.list.append(item)
        item.beforeread = self.check_next
        self.start_new()
    def startAsync(self):
        if not self.item:
            self.item = DownloadItem(self.url)
        self.makedir()
        self.check()
        
        # self.size=0
        self.timestart = time.time()
        if self.size==0: #unknown size, start 1 connection
            item = ChunkItem(0, 0, 0)
            self.list.append(item)
            self.start_new()
        elif self.resumable:
            # self.start1()
            
            self.start2()
            
            # self.start3()
        else:
            self.start1()
    def start(self):
        self.startAsync()
        try:
            self.waitthread = pthread.pthread(self.wait, ())
            self.waitthread.start()
            self.waitthread.join()
            self.calc()
            self.progress(True)
            self.clean()
            if self.error:
                raise self.error
        except Exception as e:
            self.deb(e)
            raise e
        return self.path
    def wait(self):
        try:
            if not self.item.parentTask: print("\n\n\n", file=sys.stderr, end="")
            while not self.end:
                self.calc()
                self.progress()
                time.sleep(0.5)
            self.calc()
            self.progress(True)
            self.clean()
        except Exception as e:
            # traceback.print_exc()
            self.calc()
            self.progress(True)
            self.clean()
            raise e
        
    def calc(self):
        currentSize=0
        for item in self.list:
            if item.stop: continue
            if item.done:
                if item.success:
                    currentSize+= min(item.size, item.chunk) if item.chunk>0 else item.size
                else:
                    currentSize+= min(item.size, item.chunk) if item.chunk>0 else item.size
            else:
                currentSize+= min(item.current, item.chunk) if item.chunk>0 else item.current
        self.currentSize=currentSize
        self.item.currentSize = currentSize
        self.calcSpeed(currentSize)

    def calcSpeed(self, currentSize):
        self.speedArr.append([currentSize, time.time()])
        l=len(self.speedArr)
        if l<2: return
        if(l>10): 
            self.speedArr.pop(0)
            l-=1
        t= self.speedArr[l-1][1]-self.speedArr[0][1]
        if t<=0: return
        self.speed = (self.speedArr[l-1][0]-self.speedArr[0][0])/ t
    def status(self, done=False):
        if self.item.parentTask: return
        input=[]
        arr=[]
        color=[]
        end = 0
        for item in self.list:
            if item.stop : continue #and not item.success
            # if item.begin>end:
            input.append([item.begin, 'white', 1])
            end =item.begin+item.current
            input.append([end, 'cyan', 0])
            # input.append([item.begin+item.chunk, 'white', 1])
        # input.sort(key=self.sort)
        input = sorted(input, key=lambda e: (e[0], e[2]))
        for item in input:
            arr.append(item[0])
            color.append(item[1])
        arr.append(self.size)
        color.append("white")
        # self.deb(arr)
        # self.deb(color)
        # self.deb("")
        text=formatFileSize(self.currentSize)+"/"+formatFileSize(self.size)
        eta=-1
        if not done and self.speed>0 and self.size>0:
            eta =(self.size - self.currentSize) / self.speed
        prefix=bar.up+bar.clearln+ bar.up+bar.clearln+ bar.up+bar.clearln
        if self.debug: prefix=""
        err(prefix+
            bar.barn(arr, 100, color, text=formatFileSize(self.speed)+"/s ~ "+str(self.connect))+"\n"
            +bar.barn([self.currentSize, self.size], 100, ["green", "white"], text
                      +(" ("+str(round(self.currentSize/self.size*100, 2))+"%)" if self.size>0 else ""))+"\n"
            +formatTime() +" ~ "
            +text+(" "+formatTime(time.time()-self.timestart) if done else (" ETA "+ formatTime(eta) if eta>=0 else ""))
            +" "+cut(self.name, 30) 
        )
    def is_stop(self, item):
        begin = item.begin+item.chunk
        # if item.child and item.child.begin==begin and :
        #     self.stop_item(item.child)
        #     item.chunk+= item.child.chunk
        #     item.stop=False
        #     return False
        stop = True
        with self.retryLock:
            for child in self.list:
                if child.stop or child.skip: continue
                if begin == child.begin: # or (begin < child.begin)
                    if child.success:
                        return True
                    if child.current==0:
                        if not child.done:
                            self.stop_item(child)
                        chunk =item.chunk
                        item.chunk+= child.chunk
                        self.deb(child.status()+" stop chunk")
                        self.deb("["+str(item.index)+"] "+" new chunk ["+formatFileSize(chunk)+"-"+formatFileSize(item.chunk)+"]\n\n")
                        stop=False
                        self.start_new()
                        return False
                    self.deb(child.status()+" no need bu")
                    return True
                # elif item.begin<=child.begin and begin>=child.begin+child.chunk:
                #     self.stop_item(child)
                #     try:
                #         child.req.close()
                #     except:pass
            return stop
    def addmore(self, inwait=False):
        if not self.resumable: return None
        # s = 1*1024*1024
        s = 1 * 1024
        with self.retryLock:
            if inwait:
                if self.connect >= self.max: return None
            else:
                if self.connect > self.max:
                    return None
            l = len(self.list)
            arr= []
            lists=[]
            for i in range(0, l):
                item=self.list[i]
                if item.success or item.skip or item.stop:
                    continue
                c=item.chunk - item.current
                if self.connect > 1 and c<s and not item.done:
                    arr.append(item)
                    continue
                lists.append(item)
            self.deb("Lists "+str(len(lists)))
            if len(lists)>0:
                lists = sorted(lists, key=lambda e: (e.current- e.chunk))
                for item in lists:
                    multi = False
                    if item.done:
                        if item.size==0:
                            begin = item.begin
                        else:
                            begin = item.begin+item.size
                        item.skip =True
                    # elif self.connect<=1 and (item.chunk - item.current<s):
                    #     begin = item.begin+item.size
                    #     multi=True
                    else:
                        begin = item.begin+item.current + math.floor(c/2)
                    chunk = item.chunk + item.begin - begin
                    if chunk<=0: continue
                    if not multi: item.chunk = begin - item.begin
                    down = self.copyItem(item, begin, chunk)
                    self.deb(down.status()+" from "+item.status()+"\n")
                    l+=1
                    return down
            # for item in arr:
            #     if not item.stop and item.current==0 and (time.time() - item.timestart >= 10):
            #         self.copyItem(item, item.begin, item.chunk)
            #         self.stop_item(item)
            #         with self.connectLock:
            #             self.connect-=1
            #         return True
            # if self.connect <=1:
            #     for item in arr:
            #         if not item.stop and item.current==0:
            #             self.copyItem(item, item.begin, item.chunk)
            #             self.stop_item(item)
            #             with self.connectLock:
            #                 self.connect-=1
            #             return True
        return None
    def copyItem(self, item, begin, chunk):
        down = ChunkItem(begin, chunk, len(self.list))
        down.ref = item
        item.child = down
        self.list.append(down)
        return down
    def start_item(self, index):
        with self.connectLock:
            self.connect+=1
        with self.listLock:
            if self.count >= len(self.list):
                if not self.addmore():
                    self.stop_one()
                    return
            if self.count >= len(self.list):
                self.stop_one()
                return
        i = 0
        with self.countLock:
            i = self.count
            self.count += 1
        item = self.list[i]
        item.is_stop = self.is_stop
        item.debug = self.debug
        item.ondone = self.writeFile
        item.isTilEnd= self.isTilEnd
        item.thread= self.threadList[index]
        item.headers = copy.copy(self.headers)
        try:
            path = item.download(self.url, self.tempDir)
            if item.stop:
                return
        except RangeException as e:
            self.err(e)
            self.resumable = False
        except Exception as e:
            self.err(e)
            if item.stop:
                return
            self.retry(item)
        self.done += 1
        with self.connectLock:
            self.connect-=1
        self.deb("more "+("success" if item.success else "failed")+" "+item.status())
        self.start_new()

    def retry(self, item):
        if item.stop: return
        with self.retryLock:
            i = len(self.list)
            begin = item.begin+item.size
            chunk = item.chunk - item.size
            newitem = ChunkItem(begin, chunk, i)
            self.list.append(newitem)
            item.chunk = item.size
            self.deb(newitem.status()+" retry from "+item.status())
            
    def writeFile(self, item):
        if item.stop: return
        with self.writeLock:
            # size = min(item.chunk, item.size)
            size= item.size
            if not size>0: return
            self.file.seek(item.begin)
            with open(item.path, "rb") as f:
                while chunk:= f.read(8192):
                    l = len(chunk)
                    self.file.write(chunk)
    def start_new(self):
        with self.threadLock:
            i = self.index
            self.index += 1
        # t = threading.Thread(target=self.start_item, args=(i, ))
        t = pthread.pthread(self.start_item, (i, ))
        self.threadList[i] = t
        t.start()
    def check_end(self):
        if self.connect > 0:
            return
        self.end = True
        if self.waitthread:
            self.waitthread.raise_exception()
    def stop_item(self, item):
        item.stop=True
        try:
            item.req.close()
            item.req=None
        except:pass
        try:
            if item.thread:
                item.thread.raise_exception()
                self.deb("Raise "+item.status())
        except:pass
        with self.connectLock:
            self.connect -= 1
        self.deb("Stop "+item.status())
    def stop_one(self):
        self.stop = True
        with self.connectLock:
            self.connect -= 1
        self.check_end()
    def progress(self, done=False):
        if self.item.progress:
            self.item.progress(self.item)
        else:
            self.status(done)
    def err(self, msg):
        if self.debug:
            err(msg)
    def makedir(self):
        if not self.name:
            name = parseFilename(self.url)
        else: name=self.name
        os.makedirs(self.dir, 777, True)
        self.tempDir = makedir(self.dir+"/"+name+"_temp")
    def check(self):
        p, fn = check(self.url, self.dir, self.name, self.item)
        self.path = self.item.path
        self.size = self.item.size
        self.resumable= self.item.resumable
        self.name = fn
        self.file = open(self.path, "wb+")
        if self.size > 0:
            self.file.seek(self.size-1)
            self.file.write(b"\0")
            self.file.flush()
    def sort(self, item):
        return item[0]
    def print(self, msg):
        if self.item.parentTask: return
        err(msg)
    def deb(self, msg):
        if self.debug:
            err(msg)
    def clean(self):
        if self.isClean: return
        self.isClean=True
        try:
            self.file.close()
        except:pass
        try:
           for item in self.list:
                try:
                    item.stop=True
                    item.req.close()
                except:pass
        except:pass
        try:
            shutil.rmtree(self.tempDir)
        except:pass