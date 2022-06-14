import time as timelib
s= timelib.time()
import os, sys
from datetime import datetime
from pathlib import Path
import math
import json
import re
import random
import subprocess
import shutil
from pprint import pprint as pp
import mimetypes
from .req import MultiPartForm
from urllib import parse, error, request
import ssl
import base64
import uuid
import threading
from urllib.parse import urljoin
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
except: 
    AES= unpad=None
isRequests=os.environ.get("requests", "1")=="1"
if isRequests:
    # s=timelib.time()
    import requests
    # from requests.models import HTTPError
    requests.urllib3.disable_warnings(requests.urllib3.exceptions.InsecureRequestWarning)
# else:
#     from urllib import request, error
# print(timelib.time()-s, file=sys.stderr)
# print(sys.path, file=sys.stderr)

win = os.name == "nt"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
sslctx = ssl.create_default_context() 
sslctx.check_hostname = False
sslctx.verify_mode = ssl.CERT_NONE

clear = lambda: os.system('cls')
def import_libs(name):
    try:
        return __import__(name, globals(), locals()) 
    except:
        return None
def decrypt(data, key, iv=None):
    if isinstance(key, str):
        key = key.encode("ascii")
    if not iv:
        iv=data[0: 16]
        data = data[16: ]
    cipher = AES.new(key, AES.MODE_CBC, iv=iv) 
    original_data = unpad(cipher.decrypt(data), AES.block_size)
    return original_data
def decrypt_file(file, key, output, iv=None):
    if isinstance(key, str):
        key = key.encode("ascii")
    chunk_size=24*1024
    if isinstance(file, str):
        rp=open(file, 'rb')
    else: rp=file
    try:
        if not iv: iv = rp.read(16)
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        with open(output, "wb") as f:
            while (chunk:= rp.read(chunk_size))!=b"":
                f.write(cipher.decrypt(chunk))
    except Exception as e:
        rp.close()
        raise e
    rp.close()
    return True
def removedir(path):
    shutil.rmtree(path, ignore_errors=True)
def copy(path, to, mkd=True):
    if mkd:
        dir = os.path.dirname(to)
        if dir: mkdir(dir)
    shutil.copy(path, to)
def firstFileExists(arr):
    for item in arr:
        if os.path.exists(item):
            return item
    return None
def arg(key, val=None):
    if key == None:
        return
    if isinstance(key, str):
        sys.argv.append("-" + str(key) + "=" + str(val))
    else:
        for k in key:
            sys.argv.append("-" + str(k) + "=" + str(key[k]))
def parse_args():
    data = {}
    p = None
    for i in sys.argv:
        if i == "":
            continue
        try:
            if i[0] == "-":
                if not p == None:
                    p = None
                s = i.lstrip("-")
                e = s.find("=")
                if e >= 0:
                    k = s[0:e]
                    v = s[e + 1 :]
                else:
                    k = s
                    v = ""
                    p = k
                data[k] = v
            elif p != None:
                data[p] = i
                p = None
        except:
            pass
    return data
def exists(path):
    return os.path.exists(path)
def filePut(path, text, append=False, encode="utf-8"):
    try:
        with open(path, "a" if append else "w", encoding=encode) as f:
            f.write(text)
            return True
    except: pass
    return False
def fileGetHandle(path, encode="utf-8"):
    return open(path, "r", encoding=encode)
def fileGet(path, mode="r", encode="utf-8"):
    try:
        with open(path, mode, encoding=encode) as f:
            return f.read()
    except Exception as e: 
        # err(path)
        pass
    return None
def formatFileSize(bytes, full=False):
    if bytes >= 1048576000:
        return toFixed(bytes / 1073741824, 2) + (full and "GB" or "G")
    elif bytes >= 1024000:
        return toFixed(bytes / 1048576, 1) + (full and "MB" or "M")
    elif bytes >= 1024:
        return toFixed(bytes / 1024, 0) + (full and "KB" or "K")
    elif bytes >= 1000:
        return toFixed(bytes / 1024, 2) + (full and "KB" or "K")
    elif bytes > 0:
        return toFixed(bytes, 0) + "B"
    return "0B"
def toFixed(num, dec=0):
    return str(round(num, dec))
