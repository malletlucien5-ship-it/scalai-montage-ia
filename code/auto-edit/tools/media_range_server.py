#!/usr/bin/env python3
"""Servir uniquement les médias déclarés sur localhost, avec accès HTTP Range."""
import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', required=True, help='JSON {identifiant: chemin local}')
    p.add_argument('--port', type=int, default=18761)
    p.add_argument('--no-open', action='store_true', help='Ne rien ouvrir (toujours actif pour ce serveur).')
    a = p.parse_args()
    paths = {('/'+k): Path(v).resolve() for k, v in json.loads(Path(a.manifest).read_text()).items()}

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, *args):
            pass

        def do_HEAD(self):
            self.serve(False)

        def do_GET(self):
            self.serve(True)

        def serve(self, body):
            path = paths.get(self.path)
            if path is None or not path.is_file():
                self.send_error(404)
                return
            size = path.stat().st_size
            start, end, partial = 0, size-1, False
            header = self.headers.get('Range')
            if header:
                m = re.fullmatch(r'bytes=(\d+)-(\d*)', header)
                if not m:
                    self.send_error(416)
                    return
                start = int(m[1])
                end = min(size-1, int(m[2])) if m[2] else size-1
                partial = True
            if start > end or start >= size:
                self.send_error(416)
                return
            self.send_response(206 if partial else 200)
            self.send_header('Content-Length', str(end-start+1))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Type', 'video/mp4')
            if partial:
                self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.end_headers()
            if body:
                try:
                    with path.open('rb') as stream:
                        stream.seek(start)
                        left = end-start+1
                        while left:
                            data = stream.read(min(256*1024, left))
                            if not data:
                                break
                            self.wfile.write(data)
                            left -= len(data)
                except (BrokenPipeError, ConnectionResetError):
                    pass

    print(f'Serveur localhost:{a.port}, {len(paths)} fichiers autorisés.', flush=True)
    ThreadingHTTPServer(('127.0.0.1', a.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
