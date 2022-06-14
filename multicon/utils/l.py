
import os
from pathlib import Path
import re
import math
try:
    import psutil
except: psutil=None
def formatPath(path):
    return re.sub("[\\\/]+", "/", path).strip("/")
def isExclude(path, exclude):
    if exclude==None or len(exclude)==0: return False
    path = path.lower()
    for i in exclude:
        if i.startswith("@"):
            item = i[1: ]
            if item in path: return True
        else:
            if path==i:
                return True
    return False
def isMatch(name, pattern):
    if pattern==None or len(pattern)==0: return True
    name = name.lower()
    for i in pattern:
        if i in name: return True
    return False
class FileEntry:
    def __init__(self, path=None):
        if path==None: return
        self.path = formatPath(path)  #os.path.realpath
        self.name = os.path.basename(self.path)
        self._is_dir = os.path.isdir(self.path)
        self._stat = lambda: os.stat(self.path)
        self.dir=None
    def is_dir(self):
        return self._is_dir
    def is_file(self):
        return not self._is_dir
    def stat(self):
        return self._stat
class Scanfile:
    def __init__(self, path, exclude=None, pattern=None, to=None, isSub=False) -> None:
        self.isSub=isSub
        self.to=to
        self.path=path
        self.data=[]
        self.sub=None
        self.index=0
        self.total=0
        self.parent=None
        self.readall=False
        if self.path==None:
            return
        if not isSub:
            if exclude:
                self.exclude=[]
                if isinstance(exclude, str):
                    self.exclude.append(formatPath(exclude).lower())
                else:
                    for i in exclude:
                        self.exclude.append(formatPath(i).lower())
            else: self.exclude=None
            if pattern:
                if isinstance(pattern, str):
                    self.pattern=[pattern]
                else:
                    self.pattern=pattern
            else: self.pattern=None
        else: 
            self.exclude=exclude
            self.pattern = pattern
        if isinstance(self.path, str):
            self.path = formatPath(self.path)
            if not isExclude(self.path, self.exclude):
                p = Path(self.path)
                if p.is_file():
                    if not self.pattern or isMatch(p.name, self.pattern):
                        item=FileEntry(self.path)
                        self.data=[item]
                else:
                    if isSub:
                        if self.to: self.to+="/"+os.path.basename(self.path)
                        else: self.to=os.path.basename(self.path)
                    l=os.listdir(self.path)
                    for i in l:
                        p=self.path+"/"+i
                        if self.pattern and os.path.isfile(p) and not isMatch(i, self.pattern):
                            continue
                        if not isExclude(p, self.exclude):
                            item=FileEntry(p)
                            self.data.append(item)
        else:
            for item in self.path:
                p=Path(item)
                if p.exists():
                    if self.pattern and p.is_file() and not isMatch(p.name, self.pattern):
                        continue
                    item = formatPath(item)
                    if not isExclude(item, self.exclude):
                        entry=FileEntry(item)
                        self.data.append(entry)
        self.total=len(self.data)
    def scanall(self):
        self.readall=True
        max=len(self.data)
        for j in range(max):
            item=self.data[j]
            if item.is_dir():
                scan=Scanfile(item.path, self.exclude, self.pattern, self.to, True)
                scan.scanall()
                for i in scan.data:
                    if i.is_file():
                        self.data.append(i)
                        self.total=self.total+1
            else:
                item.dir=self.to+"/"+item.name if self.to else item.name
    def next(self):
        if not self.sub==None:
            while True:
                i=self.sub.next()
                if not i==None:
                    return i
                else: 
                    self.sub=None
                    self.parent=None
                    break
        if self.index>=self.total:
            return None   
        index=self.index
        self.index=self.index+1
        item = self.data[index]
        # if isExclude(item.path, self.exclude): 
        #     return self.next()
        if item.is_file(): 
            if not self.readall: 
                item.dir=self.to+"/"+item.name if self.to else item.name
            return item
        if self.readall: 
            return self.next()
        self.sub=Scanfile(item.path, self.exclude, self.pattern, self.to, True)
        self.parent=item.path
        return self.next()
class FileFilter:
    def __init__(self, path) -> None:
        self.path=path
        self.scanfile=Scanfile(path)

