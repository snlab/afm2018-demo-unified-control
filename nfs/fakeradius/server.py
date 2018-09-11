#!/usr/bin/env python3

from flask import Flask, request, g
from gevent.pywsgi import WSGIServer
import urllib.request
import threading


app = Flask("trident")


def send_to_controller(rip):
    ip="127.0.0.1"
    flow = "<%s>"%(rip.split(":")[-1])
    key = 'auth'
    value = 'Accept'
    url = 'http://%s:8181/api/snlab/trident_server/v1/tridentkv?flow=%s&key=%s&value=%s'%(ip, flow, key, value)
    response = urllib.request.urlopen(url)
    print(response.read().decode())   

@app.route('/verify')
def test():
    global trident
    ip = request.remote_addr
    name = request.args.get('name')
    password = request.args.get('password')
    if name=='user' and password=='rightpassword':
        threading.Thread(target=send_to_controller,args=(ip,)).start()
        return 'accept'
    else:
        return 'forbid'

http_server = WSGIServer(('', 8848), app)
http_server.serve_forever()
