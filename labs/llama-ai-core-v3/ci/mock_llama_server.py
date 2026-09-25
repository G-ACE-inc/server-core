#!/usr/bin/env python3
import argparse, json, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class H(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass
    def send_json(self, code, obj):
        body=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path=='/health': return self.send_json(200,{'status':'ok'})
        if self.path in ('/v1/models','/models'):
            return self.send_json(200,{'object':'list','data':[{'id':self.server.model_id,'object':'model'}]})
        if self.path=='/metrics':
            body=b'llamacpp:requests_processing 0\nllamacpp:tokens_predicted_total 1\n'
            self.send_response(200); self.send_header('Content-Type','text/plain'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        return self.send_json(404,{'error':'not found'})
    def do_POST(self):
        if self.path!='/v1/chat/completions': return self.send_json(404,{'error':'not found'})
        n=int(self.headers.get('Content-Length','0')); raw=self.rfile.read(n)
        try: req=json.loads(raw)
        except Exception: return self.send_json(400,{'error':'bad json'})
        prompt=' '.join(str(m.get('content','')) for m in req.get('messages',[]))
        if '100 short debugging checks' in prompt: time.sleep(3.0)
        kwargs=req.get('chat_template_kwargs') or {}
        thinking=kwargs.get('enable_thinking') is True
        content=json.dumps({'served_by':self.server.model_id,'received_model':req.get('model'),'chat_template_kwargs':kwargs},ensure_ascii=False)
        msg={'role':'assistant','content':content,'reasoning_content':'mock reasoning' if thinking else ''}
        return self.send_json(200,{
            'id':'mock','object':'chat.completion','model':self.server.model_id,
            'choices':[{'index':0,'message':msg,'finish_reason':'stop'}],
            'usage':{'prompt_tokens':10,'completion_tokens':10,'total_tokens':20}
        })

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--port',type=int,required=True); ap.add_argument('--model-id',required=True); a=ap.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',a.port),H); server.model_id=a.model_id; server.serve_forever()
if __name__=='__main__': main()
