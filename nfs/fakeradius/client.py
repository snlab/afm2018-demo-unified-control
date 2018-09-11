#!/usr/bin/env python3


import urllib.request
import sys

user = sys.argv[1]
pw = sys.argv[2]

# ip="127.0.0.1"
ip="10.0.0.3"

response = urllib.request.urlopen('http://%s:8848/verify?name=%s&password=%s'%(ip, user,pw))
print(response.read().decode())