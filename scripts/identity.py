"""Conservative identities: never merge distinct DOIs on title similarity alone."""
import re
import unicodedata
from urllib.parse import unquote

def doi(value):
    value=unquote(str(value or '')).strip()
    match=re.search(r'10\.\d{4,9}/[^\s?#]+',value,re.I)
    if not match:return ''
    value=match.group().lower()
    return value

def identifier(p):
    raw=p.get('doi') or p.get('url','')
    key=doi(raw)
    if any(host in raw.lower() for host in ['biorxiv.org/','medrxiv.org/']):key=re.sub(r'(v\d+)?(?:\.full(?:-text)?|\.abstract)?/?$','',key)
    return key

def title(value):
    return ''.join(c for c in unicodedata.normalize('NFKC',value).casefold() if c.isalnum())

def duplicate(record,papers):
    key=identifier(record)
    for p in papers:
        other=identifier(p)
        if key and other:
            if key==other:return p
        elif title(record.get('title','')) and title(record['title'])==title(p.get('title','')):return p
    return None

def relations(p,papers):
    result=[]
    for other in papers:
        if other['id']==p['id']:continue
        for owner,target in [(p,other),(other,p)]:
            if owner.get('metadata',{}).get('status')!='matched':continue
            for r in owner['metadata'].get('relations',[]):
                if r.get('type') in ['is-preprint-of','has-preprint','is-version-of','has-version','is-identical-to'] and doi(r.get('id'))==identifier(target) and identifier(target):
                    result.append({'paper_id':other['id'],'title':other['title'],'type':r['type'],'source_id':owner['id']})
    return list({r['paper_id']:r for r in result}.values())
