
import os
from pathlib import Path
import re
import math
try:
    import psutil
except: psutil=None
def formatPath(path, sep="/"):
    return re.sub("[\\\/]+", sep, path).strip(sep)
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
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

class Opt:
    def __init__(self) -> None:
        self.opt = parse_args()
    def get(self, name, defVal=None):
        if not name in self.opt:
            return defVal
        return self.opt[name]
    
def walkfile(path, exclude=None, pattern=None, root=None, sep="/", issub=False):
    if not issub:
        if root: root = formatPath(root, sep)
        if exclude:
            for i in range(0, len(exclude)):
                exclude[i] = formatPath(exclude[i], sep).lower()
        if pattern:
            if isinstance(pattern, str):
                pattern = [pattern]
    if isinstance(path, list):
        for i in range(0, len(path)):
            item = path[i]
            todir= root
            if isinstance(item, str):
                if not os.path.exists(item): continue
                if os.path.isdir(item):
                    todir = (todir+sep if todir else "") + os.path.basename(item)
            yield from walkfile(item, exclude=exclude, pattern=pattern, root=todir, sep=sep, issub=True)
        return
    if isinstance(path, dict):
        for i in path:
            item = path[i]
            todir = root if not i else (i if not root else root+sep+i)
            # if isinstance(item, str):
            #     if not os.path.exists(item): continue
            #     if os.path.isdir(item):
            #         todir = (todir+sep if todir else "") + os.path.basename(item)
            yield from walkfile(item, exclude=exclude, pattern=pattern, root=todir, sep=sep, issub=True)
        return
    if not os.path.exists(path): return
    path = formatPath(path, sep)
    if exclude:
        if isExclude(path, exclude): return
    if os.path.isfile(path):
        if pattern and not isMatch(os.path.basename(path), pattern): return
        file =FileEntry(path)
        file.dir = (root+sep if root else "") + file.name
        yield file
    else:
        yield from walkdir(path, exclude=exclude, pattern=pattern, root=root, sep=sep)
def walkdir(path, exclude=None, pattern=None, root=None, sep="/"):
    lists = os.listdir(path)
    if len(lists)==0: return 0
    for name in lists:
        p = path+sep+name
        if exclude:
            if isExclude(p, exclude): continue
        if os.path.isdir(p):
            todir = (root+"/" if root else "") + name
            yield from walkdir(p, exclude=exclude, pattern=pattern, root=todir, sep=sep)
        else:
            if pattern and not isMatch(name, pattern): continue
            f =FileEntry(p)
            f.dir = (root+sep if root else "") + f.name
            yield f
            
def scanfile(path, exclude=None, pattern=None, root=None, sep="/", issub=False):
    if not issub:
        if exclude:
            for i in range(0, len(exclude)):
                exclude[i] = formatPath(exclude[i], sep).lower()
        if pattern:
            if isinstance(pattern, str):
                pattern = [pattern]
    if isinstance(path, list):
        for i in range(0, len(path)):
            item = path[i]
            todir= root
            if isinstance(item, str):
                if not os.path.exists(item): continue
                if os.path.isdir(item):
                    todir = (todir+sep if todir else "") + os.path.basename(item)
            yield from scanfile(item, exclude=exclude, pattern=pattern, root=todir, sep=sep, issub=True)
        return
    if isinstance(path, dict):
        for i in path:
            item = path[i]
            todir = root if not i else (i if not root else root+sep+i)
            # if isinstance(item, str):
            #     if not os.path.exists(item): continue
            #     if os.path.isdir(item):
            #         todir = (todir+sep if todir else "") + os.path.basename(item)
            yield from scanfile(item, exclude=exclude, pattern=pattern, root=todir, sep=sep, issub=True)
        return
    if not os.path.exists(path): return
    path = formatPath(path, sep)
    if exclude:
        if isExclude(path, exclude): return
    if os.path.isfile(path):
        if pattern and not isMatch(os.path.basename(path), pattern): return
        yield path
    else:
        yield from scandir(path, exclude=exclude, pattern=pattern, root=root, sep=sep)
def scandir(path, exclude=None, pattern=None, root=None, sep="/"):
    lists = os.listdir(path)
    if len(lists)==0: return 0
    for name in lists:
        p = path+sep+name
        if exclude:
            if isExclude(p, exclude): continue
        if os.path.isdir(p):
            todir = (root+sep if root else "") + name
            yield from scandir(p, exclude=exclude, pattern=pattern, root=todir, sep=sep)
        else:
            if pattern and not isMatch(name, pattern): continue
            yield p