import os
import time
from .util import (USER_AGENT, makefile, makedir, castext, splitname,
                   getConnection, initHeader, err
                   )
from ...utils.r import (formatPath, parseFilename, isDirectURL, getSize, getFilename, uri_decode, cookie_encode, formatFilename)
TMPNAME =".temp"

class Res:
    def __init__(self, headers, type=None, content=None, html=None):
        self.headers=headers
        self.type = type
        self.content=content
        self.html=html
class DownloadItem:
    def __init__(self, url=None, path=None, dir=None, name=None):
        self.url = url
        self.title = None
        self.path = path
        self.realpath = None
        self.dir = dir
        self.mode = -1
        self.name = name
        self.link = None
        self.status = ""
        self.realtitle = None
        self.targetPath = None
        self.referer = None
        self.headers = {}
        self.cookie = []
        self.done = False
        self.success = False
        self.index = -1
        self.size = 0
        self.currentSize = 0
        self.timeout=False
        self.isDirect = False
        self.ytc = False
        self.torrent=False
        self.nocheck = False
        self.m3u8 = False
        self.embed = False
        self.forceDirect = False
        self.forceOrder = None
        self.conn = None
        self.prependOrder = []
        self.thread = None
        self.timestart = 0
        self.time = 0
        self.timeend = 0
        self.stop = False
        self.retry = 0
        self.newPath = None
        self.parent = None
        self.newSize = 0
        self.currentRetry = 0
        self.percent = None
        self.retryLock = None
        self.processFile = None
        self.parentTask = None
        self.successPrint = 0
        self.temp=None
        self.username=None
        self.password=None
        self.debug = False
        self.res=None
        self.progress=None
        self.speedArr= []
        self.speed = 0
        self.calcTime=0
        self.range=[]
        self.resumable =False
        self.hash={}
        self.proxy=None
        self.auth = None
        self.thread=False
        self._interval = 0.5
        self._max = 0
        self.originname = None
        self.autoext=False
    @property
    def max(self):
        return self._max
    @max.setter
    def max(self, val):
        try:
            self._max = int(val)
        except:pass
    @property
    def interval(self):
        return self._interval
    @interval.setter
    def interval(self, val):
        try:
            self._interval = int(val)
        except:pass
    def getHeaders(self):
        h = self.headers
        if self.referer:
            h['referer'] =self.referer
        if self.cookie:
            if not isinstance(self.cookie, str):
                self.cookie = cookie_encode(self.cookie)
            h["Cookie"] = self.cookie
        return h
    def cookie_merge(self, cookie):
        if not isinstance(self.cookie, str):
            self.cookie = cookie_encode(self.cookie)
        if not isinstance(cookie, str):
            cookie = cookie_encode(cookie)
        self.cookie += "; "+cookie
    def tempdir(self, name):
        if not name: name="temp"
        if self.temp:
            temp = makedir(self.temp+"/"+TMPNAME+"/"+name)
            return temp
        if self.parentTask:
            temp =self.parentTask.tempdir(name)
            if temp: return temp
        if self.path:
            dir= os.path.dirname(self.path)
        else:
            dir=self.dir
        temp = makedir(dir+"/"+TMPNAME+"/"+name)
        return temp
    

class DownloadEvent:
    def start(self, item, task):
        pass

    def done(self, item, task):
        pass

def urlGuessExt(url):
    arr = {
        "image": [
            ["jpg", "jpeg", "gif"],
            ["image", "img"],
        ],
        "video": [
            ["mp4", "mkv", "ts"],
            ["video"],
        ],
        "audio": [
            ["mp3"],
            ["audio", "music"],
        ],
    }
    for i in arr:
        for j in arr[i][0]:
            if "." + j in url:
                return j
    for i in arr:
        for j in arr[i][1]:
            if j in url:
                return arr[i][0][0]
    return None
def defaultExt(url, defExt="html"):
    data = {
        'mp4': ["tiktok"]
    }
    list = key = item = None
    for key in data:
        list = data[key]
        for item in list:
            if item in url:
                return key
    ext = urlGuessExt(url)
    if ext:
        return ext
    return defExt
def parseName(url, name, ext):
    newName = parseFilename(url)
    dot = newName.rfind(".")
    if(dot >= 0):
        if not name:
            name = newName[0: dot]
        if(ext == None):
            ext = newName[dot+1:]
            if(ext == ""):
                ext = None
    else:
        if not name:
            name = newName
        if(ext == None):
            ext = defaultExt(url)
    return name, ext