class Scanpath:
    def __iter__(self):
        return self
    def __init__(self, path, exclude=None, isSub=False) -> None:
        self.isSub=isSub
        self.path=path
        self.data=[]
        self.sub=None
        self.index=0
        self.total=0
        if self.path==None:
            return
        if not isSub:
            if exclude:
                self.exclude=[]
                for i in exclude:
                    self.exclude.append(formatPath(i).lower())
            else: self.exclude=None
        else: self.exclude=exclude
        if isinstance(self.path, str):
            self.path = formatPath(self.path)
            if not isExclude(self.path, self.exclude):
                if Path(self.path).is_file():
                    self.data=[self.path]
                else:
                    l=os.listdir(self.path)
                    for i in l:
                        p=self.path+"/"+i
                        if not isExclude(p, self.exclude):
                            self.data.append(p)
        else:
            for item in self.path:
                if Path(item).exists() and not isExclude(item, self.exclude):
                    self.data.append(formatPath(item))
        self.total=len(self.data)
    def __next__(self):
        res = self.next()
        if res==None: raise StopIteration
        return res
    def next(self):
        if self.sub is not None:
            while True:
                i=self.sub.next()
                if i is not None:
                    return i
                else: 
                    self.sub=None
                    break
        if self.index>=self.total:
            return None   
        index=self.index
        self.index += 1
        item = self.data[index]
        # if isExclude(item, self.exclude):
        #     return self.next()
        if Path(item).is_file(): 
            return item
        self.sub=Scanpath(item, self.exclude, True)
        return self.next()

import sys
import fileinput

def cmd_input(arr, callback, maxrow=0, maxcol=0, maxlen=0, dir=0, title=None, end=""):
    text=("\n"+(title+"\n" if title else "")
    +cmd_options(arr, callback, maxrow, maxcol, maxlen, dir)
    +"\n"
    +(end if end else ""))
    print(text, end="", file=sys.stderr)
    for line in fileinput.FileInput(): # input()
        if line:
            line = line.strip()
            if line=="c": return False
            try:
                if not line.isnumeric(): raise Exception("")
                line=int(line)
                if not (line>=1 and line<=len(arr)): raise Exception("")
                if isinstance(arr, dict): return list(arr)[line-1]
                return line-1
                # if isinstance(arr, dict): return list(arr.values())[line-1]
                # return arr[line-1] 
            except Exception as e:
                pass
            print("No Option", file=sys.stderr)
            print(text, end="", file=sys.stderr)
def cmd_options(arr, callback, maxrow=0, maxcol=0, maxlen=0, dir=0):
    rows=[]
    max=[]
    i=0
    for k in arr:
        if isinstance(arr, dict): item = arr[k]
        else: item=k
        if dir:
            if maxcol:
                c=i%maxcol
                r=int(i/maxcol)
            elif maxrow:
                maxcol=math.ceil(len(arr)/maxrow)
                c=i%maxcol
                r=int(i/maxcol)
            else:
                c=i
                r=0
        else:
            if maxrow:
                r=i%maxrow
                c=int(i/maxrow)
            elif maxcol:
                maxrow=math.ceil(len(arr)/maxcol)
                r=i%maxrow
                c=int(i/maxrow)
            else:
                r=i
                c=0
        if not (r < len(rows)): 
            for j in range(r-len(rows)+1):
                rows.append([])
        t=str(i+1) +"/ "+(callback(item, i) if callback else str(item))
        rows[r].append(t)
        if not (c in max):
            for j in range(c-len(max)+1):
                max.append(0)
        if maxlen: max[c]=maxlen
        else:
            if c < len(max):
                if(len(t)>max[c]): max[c]=len(t)
            else: max[c]=len(t)
        i+=1
    template=[]
    for item in rows:
        for i, v in enumerate(item):
            item[i]=slim(v, max[i])
        template.append(" ".join(item))
    return "\n".join(template)
def slim(text, max=0):
    if(not (max>0)): return text
    strlen=len(text)
    if strlen == max:
        return text
    if strlen < max:
        for i in range(strlen, max):
            text+=" "
        return text
    return text[0: max-3]+"..."
def mem():
    #pip install psutil
    if not psutil: return 0
    # psutil=__import__('psutil', globals(), locals()) 
    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    except:
        return 0