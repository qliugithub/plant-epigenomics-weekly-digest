"""Canonical paper/issue records and immutable commentary revisions."""
import datetime as dt
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(name,default):
    path=ROOT/'data'/name
    return json.loads(path.read_text()) if path.exists() else default

def write(name,value):
    path=ROOT/'data'/name;path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2));temp.replace(path)

def snapshot(p):
    return {k:p[k] for k in ['title','heading','sections','translations','priority','date','journal','kind','url','doi','classification','tags','evidence'] if k in p}

def record_revision(p,reason):
    revisions=read('revisions.json',{})
    body=snapshot(p);digest=hashlib.sha256(json.dumps(body,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    history=revisions.setdefault(p['id'],[])
    if not history or history[-1]['hash']!=digest:
        history.append({'version':len(history)+1,'at':dt.datetime.now(dt.timezone.utc).isoformat(),'reason':reason,'hash':digest,'content':body})
        write('revisions.json',revisions)
    p['revision']=history[-1]['version']
    return p['revision']
