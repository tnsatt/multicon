import os, sys
from urllib import error, request
import ssl
try:
    import requests
except:
    requests=None
from ...utils.r import (check_file)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"

sslctx = ssl.create_default_context() 
sslctx.check_hostname = False
sslctx.verify_mode = ssl.CERT_NONE

def head(url, data=None, timeout=30, headers=None, params=None):
    try:
        res = getConnection(url, data=data, timeout=timeout, headers=headers, params=params)
        headers = res.headers
        res.close()
        return headers
    except Exception as e:
        return None
    
def initHeader(headers):
    if headers == None:
        headers = {}
    default_headers={
        "User-Agent" : USER_AGENT,
    }
    default_headers.update(headers)
    headers = default_headers
    return headers
def getConnection(url, timeout=30, headers=None, params=None):
    if requests: 
        headers = initHeader(headers)
        return requests.get(url, headers=headers, stream=True, timeout=timeout, params=params, verify=False)
    else:
        headers = initHeader(headers)
        con = request.Request(url, headers=headers)
        try:
            return request.urlopen(con, context=sslctx, timeout=timeout)
        except error.HTTPError as e:
            return e
def err(msg):
    print(msg, file=sys.stderr)
def splitname(path):
    name= os.path.basename(path)
    index=name.rfind(".")
    if index>=0:
        return name[0: index], name[index+1: ]
    return name, ""
def castext(ext):
    castarr = {
        "mp4": ["m3u", "m3u8"],
        "ts": ["mp2t"]
    }
    lower = ext.lower()
    for i in castarr:
        for k in castarr[i]:
            if k == lower:
                return i
    return ext
def makedir(path, lock=None):
    if lock:
        with lock:
            path = check_file(path)
            os.makedirs(path, 777, True)
            return path
    else:
        path = check_file(path)
        os.makedirs(path, 777, True)
        return path
def makefile(path, lock=None):
    os.makedirs(os.path.dirname(path), 777, True)
    if lock:
        with lock:
            path = check_file(path, None, prefix=" (", suffix=")")
            open(str(path), "a+").close()
            return path
    else:
        path = check_file(path, None, prefix=" (", suffix=")")
        open(str(path), "a+").close()
        return path