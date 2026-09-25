#!/usr/bin/env python3
import argparse, json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

class H(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass
    def send_json(self, code, obj):
        body=json.dumps(obj).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path=='/health': return self.send_json(200,{'status':'ok'})
        return self.send_json(404,{'error':'not found'})
    def do_POST(self):
        if self.path!='/ingest': return self.send_json(404,{'error':'not found'})
        n=int(self.headers.get('Content-Length','0')); raw=self.rfile.read(n)
        try: obj=json.loads(raw)
        except Exception: return self.send_json(400,{'status':'rejected','reason':'bad json'})
        with self.server.capture.open('a',encoding='utf-8') as f:
            f.write(json.dumps(obj,ensure_ascii=False)+'\n')
        return self.send_json(200,{'status':'accepted','hash':'ci-mock'})

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--capture',required=True); a=ap.parse_args()
    p=Path(a.capture); p.parent.mkdir(parents=True,exist_ok=True); p.write_text('')
    s=ThreadingHTTPServer(('127.0.0.1',3000),H); s.capture=p; s.serve_forever()
if __name__=='__main__': main()