def parseInt(input, defVal=0):
    try:
        return int(input)
    except:
        return defVal
def parseFloat(input, defVal=0):
    try:
        return float(input)
    except:
        return defVal
def stack():
    traceback.print_exc()
def formatFilename(name, full=False):
    if full:
        name = replace('([^\\x20-~]+)|([\\\\/:?"<>|\\s\\%\\_\\r\\n]+)', "_", name)
    else:
        name = replace('([\\\\/:*?"<>|]+)', "", name)
        name = replace("[\\s\\r\\n]+", " ", name)
    return name.strip()
def filesize(path):
    try:
        return os.path.getsize(path)
    except Exception as e:
        return 0
def rmdir(path):
    if isinstance(path, str):
        file = Path(path)
    else:
        file = path
    if not file.exists():
        return False
    if file.is_file():
        file.unlink(True)
        return True
    file.rmdir()
    return True
def mkfile(path):
    if isinstance(path, str):
        file = Path(path)
    else:
        file = path
    try:
        if not file.exists():
            open(str(file), "a+").close()
            return True
        elif file.is_file(): return True
    except: pass
    return False
def mkdir(path):
    if isinstance(path, str):
        file = Path(path)
    else:
        file = path
    try:
        file.mkdir(777, True, True)
        return True
    except:
        return False
def in_array(text, arr):
    for item in arr:
        if item == text:
            return True
    return False
def match_array(text, arr):
    for item in arr:
        if item in text:
            return True
    return False
def scanfile(path, arr=None):
    if arr == None:
        arr = []
    path = re.sub("[\\\/]+", "/", path).strip("/")
    file = Path(path)
    if not file.exists():
        return arr
    if file.is_file():
        arr.append(path)
        return arr
    scan = os.listdir(path)
    for i in scan:
        f = path + "/" + i
        if os.path.isfile(f):
            arr.append(f)
        else:
            scandir(f, arr)
    return arr
def scandir(path, arr=None):
    if arr == None:
        arr = []
    scan = os.listdir(path)
    for i in scan:
        f = path + "/" + i
        if os.path.isfile(f):
            arr.append(f)
        else:
            scandir(f, arr)
    return arr
def rescanfile(path):
    path = re.sub("[\\\/]+", "/", path).strip("/")
    file = Path(path)
    if not file.exists():
        return
    if file.is_file():
        yield path
        return
    scan = os.listdir(path)
    for i in scan:
        f = path + "/" + i
        if os.path.isfile(f):
            yield f
        else:
            yield from rescandir(f)
def rescandir(path):
    scan = os.listdir(path)
    for i in scan:
        f = path + "/" + i
        if os.path.isfile(f):
            yield f
        else:
            yield from rescandir(f)
def microtime():
    return timelib.time() * 1000
def now():
    return int(timelib.time())
def ftime():
    return timelib.time()
def time():
    return int(timelib.time())
def gap():
    return formatTime(None)
def formatTime(pattern=None, num=None):
    if pattern == None:
        pattern = "%m/%d/%Y %H:%M:%S"
        if num == None:
            num = int(timelib.time())
        return str(datetime.utcfromtimestamp(num).strftime(pattern))
    if type(pattern) == str:
        if num == None:
            num = int(timelib.time())
        return str(datetime.utcfromtimestamp(num).strftime(pattern))
    return formatTime2(pattern)
def formatTime2(num):
    r = None
    if num < 60:
        r = str(math.floor(num)) + "s"
    elif num < 3600:
        m = math.floor(num / 60)
        s = math.floor(num)
        r = str(m) + "m:" + fixten(s - 60 * m) + "s"
    elif num < 86400:
        h = math.floor(num / 3600)
        m = math.floor(num / 60)
        s = math.floor(num)
        r = str(h) + "h:" + fixten(m - 60 * h) + "m:" + fixten(s - 60 * m) + "s"
    elif num < 86400000:
        d = math.floor(num / 86400)
        h = math.floor(num / 3600)
        m = math.floor(num / 60)
        s = math.floor(num)
        r = (
            str(d)
            + "d:"
            + fixten(h - 24 * d)
            + "h:"
            + fixten(m - 60 * h)
            + "m:"
            + fixten(s - 60 * m)
            + "s"
        )
    else:
        y = math.floor(num / 31536000)
        d = math.floor(num / 86400)
        h = math.floor(num / 3600)
        m = math.floor(num / 60)
        s = math.floor(num)
        r = (
            str(y)
            + "y:"
            + fixten(d - 365 * y)
            + str(d)
            + "d:"
            + fixten(h - 24 * d)
            + "h:"
            + fixten(m - 60 * h)
            + "m:"
            + fixten(s - 60 * m)
            + "s"
        )
    return r
