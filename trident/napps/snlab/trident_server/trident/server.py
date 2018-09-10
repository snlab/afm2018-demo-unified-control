from flask import Flask, request, g
from gevent.pywsgi import WSGIServer
from napps.snlab.trident_server.trident.tridentlib import TridentServer

app = Flask("trident")
trident = TridentServer()
from napps.snlab.trident_server.settings import CONFIG_LARK as lark

@app.route('/submit', methods=['POST'])
def submit_program():
    global trident
    program = request.data

    try:
        trident.submit(lark, program)
        return 'ok'
    except Exception as e:
        raise e

@app.route('/ast')
def read_program():
    global trident
    return trident.ctx.ast.pretty()

@app.route('/tridentkv')
def update_kv():
    global trident
    pkt = request.args.get('flow')
    sa_name = request.args.get('key')
    value = request.args.get('value')

    trident.update_sa(sa_name, pkt, value)

    return 'ok'

@app.route('/packetin')
def new_packet():
    global trident
    pkt = request.args.get('pkt')
    trident.new_pkt(pkt)

    return 'ok'

http_server = WSGIServer(('', 12321), app)
