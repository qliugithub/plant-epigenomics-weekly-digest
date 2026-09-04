"""Cache OpenAlex bibliometrics separately from immutable scientific commentary."""
import datetime as dt
import json
import os
import re
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError
from difflib import SequenceMatcher
try:
    from .store import read, write
    from .identity import identifier, doi, title
except ImportError:
    from store import read, write
    from identity import identifier, doi, title

def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def request(path):
    query={'api_key':os.environ['OPENALEX_API_KEY']} if os.environ.get('OPENALEX_API_KEY') else {}
    url='https://api.openalex.org/'+path
    if query:url+=('&' if '?' in url else '?')+urllib.parse.urlencode(query)
    req=urllib.request.Request(url,headers={'User-Agent':'PlantEpigenomicsDigest/4.0','Accept':'application/json'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
        except (HTTPError,URLError,TimeoutError) as exc:
            if attempt==2 or isinstance(exc,HTTPError) and exc.code not in [429,500,502,503,504]:raise
            time.sleep(2**attempt)

def valid_url(value):
    if not isinstance(value,str):return None
    try:
        parsed=urllib.parse.urlsplit(value)
        return value if parsed.scheme=='https' and parsed.hostname and not parsed.username and not parsed.password else None
    except ValueError:return None

def count(value):return value if type(value) is int and value>=0 else None

def lookup_doi(p):
    m=p.get('metadata',{})
    return identifier(p) or (doi(m.get('bibliography',{}).get('doi')) if m.get('status')=='matched' else '')

def normalize_work(p,w,method):
    key=lookup_doi(p)
    # A preprint may redirect to a merged published work. Do not silently assign its count.
    if key and doi(w.get('doi'))!=key:raise ValueError('doi_conflict')
    if SequenceMatcher(None,title(p['title']),title(w.get('title') or w.get('display_name') or '')).ratio()<.94:raise ValueError('title_conflict')
    if not re.fullmatch(r'https://openalex.org/W\d+',w.get('id','')):raise ValueError('invalid_work_id')
    oa=w.get('open_access') or {};location=w.get('best_oa_location') or {}
    authors=[];institutions={}
    for a in w.get('authorships') or []:
        author=a.get('author') or {}
        if author.get('display_name'):authors.append({'name':author['display_name'],'url':valid_url(author.get('id')),'orcid':valid_url(author.get('orcid'))})
        for inst in a.get('institutions') or []:
            if inst.get('display_name'):institutions[inst.get('id') or inst['display_name']]={'name':inst['display_name'],'url':valid_url(inst.get('id')),'country':inst.get('country_code')}
    series=[{'year':r['year'],'cited_by_count':r['cited_by_count']} for r in w.get('counts_by_year') or [] if type(r.get('year')) is int and count(r.get('cited_by_count')) is not None]
    refs=w.get('referenced_works')
    return dict(status='matched',match_method=method,checked_at=now(),source_updated_at=w.get('updated_date'),id=w['id'],doi=doi(w.get('doi')),cited_by_count=count(w.get('cited_by_count')),referenced_works_count=count(w.get('referenced_works_count')) if count(w.get('referenced_works_count')) is not None else len(refs) if isinstance(refs,list) else None,counts_by_year=sorted(series,key=lambda r:r['year'],reverse=True),authors=authors,institutions=list(institutions.values()),is_oa=oa.get('is_oa') if type(oa.get('is_oa')) is bool else None,oa_status=oa.get('oa_status'),oa_url=valid_url(oa.get('oa_url')) if oa.get('is_oa') is True else None,pdf_url=valid_url(location.get('pdf_url')) if location.get('is_oa') is True else None,is_retracted=w.get('is_retracted') is True)

def fetch_paper(p):
    key=lookup_doi(p)
    if key:return normalize_work(p,request('works/https://doi.org/'+urllib.parse.quote(key,safe='/')),'doi_title')
    candidates=request('works?'+urllib.parse.urlencode({'search':p['title'],'per_page':5})).get('results',[])
    exact=[w for w in candidates if title(w.get('title') or w.get('display_name') or '')==title(p['title']) and str(w.get('publication_year',''))==p.get('date','')[:4]]
    if len(exact)!=1:raise ValueError('no_unique_title_year_match')
    return normalize_work(p,exact[0],'exact_title_year')

def refresh(force=False):
    papers=read('papers.json',[]);results={};today=dt.datetime.now(dt.timezone.utc)
    for p in papers:
        old=p.get('openalex',{});last=old.get('last_attempt_at') or old.get('checked_at')
        try:fresh=last and (today-dt.datetime.fromisoformat(last)).total_seconds()<7*86400
        except (ValueError,TypeError):fresh=False
        if fresh and not force:continue
        try:p['openalex']=fetch_paper(p)
        except Exception as exc:
            reason=('not_found' if exc.code==404 else 'rate_limited' if exc.code==429 else 'access_error' if exc.code in [401,403] else 'unavailable') if isinstance(exc,HTTPError) else 'conflict' if isinstance(exc,ValueError) else 'unavailable'
            if old.get('status')=='matched':p['openalex']={**old,'last_attempt_at':now(),'last_error':reason}
            else:p['openalex']={'status':reason,'last_attempt_at':now()}
        results[p['openalex']['status']]=results.get(p['openalex']['status'],0)+1
    write('papers.json',papers)
    print('OpenAlex refresh: '+json.dumps(results)+'; unavailable counts remain unknown.')
if __name__=='__main__':refresh()