def fixten(num):
    return "0" + str(num) if (num >= 0 and num < 10) else str(num)
def urlencode(str):
    return parse.quote(str)
def urldecode(str):
    return parse.unquote(str)
def urlencodePath(str):
    str = replace("%2F", "/", parse.quote(str))
    return str
def uri_encode(data):
    return parse.urlencode(data)
def uri_decode(data):
    return parse.parse_qs(data)
def json_encode(data):
    return json.dumps(data)
def json_decode(data):
    try:
        return json.loads(data)
    except:
        return None
def base64_encode(data):
    if data==None: return None
    if isinstance(data, str):
        message_bytes = data.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        return base64_bytes.decode('ascii')
    else:
        return base64.b64encode(data)
def base64_decode(data):
    if data==None: return None
    if isinstance(data, str):
        base64_bytes = data.encode('ascii')
        message_bytes = base64.b64decode(base64_bytes)
        return message_bytes.decode('ascii')
    else:
        return base64.b64decode(data)
def fixUri(uri):
    uri = replace("\\r\\n", "%0D%0A", uri)
    uri = replace("\\n", "%0A", uri)
    uri = replace("\\s", "%20", uri)
def merge(d1, d2):
    pass
def initHeader(headers):
    if headers == None:
        headers = {}
    default_headers={
        "User-Agent" : USER_AGENT,
        # "Accept-Language" : "en-US,en;q=0.8",
        # "Cache-Control" : "no-cache",
    }
    default_headers.update(headers)
    headers = default_headers
    return headers
def addHeaders(con):
    con.add_header("User-Agent", USER_AGENT)
    con.add_header("Accept-Language", "en-US,en;q=0.8")
    con.add_header("Cache-Control", "no-cache")
def post_json(url, data=None, headers=None):
    if headers == None:
        headers = {}
    headers["Content-Type"] = "application/json; charset=utf-8"
    headers["Accept"] = "application/json"
    if not data == None and not type(data) == str:
        data = json_encode(data)
    return json_decode(post(url, data=data, headers=headers))
def postData(data):
    if not data == None:
        t = type(data)
        if not t == str:
            data = parse.urlencode(data).encode("utf-8")
        else:
            data = data.encode("utf-8")
    return data
def onRes(con):
    con.content = con.read()
    try:
        con.text = con.content.decode("utf-8")
    except:
        try:
            con.text = con.content.decode("ascii")
        except:
            con.text = None
            pass
    con.status_code=con.getcode()
    return con
def getConnection(url, data=None, timeout=30, headers=None, files=None, params=None):
    if isRequests: 
        headers = initHeader(headers)
        if data or files:
            # data = postData(data)
            return requests.post(url, data=data, headers=headers, stream=True, 
            timeout=timeout, params=params, files=files, verify=False)
        else:
            return requests.get(url, headers=headers, stream=True, timeout=timeout, params=params, verify=False)
    else:
        headers = initHeader(headers)
        if params: url = newurl(url, params)
        if files:
            if isinstance(files, str):
                files={'file': (files, open(files,'rb'))}
            elif not isinstance(files, dict): 
                files={'file': (files.name, files)}
            formData=MultiPartForm(files, data, headers)
        else: formData= postData(data)
        con = request.Request(url, data=formData, headers=headers)
        try:
            return request.urlopen(con, context=sslctx, timeout=timeout)
        except error.HTTPError as e:
            return e
