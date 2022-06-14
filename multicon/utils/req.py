import binascii
import os
from . import r

class FileChunk():
    def __init__(self, file, max=0, start=-1) -> None:
        if isinstance(file, str):
            file=open(file, "rb")
        self.file=file
        self.max= int(max)
        if start>=0:
            self.start=int(start)
            self.file.seek(self.start)
        else:
            self.start=self.file.tell()
        self.end= -1 if self.max<0 else self.start + self.max 
    def __iter__(self):
        return self    
    def __next__(self):
        res = self.readline()
        if not res: 
            raise StopIteration
        return res
    def readline(self):
        res = self.file.readline()
        return res
    @property
    def name(self):
        return self.file.name
    def seek(self, start, from_what=0):
        self.file.seek(start, from_what)
    def eof(self):
        size = os.path.getsize(self.file.name)
        return self.file.tell()>=size
    def tell(self):
        return self.file.tell()
    def read(self, n=-1):
        n=int(n)
        if self.end >= 0:
            if self.start>=self.end:
                return ""
            if n>0:
                if self.start+n>self.end:
                    n=self.end-self.start
            elif n<0: n=self.end-self.start
        res = self.file.read(n)
        if hasattr(self.file, "tell"):
            self.start=self.file.tell()
        else: self.start+=len(res)
        return res
class MultiPartForm:
    def encode_multipart_formdata(fields):
        boundary = binascii.hexlify(os.urandom(16)).decode('ascii')
        body = (
            "".join("--%s\r\n"
                    "Content-Disposition: form-data; name=\"%s\"\r\n"
                    "\r\n"
                    "%s\r\n" % (boundary, field, value)
                    for field, value in fields.items()) +
            "--%s--\r\n" % boundary
        )
        content_type = "multipart/form-data; boundary=%s" % boundary
        return body, content_type
    def __init__(self, files=None, data=None, headers=None) -> None:
        self.data=[]
        self.index=0
        self.total=0
        self.loaded=0
        if headers==None: headers={}
        self.headers=headers
        boundary = binascii.hexlify(os.urandom(16)).decode('ascii')
        totallen=0
        index=-1
        correctlen=True
        if data==None: data={}
        if files==None: files={}
        for i in data:
            item=data[i]
            if isinstance(item, bytes):
                index+=1
                text=(self.encode(("--%s\r\n"
                    "Content-Disposition: form-data; name=\"%s\"\r\n"
                    "\r\n") % (boundary, i))
                    + item + self.encode("\r\n"))
                self.data.append(text)
                totallen+=len(text)
            elif isinstance(item, str):
                index+=1
                text=self.encode(("--%s\r\n"
                    "Content-Disposition: form-data; name=\"%s\"\r\n"
                    "\r\n"
                    "%s\r\n") % (boundary, i, item))
                self.data.append(text)
                totallen+=len(text)
            elif isinstance(item, (list, tuple)):
                for j in item:
                    index+=1
                    text=self.encode(("--%s\r\n"
                        "Content-Disposition: form-data; name=\"%s\"\r\n"
                        "\r\n"
                        "%s\r\n") % (boundary, i+"[]", str(j)))
                    self.data.append(text)
                    totallen+=len(text)
            else:
                index+=1
                text=self.encode(("--%s\r\n"
                    "Content-Disposition: form-data; name=\"%s\"\r\n"
                    "\r\n"
                    "%s\r\n") % (boundary, i, str(item)))
                self.data.append(text)
                totallen+=len(text)
        for i in files:
            item=files[i]
            index+=2
            type="application/octet-stream"
            if isinstance(item, str):
                fp=open(item, "rb")
                fn=item
            elif isinstance(item, (tuple, list)):
                fp=item[1]
                fn=item[0]
                if(len(item)>2): type=item[2]
                # else: type = mimetypes.guess_type(fn)[0]
            else:
                fp=item
                try:
                    fn=item.name
                except: fn=None
                # type=mimetypes.guess_type(fn)[0]  
            text=self.encode(("--%s\r\n"
                "Content-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
                "Content-Type: %s\r\n"
                "\r\n") % (boundary, i, os.path.basename(fn), type))
            self.data.append(text)
            if isinstance(fp, str):
                t = self.encode(fp)
                self.data.append(t)
                totallen+= len(t)
            elif isinstance(fp, bytes):
                self.data.append(fp)
                totallen+= len(fp)
            else:
                self.file=fp
                self.data.append(fp)
                if hasattr(fp, "name"):
                    totallen+= os.path.getsize(fp.name)
                else: correctlen=False
            self.data.append(b"\r\n")
            totallen+= len(text) + 2
        index+=1
        text=self.encode("--%s--\r\n" % boundary)
        self.data.append(text)
        totallen += len(text)
        self.total=len(self.data)
        self.headers['Content-Type'] = "multipart/form-data; boundary=%s" % boundary
        #block headers
            # self.headers['Accept-Encoding']='gzip' # cloudflare error decode
        if correctlen and totallen:
            self.headers['content-length']= str(totallen)
        pass
    def encode(self, text):
        return text.encode('utf-8')
    def readLen(self, text, max):
        if len(text)<=max:
            r=text
            text=None
        else:
            r=text[0, max]
            text=text[max]
        return r, text
    def close(self):
        for item in self.data:
            try:
                if(hasattr(item, "close")):
                    item.close()
            except:pass
    def read(self, max=0):
        unlimit=not(max > 0)
        text=b""
        # print(r.formatTime()+" "+self.file.name)
        while self.index<self.total and (unlimit or max>0):
            item=self.data[self.index]
            if isinstance(item, bytes):
                if unlimit:
                    text+=item
                    self.index+=1
                    self.loaded+=len(item)
                    continue
                l = len(item)
                if l==max:
                    text+=item
                    self.index+=1
                    self.loaded+=l
                    return text
                elif l<max:
                    text+=item
                    self.index+=1
                    max-=l
                    self.loaded+=l
                    continue
                else:
                    text +=item[0: max]
                    self.data[self.index]=item[max: ]
                    self.loaded+=max
                    return text
            else:
                if unlimit:
                    t=item.read()
                    text += t
                    self.index+=1
                    self.loaded+=len(t)
                    continue
                t = item.read(max)
                if t==None or t==b"":
                    self.index+=1
                    continue
                text += t
                l = len(t)
                max -= l
                self.loaded += l
                if max<=0: return text
                self.index+=1
                continue
        if text: 
            return text
        return None
class MultiRequestUpload:
    def __init__(self, url, file, headers=None, step=8192) -> None:
        self.url=url
        self.fp=file if not isinstance(file, str) else open(file, "rb")
        if headers==None: headers={}
        self.headers=headers
        self.step=step
        self.current=0
        self.prev=self.current
        self.size=os.path.getsize(self.fp.name)
        self.type='application/octet-stream'
    def tell(self):
        return self.current
    def seek(self, n):
        self.current=int(n)
        self.prev=self.current
        self.fp.seek(self.current)
    def upload(self, start=-1):
        if start>=0:
            self.current=start
            self.prev=self.current
            self.file.seek(self.current)
        if self.current>=self.size: return False
        filerange=FileChunk(self.fp, self.step)
        max = self.size if self.step<0 else self.current+self.step
        if max>self.size: max=self.size
        self.headers['Content-Type']=self.type
        # self.headers['Content-Length'] = str(max-self.current)
        if max>self.current:
            self.headers['Content-Range'] = 'bytes '+str(self.current)+'-'+str(max-1)+"/"+str(self.size)
        req=r.uploadReq(self.url, filerange, self.headers)
        self.prev=self.current
        self.current=filerange.tell()
        return req