def check(url, dir, name=None, item=None, overwrite=False, headers=None, lock=None):
    dir = formatPath(dir, "/")
    filename = None
    ext = None
    isDirect=False
    os.makedirs(dir, 777, True)
    if name:
        filename = name
        if not item.autoext:
            dot = filename.rfind(".")
            if(dot >= 0):
                ext = filename[dot+1:]
                if(ext == ""):
                    ext = None
                name = filename[0: dot]
            else:
                name = filename
    if((item == None or not item.nocheck) and (not name or ext == None or not item == None)):
        if not headers:
            headers = item.getHeaders()
            headers = initHeader(headers)
        req = getConnection(url, headers=headers, proxy=item.proxy, auth=item.auth)
        headers = req.headers
        if(headers != None):
            isDirect= isDirectURL(headers)
            type = headers['Content-Type'] if 'Content-Type' in headers else None
            if type and "torrent" in type:
                item.torrent = True
                return None, None
            if not name or ext == None or item.autoext:
                newName = getFilename(headers)
                if(newName != None):
                    n, e = splitname(newName)
                    if not name:
                        name = n
                    if(ext == None and e):
                        ext = e
                    # if item.autoext and e and e!=ext:
                    #     name +="."+ext
                    #     ext = e
                if not name or ext == None:
                    if item and item.link:
                        name, ext = parseName(item.link, name, ext)
                        if not name or ext == None:
                            name, ext = parseName(url, name, ext)
                    else:
                        name, ext = parseName(url, name, ext)
            if(item != None):
                item.size = getSize(headers, max=True)
                item.isDirect = isDirect
                res = Res(headers, type=type)
                if item.isDirect:
                    item.conn = req
                else:
                    if type and "html" in type:
                        res.html = (req.read() if hasattr(req, "read") else req.text)
                    req.close()
                item.res = res
                if item.isDirect and not item.m3u8 and item.size > 0:
                    item.timeend = time.time() + 60 + item.size/20000
                if headers.get("Accept-Ranges") != None:
                    item.resumable= True
        elif not name or ext == None:
            name, ext = parseName(url, name, ext)
    elif(not item == None and item.nocheck):
        name, ext = parseName(url, name, ext)
    if ext:
        ext = castext(ext)
    if item.autoext and name and ext and name.endswith("."+ext):
        name = name[0: -len(ext)-1]
    if name:
        name = formatFilename(name).strip()
    if item:
        item.name = (name if name else "") + \
            ("" if (ext == None or ext == "") else "."+ext)
        if item.isDirect:
            item.originname = item.name
    if not name:
        if(item != None):
            name = item.title
    if name == None:
        name = ""
    filename = name+("" if (ext == None or ext == "") else "."+ext)
    path = dir+"/"+filename
    # if overwrite:
    #     item.targetPath = path
    if isDirect and not overwrite:
        path = makefile(path, lock)
    else: pass
    filename = os.path.basename(path)
    if(not item == None):
        # item.realpath = item.path
        item.path = path
    return path, filename

def isResumable(headers):
    if not headers: return False
    accept = headers.get("Accept-Ranges")
    if accept != None and accept!="None":
        return True
    return False

def initHeaders(headers, item=None):
    if not headers:
        headers = {}
    default_headers={
        "User-Agent": USER_AGENT
    }
    default_headers.update(headers)
    headers = default_headers
    if(not item == None):
        j = item.url.rfind("#")
        model = {
            "ref": "referer",
            "header": "headers",
            "p": "proxy",
            "proxy": "proxy",
            "a": "auth",
            "auth": "auth",
            "s": "max",
            "i": "interval",
            "n": "name",
            "name": "name",
            "autoext": "autoext",
        }
        if j>=0:
            hash = item.url[j+1: ]
            item.url = item.url[0: j]
            hash = uri_decode(hash)
            if hash:
                item.hash = hash
                for k in model:
                    if k in hash:
                        setattr(item, model[k], hash[k] if len(hash[k])>1 else hash[k][0])
        if(not item.referer == None):
            headers["referer"] = item.referer
        if(not item.headers == None):
            for k in item.headers:
                headers[k] = item.headers[k]
    return headers