def req(url, data=None, timeout=30, headers=None, files=None, params=None, stream=False, method=None):
    if isRequests: return req2(url, params=params, data=data, timeout=timeout, headers=headers, files=files, stream=stream, method=method)
    headers = initHeader(headers)
    if params: url = newurl(url, params)
    if files:
        if isinstance(files, str):
            files={'file': (files, open(files,'rb'))}
        elif not isinstance(files, dict): 
            files={'file': (files.name, files)}
        formData=MultiPartForm(files, data, headers)
    else: formData= postData(data)
    con = request.Request(url, data=formData, headers=headers)
    try:
        with request.urlopen(con, context=sslctx, timeout=timeout) as con:
            return onRes(con)
    except error.HTTPError as e:
        return onRes(e)
def post(url, data=None, timeout=30, headers=None, params=None):
    try:
        res = req(url, data=data, timeout=timeout, headers=headers, params=params)
        return res.text
    except Exception as e:
        print(e)
        return None
def head(url, data=None, timeout=30, headers=None, params=None):
    try:
        res = getConnection(url, data=data, timeout=timeout, headers=headers, params=params)
        headers = res.headers
        res.close()
        return headers
    except Exception as e:
        return None
def get(url, params=None, timeout=30, headers=None, data=None):
    try:
        if not params: params=data
        res = req(url, data=None, timeout=timeout, headers=headers, params=params)
        return res.text
    except Exception as e:
        return None
def upload(url, file=None, data=None, headers=None, params=None):
    if isRequests: return upload2(url, file=file, data=data, headers=headers, params=params)
    return upload1(url, file=file, data=data, headers=headers, params=params)
def upload1(url, file=None, data=None, headers=None, params=None):
    # try:
    res = uploadRequest(url, file=file, data=data, headers=headers, params=params)
    return res.text
    # except Exception as e: 
    #     print(e)
    #     pass
    # return None
def uploadRequest(url, file=None, data=None, headers=None, params=None):
    headers = initHeader(headers)
    if data==None: data={}
    if file!=None:
        if isinstance(file, str):
            files={'file': (file, open(file,'rb'))}
        elif isinstance(file, dict): 
            files=file
        else: 
            files={'file': (file.name, file)}
        formData=MultiPartForm(files, data, headers)
    if params: url = newurl(url, params)
    con = request.Request(url, formData, headers=headers)
    try:
        with request.urlopen(con, context=sslctx) as con:
            formData.close()
            return onRes(con)
    except error.HTTPError as e:
        formData.close()
        return onRes(e)
    except:
        formData.close()
        raise
def uploadReq(url, file=None, headers=None, params=None, method="POST"):
    if isinstance(file, str):
        file=open(file, "rb")
    if isRequests: return req2(url, data=file, headers=headers, params=params)
    headers = initHeader(headers)
    if params: url=newurl(url, params)
    con = request.Request(url, file, headers=headers, method=method)
    try:
        with request.urlopen(con, context=sslctx) as con:
            return onRes(con)
    except error.HTTPError as e:
        return onRes(e)
def req2(url, data=None, headers=None, timeout=30, params=None, files=None, stream=False, method=None):
    headers = initHeader(headers)
    if data or files:
        # data = postData(data)
        if method==None: method="POST"
        with requests.request(method, url=url, data=data, headers=headers, stream=stream, 
        timeout=timeout, params=params, files=files, verify=False) as con:
            #con.raise_for_status()
            return con
    else:
        with requests.get(url, headers=headers, stream=stream, timeout=timeout, params=params, verify=False) as con:
            #con.raise_for_status()
            return con
def upload2(url, file=None, data=None, headers=None, params=None):
    try:
        headers = initHeader(headers)
        if file:
            if isinstance(file, str):
                files = {"file": open(file, "rb")}
            else: files=file
        else: files=None
        with requests.post(url, data=data, headers=headers, files=files, params=params, verify=False) as con:
            return con.text
    except Exception as e:
        return None
def upload_progress(url, file=None, data=None, headers=None, params=None, progress=None):
    try:
        headers = initHeader(headers)
        if file:
            if isinstance(file, str):
                # files = {"file": open(file, "rb")}
                
                file = {"file": (file, open(file, "rb"))}
                data  = MultiPartForm(file, data, headers, progress=progress)
                files=None
            else: 
                # files=file
                data  = MultiPartForm(file, data, headers, progress=progress)
                files=None
        else: files=None
        with requests.post(url, data=data, headers=headers, files=files, params=params, verify=False) as con:
            return con.text
    except Exception as e:
        return None
