#!/usr/bin/env python3
import concurrent.futures, json, sys, time, urllib.error, urllib.request

BASE='http://127.0.0.1:18080'
KEY='ci-test-key'
ROLE_TO_MODEL={
 'evidence-reader':'granite-test','researcher':'granite-test',
 'constructive-analyst':'qwen3-test','causal-scout':'qwen3-test','diagnoser':'qwen3-test',
 'adversarial-auditor':'ministral-test','local-reviewer':'ministral-test',
 'code-scout':'coder-test','patch-engineer':'coder-test',
}

def req(method,url,key=None,obj=None,timeout=20):
    data=None; headers={}
    if key: headers['Authorization']='Bearer '+key
    if obj is not None:
        data=json.dumps(obj).encode(); headers['Content-Type']='application/json'
    r=urllib.request.Request(url,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(r,timeout=timeout) as x:
            raw=x.read(); c=x.headers.get('content-type','')
            return x.status,(json.loads(raw.decode()) if 'json' in c else raw.decode(errors='replace'))
    except urllib.error.HTTPError as e:
        raw=e.read()
        try: out=json.loads(raw.decode())
        except Exception: out=raw.decode(errors='replace')
        return e.code,out

def fail(msg):
    print('REAL_LLAMA_SWAP_CI_E2E=FAIL|'+msg); sys.exit(1)

def chat(model,prompt,max_tokens=32,timeout=30):
    return req('POST',BASE+'/v1/chat/completions',KEY,{
      'model':model,'messages':[{'role':'user','content':prompt}],
      'temperature':0,'max_tokens':max_tokens,'stream':False
    },timeout)

def wait():
    for _ in range(100):
        try:
            st,_=req('GET',BASE+'/health',timeout=1)
            if st==200:return
        except Exception: pass
        time.sleep(.1)
    fail('health_timeout')

def main():
    wait()
    st,_=req('GET',BASE+'/v1/models')
    if st!=401: fail(f'unauth_expected_401_got_{st}')
    st,obj=req('GET',BASE+'/v1/models',KEY)
    if st!=200: fail(f'auth_models_{st}')
    listed={x.get('id') for x in obj.get('data',[]) if x.get('id')}
    missing=set(ROLE_TO_MODEL)-listed
    if missing: fail('selectors_missing:'+','.join(sorted(missing)))

    for role,physical in ROLE_TO_MODEL.items():
        st,out=chat(role,'Reply OK.',16)
        if st!=200: fail(f'{role}_http_{st}:{out}')
        msg=(out.get('choices') or [{}])[0].get('message') or {}
        try: payload=json.loads(msg.get('content') or '{}')
        except Exception: fail(f'{role}_content_not_json:{msg}')
        if payload.get('served_by')!=physical: fail(f'{role}_served_by={payload.get("served_by")} expected={physical}')

    st,_=chat('does-not-exist','OK',8)
    if st!=404: fail(f'unknown_expected_404_got_{st}')

    st,scout=chat('causal-scout','Compute 17*19.',64)
    if st!=200: fail('scout_request')
    sm=(scout.get('choices') or [{}])[0].get('message') or {}
    sp=json.loads(sm.get('content') or '{}')
    if (sm.get('reasoning_content') or '').strip(): fail('scout_reasoning_not_disabled')
    if (sp.get('chat_template_kwargs') or {}).get('enable_thinking') is not False: fail('scout_filter_missing')

    st,think=chat('diagnoser','Compute 17*19.',64)
    if st!=200: fail('diagnoser_request')
    tm=(think.get('choices') or [{}])[0].get('message') or {}
    tp=json.loads(tm.get('content') or '{}')
    if not (tm.get('reasoning_content') or '').strip(): fail('diagnoser_reasoning_missing')
    if (tp.get('chat_template_kwargs') or {}).get('enable_thinking') is not True: fail('diagnoser_filter_missing')

    def long(role): return chat(role,'Generate a numbered list of 100 short debugging checks. Do not stop early.',256,20)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        a=ex.submit(long,'code-scout'); b=ex.submit(long,'diagnoser')
        time.sleep(1.0)
        st3,out3=chat('evidence-reader','Reply OK.',8,5)
        r1=a.result(); r2=b.result()
    if r1[0]!=200 or r2[0]!=200: fail(f'first_two_failed:{r1[0]},{r2[0]}')
    if st3!=429: fail(f'third_expected_429_got_{st3}:{out3}')

    metrics_status=None; metrics=None
    for _ in range(30):
        metrics_status,metrics=req('GET',BASE+'/metrics',KEY)
        if metrics_status==200 and isinstance(metrics,str) and metrics.strip(): break
        time.sleep(1)
    else:
        fail(f'metrics_not_ready:status={metrics_status}:body={metrics!r}')

    print('REAL_LLAMA_SWAP_CI_E2E=PASS')
    print(json.dumps({'roles':len(ROLE_TO_MODEL),'third_concurrent_status':st3,'scout_thinking':False,'diagnoser_thinking':True,'metrics_ready':True}))

if __name__=='__main__': main()
