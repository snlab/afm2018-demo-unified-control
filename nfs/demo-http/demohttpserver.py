#!/usr/bin/env python3

import sys
from flask import stream_with_context, request, Response
from flask import Flask

app = Flask("demo-http-server")

def make_chunk(size):
    return 'a' * (size - 2) + '\r\n'

CHUNK_SIZE = 65536
CHUNK = make_chunk(CHUNK_SIZE)

MIME_MAPPING = {
            "mp4": "video/mp4",
            "mkv": "video/divx",
            "avi": "video/divx",
            "zip": "application/x-zip-compressed",
            "iso": "application/octet-stream",
            "txt": "text/plain",
            "html": "text/html"
        }

@app.route('/demo/<size>.<suffix>')
def supply(size, suffix):
    def generate(size):
        size = int(size)
        rnd = int(size / CHUNK_SIZE)
        for i in range(rnd):
            print('percentage: {:.2%}'.format(i * CHUNK_SIZE / size), file=sys.stderr)
            yield CHUNK
        yield CHUNK[rnd * CHUNK_SIZE - size:]
        print('percentage: {:.2%}'.format(1), file=sys.stderr)

    headers = {}
    headers['content-length'] = size
    headers['content-type'] = "{}; name={}.{}".format(MIME_MAPPING[suffix], size, suffix)
    headers['content-disposition'] = 'attachment; filename={}.{}'.format(size, suffix)
    response = Response(generate(size), mimetype=MIME_MAPPING[suffix], headers=headers)
    return response

if __name__ == '__main__':
    host = '127.0.0.1' if len(sys.argv) < 2 else sys.argv[1]
    port = 6666 if len(sys.argv) < 3 else int(sys.argv[2])
    CHUNK_SIZE = CHUNK_SIZE if len(sys.argv) < 4 else int(sys.argv[3])
    CHUNK = make_chunk(CHUNK_SIZE)
    app.run(host=host, port=port)