def post2(url, data=None, timeout=30, headers=None, params=None):
    try:
        headers = initHeader(headers)
        with requests.post(url, data=data, headers=headers, timeout=timeout, params=params, verify=False) as con:
            return con.text
    except Exception as e:
        return None
def head2(url, data=None, timeout=30, headers=None, params=None):
    try:
        with requests.get(url, data=data, timeout=timeout, headers=headers, params=params, stream=True, verify=False) as con:
            return con.headers
    except Exception as e:
        return None
def get2(url, params=None, timeout=30, headers=None):
    try:
        headers = initHeader(headers)
        with requests.get(url, timeout=timeout, params=params, headers=headers, verify=False) as con:
            return con.text
    except Exception as e:
        return None
def isDirectURL(headers, url=None):
    try:
        if isinstance(headers, str):
            url = headers
            headers = head(url)
            if headers == None:
                return None
        elif isinstance(headers, dict):
            a= {}
            for i in headers:
                a[i.lower()]= headers[i]
            headers=a
        elif headers == None:
            return None
        filename = None
        ext = None
        type = headers.get("content-disposition", None)
        if not type == None:
            match = re.match("^.*filename=\s*['\"]*([^'\"]+)['\"]*\s*$", type)
            if match:
                filename=match.group(1)
                dot = filename.rfind(".")
                if dot >= 0:
                    ext = filename[dot + 1 :]
        if ext == None:
            type = headers.get("content-type", None)
            if not type == None:
                ext = mimeToExt(type, True)
        if ext == None:
            return False
        return True
    except:
        return False
def getSize(headers, url=None, defVal=0, max=False):
    try:
        if headers == None:
            return defVal
        if isinstance(headers, str):
            url = headers
            headers = head(url)
            if headers == None:
                return defVal
        elif isinstance(headers, dict):
            a= {}
            for i in headers:
                a[i.lower()]= headers[i]
            headers=a
        if max and headers.get('Content-Range', None)!=None:
            try:
                m = findall("bytes(\=|\s+)(\d+)\-(\d+)\/(\d+)", headers.get('Content-Range'))
                if m:
                    return int(m[0][3])
            except:pass
        length = headers.get("content-length")
        if length==None: 
            return defVal
        return int(length.strip())
    except:
        return defVal
def getRange(headers):
    if headers and headers.get('Content-Range', None):
        try:
            m = re.findall("bytes(\=|\s+)(\d+)\-(\d+)\/(\d+)", headers.get('Content-Range'))
            if m:
                start = int(m[0][1])
                end = int(m[0][2])
                size = int(m[0][3])
                return start, end, size
        except:pass
    return None
def getRangeReq(headers):
    try:
        rang = headers['range']
        match = re.match("bytes=(\d+)-(\d+)", rang)
        if not match: return None
        return [int(match.group(1)), int(match.group(2))]
    except: return None
def getFilename(headers, url=None):
    try:
        if isinstance(headers, str):
            url = headers
            headers = head(url)
        elif isinstance(headers, dict):
            a= {}
            for i in headers:
                a[i.lower()]= headers[i]
            headers=a
        filename = None
        name = None
        ext = None
        if headers != None:
            try:
                type = headers.get("content-disposition", None)
                if not type == None:
                    match = re.match("^.*filename=\s*['\"]*([^'\"]+)['\"]*\s*$", type)
                    if match:
                        filename = match.group(1)
                        dot = filename.rfind(".")
                        if dot >= 0:
                            name = filename[0:dot]
                            ext = filename[dot + 1 :]
                        else:
                            name = filename
            except:
                pass
            if ext == None:
                try:
                    type = headers.get("content-type", None)
                    if not type == None:
                        ext = mimeToExt(type)
                except:
                    pass
        if (name == None or ext == None) and url != None:
            newName = parseFilename(url)
            dot = newName.rfind(".")
            if dot >= 0:
                if name == None:
                    name = newName[0:dot]
                if ext == None:
                    ext = newName[dot + 1 :]
            else:
                if name == None:
                    name = newName
        if name == None:
            if ext == None:
                return None
            return "." + ext
        if ext == None:
            return name
        return name + "." + ext
    except:
        return None
