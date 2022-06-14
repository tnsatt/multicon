# multicon

Download url with multiple connection

# Requirement

pip install requests

# How to use
```
from multicon.downloader.multicon import MultiCon

url="https://abc.xyz/download"
dir="C:\\Downloads"
name=None # or name you want
m = MultiCon(url, dir=dir, name=name, max=8)
path = m.start()
```
# Demo

![image](https://i.imgur.com/udPWLKO.gif)