def mimeToExt(mime, media=False):
    if mime==None: return None
    ext=mimetypes.guess_extension(mime)
    if media:
        exclude=[
            ".html", ".htm"
        ]
    else:
        exclude=[]
    if ext!=None and not ext in exclude: return ext[1: ]
    arr = {
        "image": "jpg",
        "video": "mp4",
        "audio": "mp3",
    }
    cast={
        "mp2t":"ts",
    }
    for i in arr:
        if i+"/" in mime:
            try:
                e = mime[len(i) + 1 :].strip()
                if e:
                    if e in cast: return cast[e]
                    return e
            except:
                pass
            return arr[i]
    return None
def newurl(url, params):
    try:
        if type(params) == str:
            params = uri_decode(params)
        url_parts = list(parse.urlparse(url))
        query = dict(parse.parse_qsl(url_parts[4]))
        query.update(params)
        url_parts[4] = parse.urlencode(query)
        return parse.urlunparse(url_parts)
    except:
        return url
def trim(s):
    return s.strip()
def cmd(bin, args=[]):
    if bin:
        # cmd = "\""+bin+"\""
        cmd=bin
    else: cmd=""
    if args:
        for item in args:
            cmd+=" \""+(item)+"\""
    return cmd
def run(bin, args=[]):
    if bin:
        cmd = "\""+bin+"\""
    else: 
        cmd=""
    if args:
        for item in args:
            cmd+=" \""+(item)+"\""
    system(cmd)
def readstd(proc, buffer, output=None):
    try:
        while proc.poll() is None:
            res = buffer.readline()
            if res!=None and res!="":
                print(res, end="")
                if output!=None:
                    output.append(res)
        res = buffer.readlines()
        if res:
            print(''.join(res), end="")
            if output!=None:
                output.extend(res)
    except Exception as e:
        print(e)
def exec(cmd, debug=False, stdout=None, stderr=None, encoding="utf-8"):
    try: #using pipe and wait => hangs
        if debug:
            if stdout==None and stderr==None:
                proc = subprocess.Popen(cmd, encoding=encoding)
                proc.wait()
            else:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding=encoding)
                t =threading.Thread(target=readstd, args=(proc, proc.stdout, stdout))
                t.start()
                while proc.poll() is None:
                    err = proc.stderr.readline()
                    if err!=None and err!="":
                        print(err, end="", file=sys.stderr)
                        if stderr!=None:
                            stderr.append(err)
                err = proc.stderr.readlines()
                if err:
                    print(''.join(err), end="", file=sys.stderr)
                    if stderr!=None:
                        stderr.extend(err)
                # out = proc.stdout.readlines()
                # if out:
                #     print(''.join(out), end="")
                #     if stdout!=None:
                #         stdout.extend(out)
                # (out, err) = proc.communicate()
                # if out!=None:
                #     print(out, end="")
                #     if stdout!=None: stdout.append(out)
                # if err!=None:
                #     print(err, end="", file=sys.stderr)
                #     if stderr!=None: stderr.append(err)
            return True
        else:
            if stdout==None and stderr==None:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, encoding=encoding)
                proc.wait()
            else:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding=encoding)
                (out, err) = proc.communicate()
                if stdout!=None and out!=None:
                    stdout.append(out)
                if stderr!=None and err!=None:
                    stderr.append(err)
            return True
    except subprocess.CalledProcessError as e:
        if(debug): print(e, file=sys.stderr)
        return e.output
    except Exception as e:
        if(debug): print(e, file=sys.stderr)
        return None
def system(cmd):
    return os.system(cmd)
def rand(fr, to):
    return random.randint(fr, to)
def sleep(t):
    timelib.sleep(t)
def rename(a, b):
    os.rename(a, b)
def match(reg, str):
    return re.match(reg, str)
def replace(reg, to, str):
    return re.sub(reg, to, str)
def escape(str):
    return re.escape(str)
def search(regex, str):
    return re.search(regex, str)
def findall(regex, str):
    return re.findall(regex, str)
def matches(regex, str):
    list = []
    i = 0
    a = None
    s = re.search(regex, str)
    while True:
        try:
            a = s.group(i)
            list.append(a)
            i = i + 1
        except:
            break
    return list
def isURL(url):
    if not url: return False
    return re.match("^https?\\:\\/\\/.+", url)
def download(url, dir=None, name=None, headers=None, autorename=False, timeout=300):
    headers = initHeader(headers)
    con = getConnection(url, headers=headers, timeout=timeout)
    return downloadReq(con, url=url, dir=dir, name=name, autorename=autorename)
def downloadReq(con, url=None, dir=None, name=None, autorename=False, checkSize=True):
    if hasattr(con, "raise_for_status"):
        con.raise_for_status()
    else:
        pass
    if not name:
        if url==None: url=con.url
        filename=getFilename(con.headers, url)
        if not filename: 
            filename = formatFilename(parse.urlparse(url).hostname)
    else:
        filename = name
    if dir:
        os.makedirs(dir, 777, True)
        path = dir + "/" + filename
    else:
        path = filename
    file = Path(path)
    isTemp = True #file.exists()
    # if isTemp and autorename:
    #     path=check_file(path)
    #     file=Path(path)
    #     isTemp=False
    if isTemp:
        tempFile = check_file(str(file) + "."+str(uuid.uuid4())+".part")
    else:
        tempFile = path
    headersize=None
    step=8192
    try:
        with open(tempFile, "wb") as f:
            if hasattr(con, "read"):
                headersize=getSize(con.info(), defVal=-1)
                while chunk:=con.read(step):
                    f.write(chunk)
            else:
                headersize=getSize(con.headers, defVal=-1)
                for chunk in con.iter_content(step):
                    f.write(chunk)
    except Exception as e:
        try:
            os.unlink(tempFile)
        except:
            pass
        raise e
    finally:
        con.close()
    if not os.path.exists(tempFile):
        raise Exception("Download Failed: File Not Exists")
    if headersize==None:
        try:
            os.unlink(tempFile)
        except:
            pass
        raise Exception("Download Failed: Something Error")
    if checkSize:
        size=os.path.getsize(tempFile)
        if headersize!=-1 and size != headersize:
            try:
                os.unlink(tempFile)
            except:
                pass
            raise Exception("Download Failed: File Size Mismatch ("+str(size)+" - "+str(headersize)+")")
    else:
        if os.path.getsize(tempFile) == 0:
            try:
                os.unlink(tempFile)
            except:
                pass
            raise Exception("Download Failed: Empty File")
    if isTemp:
        if autorename:
            path = check_file(path)
        os.replace(tempFile, path)
        if not os.path.exists(path):
            try:
                os.unlink(tempFile)
            except:
                pass
            raise Exception("Download Failed: Rename File Failed")
    return path
def formatPath(path, sep="/", trim=False):
    if not path: return None
    path = re.sub("[\\\/]+", sep, path)
    if trim:
        path = re.sub("^[\\\/]+|[\\\/]+$", "", path)
    return path
def check_file(path, base=None, prefix=None, suffix=None, sep="/"):
    if path == None:
        path = ""
    path = formatPath(path, sep, True).strip()
    if path == ".":
        path = ""
    if base == None or base == "":
        base = ""
    else:
        base = formatPath(base, sep, True) + sep
    file = base + path
    isExists = os.path.exists(file)
    isEmpty = path == "" or path == "."
    if not isExists and not isEmpty:
        return path
    index = path.rfind("/")
    if index == -1:
        dir = ""
        name = path
    else:
        dir = path[0 : index + 1]
        name = path[index + 1 :]
    index = name.rfind(".")
    if index == -1:
        ext = ""
    else:
        ext = name[index:]
        if ext == ".":
            ext = ""
        name = name[0:index]
    newName = None
    count = 0
    basedir=base + dir
    if not basedir: basedir=os.getcwd()
    if isExists or (not isEmpty and basedir and os.path.exist(basedir)):
        arr = os.listdir(basedir)
    else:
        arr = []
    if isEmpty:
        if prefix == None:
            prefix = ""
        if suffix == None:
            suffix = ""
    else:
        if prefix == None:
            if suffix == None:
                prefix = " ("
                suffix = ")"
            else:
                prefix = "_"
        elif suffix == None:
            suffix = ""
    while True:
        count += 1
        newName = (name + prefix + str(count) + suffix + ext).strip()
        item = None
        ok = True
        for item in arr:
            if item == newName:
                ok = False
                break
        if ok:
            break
    return dir + newName
def strjoin(arr):
    if not isinstance(arr, list):
        return arr
    text = ""
    for i in arr:
        text += str(i)
    return text
def out(text):
    print(text, file=sys.stdout)
def errj(text):
    print(strjoin(text), file=sys.stderr)
def err(text):
    print(text, file=sys.stderr)
def errn(text):
    print(text, file=sys.stderr, end="")
def errln(text):
    print(text, file=sys.stderr)
def errl(text, t=0):
    print(text, file=sys.stderr)
    sleep(t)
def urlparse(url):
    return parse.urlparse(url)
def parseurl(url, base=None):
    if not base or not url or not isinstance(url, str) or not isinstance(base, str): return url
    return urljoin(base, url)
def parseFilename(url):
    a = parse.urlparse(url)
    return os.path.basename(a.path.rstrip("/"))
def count(str, sub):
    return len(str.split(sub)) - 1
def isRunPid(pid):
    try:
        pid = int(pid)
    except: return False
    if not(pid>=0): return False
    if win:
        output=[]
        exec('TASKLIST /NH /FO "CSV" /FI "PID eq ' + str(pid) + '"', stdout=output, stderr=output);
        if "INFO: No task" in "\n".join(output):
            return False
    else:
        if not os.path.exists("/proc/" + str(pid)):
            return False
    return True
def printUp(str, prev=0, isClear=False):
    if isClear:
        str = clearLn(prev, False) + str
    elif prev > 0:
        for i in range(0, prev):
            str = "\033[F" + str
    errn(str)
def clearLn(line, dir=False):
    newLine = ""
    goup = ""
    for i in range(0, line):
        newLine = newLine + "                                        \n"
        goup = goup + "\033[F"
    if dir:
        return newLine + goup
    else:
        return goup + newLine + goup
def parseInt(data, defVal=0):
    try:
        return int(data)
    except:
        return defVal
def parseBool(data, defVal=False):
    try:
        return bool(data)
    except:
        return defVal
def parseStr(data, defVal=None):
    if data==None: return defVal
    try:
        return str(data)
    except:
        return defVal
def getInt(data, key, defVal=0):
    if key in data and data[key] is not None:
        try:
            return int(data[key])
        except:
            pass
    return defVal
def getBool(data, key, defVal=False):
    if key in data and data[key] is not None:
        try:
            return bool(data[key])
        except:
            pass
    return defVal
def getStr(data, key, defVal=None):
    if key in data and data[key] is not None:
        try:
            return str(data[key])
        except:
            pass
    return defVal
def rand(fr, to):
    return math.floor(random.random()*(to-fr+1)+fr)
def slim(text, max=0):
    if(not (max>0)): return text
    strlen=len(text)
    if strlen == max:
        return text
    if strlen < max:
        return text + " "*(max-strlen)
    return text[0: max-3]+"..."
def cut(text, max=0):
    if(not (max>0)): return text
    strlen=len(text)
    if strlen == max:
        return text
    if strlen < max:
        return text + " "*(max-strlen)
    f=math.ceil((max-3)/2)
    return text[0: f]+"..."+text[strlen-max+f+3: ]
def cookie_encode(data):
    if isinstance(data, list):
        return "; ".join(data)
    elif isinstance(data, dict):
        cookie=""
        i=0
        for k in data:
            if data[k]==None: continue
            if i >0: 
                cookie+="; "
            cookie+=k+"="+str(data[k])
            i+=1
        return cookie
    return data
def cookie_decode(text):
    data={}
    if isinstance(text, str):
        arr=text.split(";")
    else: arr=text
    for item in arr:
        item=item.strip()
        if item=="": continue
        index=item.find("=")
        if index>=0:
            data[item[0: index].strip()]=item[index+1: ].strip()
        else: data[item]=None
    return data
def headers_decode(text):
    data={}
    if isinstance(text, str):
        arr=text.split("\n")
    else: arr=text
    for item in arr:
        item=item.strip()
        if item=="": continue
        index=item.find(":")
        if index>=0:
            data[item[0: index].strip()]=item[index+1: ].strip()
        else: data[item]=None
    return data

# print(timelib.time()-s)
# if __name__=="__main__":
#     print(sys.path)
#     sleep(100000)