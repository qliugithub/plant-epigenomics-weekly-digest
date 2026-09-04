"""Collect an auditable candidate pool and check bibliographic metadata, not claims."""
import datetime as dt
import html
import json
import re
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from urllib.error import HTTPError
try:
    from .store import read,write
except ImportError:
    from store import read,write

def request(url):
    req=urllib.request.Request(url,headers={'User-Agent':'PlantEpigenomicsWeeklyDigest/3.0 (public research bibliography)','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=25) as response:return json.load(response)
def plain(s):return html.unescape(re.sub('<[^>]+>','',s or '')).strip()
def normalize(s):return re.sub(r'[^a-z0-9]','',plain(s).lower())
def doi_of(p):
    if p.get('doi'):return p['doi'].lower().removeprefix('https://doi.org/').strip()
    match=re.search(r'(10\.\d{4,9}/[^?#\s]+)',p.get('url',''))
    return re.sub(r'(v\d+)?(?:\.full(?:-text)?|/full)?/?$','',match.group(1)).lower() if match else ''
def today():return dt.datetime.now(dt.timezone.utc).date()
def timestamp():return dt.datetime.now(dt.timezone.utc).isoformat()
LANES={
 'solanaceae':'(Capsicum OR tomato OR Solanaceae OR potato) AND (epigenom* OR methylation OR histone OR chromatin OR "multi-omics" OR "fruit development" OR "fruit ripening")',
 'general':'(plant OR Arabidopsis OR fruit) AND ("DNA methylation" OR "histone modification" OR "chromatin accessibility" OR "chromatin remodeling" OR "H3K27me3")',
 'method':'(plant OR Capsicum OR tomato OR Arabidopsis) AND ("Fiber-seq" OR "CUT&Tag" OR "single-cell multiome" OR "single-nucleus" OR "epigenome editing" OR "multi-omics database" OR "cis-regulatory grammar")'
}
def collect(force=False):
    pool=read('candidates.json',{'records':[],'searches':[]});now=today()
    if not force and (pool.get('updated_at') or '')[:10]==str(now) and pool.get('searches') and all(s.get('ok') for s in pool['searches']):return pool
    start=now-dt.timedelta(days=28);papers=read('papers.json',[])
    seen_titles={normalize(p['title']) for p in papers};seen_dois={doi_of(p) for p in papers if doi_of(p)}
    existing={r['key']:r for r in pool.get('records',[])};searches=[];total=0
    for lane,terms in LANES.items():
        # Publication OR first-index date catches late indexing; original date remains visible.
        query=f'({terms}) AND (FIRST_PDATE:[{start} TO {now}] OR FIRST_IDATE:[{start} TO {now}])'
        cursor='*';count=0;complete=False
        try:
            for page in range(5):
                result=request('https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode(dict(query=query,format='json',resultType='core',pageSize=100,cursorMark=cursor)))
                batch=result.get('resultList',{}).get('result',[])
                for r in batch:
                    title=plain(r.get('title',''));doi=r.get('doi','').lower();source=r.get('source','');rid=r.get('id','')
                    if not title or not rid:continue
                    key=doi or source+':'+rid;old=existing.get(key,{})
                    abstract=plain(r.get('abstractText',''));text=(title+' '+abstract).lower();weights={'capsicum':8,'tomato':6,'solanaceae':6,'fruit':4,'methylation':4,'chromatin':4,'histone':4,'multi-omics':2}
                    record=dict(key=key,title=title,doi=doi,date=r.get('firstPublicationDate',''),journal=r.get('journalInfo',{}).get('journal',{}).get('title') or 'Europe PMC',kind='预印本' if source=='PPR' or 'preprint' in json.dumps(r.get('pubTypeList',{})).lower() else '期刊记录（审稿状态请核对原文）',url='https://doi.org/'+doi if doi else 'https://europepmc.org/article/'+urllib.parse.quote(source)+'/'+urllib.parse.quote(rid),abstract=abstract,score=sum(w for term,w in weights.items() if term in text),lanes=sorted(set(old.get('lanes',[])+[lane])),first_seen=old.get('first_seen',timestamp()),last_seen=timestamp(),recommended=normalize(title) in seen_titles or bool(doi and doi in seen_dois),source='Europe PMC')
                    existing[key]=record;count+=1
                nxt=result.get('nextCursorMark')
                if not batch or not nxt or nxt==cursor or count>=int(result.get('hitCount',0)):complete=True;break
                cursor=nxt
            searches.append(dict(lane=lane,ok=complete,count=count,query=query,at=timestamp(),error=None if complete else 'retrieval_cap'))
        except Exception as exc:searches.append(dict(lane=lane,ok=False,count=count,query=query,at=timestamp(),error=type(exc).__name__))
        total+=count
    records=sorted(existing.values(),key=lambda r:(r.get('date',''),r['score']),reverse=True)
    pool=dict(updated_at=timestamp(),records=records,searches=searches,retrieved=total,partial=not all(s['ok'] for s in searches))
    write('candidates.json',pool);print(f'Candidate pool: {len(records)} unique retained records; {sum(s["ok"] for s in searches)}/3 complete search lanes.')
    return pool

def metadata_from(p,message):
    title=plain((message.get('title') or [''])[0]);match=SequenceMatcher(None,normalize(title),normalize(p['title'])).ratio()
    # Even an exact DOI is insufficient if the title resolves to another work.
    if match<.94:return dict(status='conflict',bibliography={'title':title,'doi':message.get('DOI','')},differences=[{'zh':'检索标题与原记录不一致，请核对原文。','en':'The retrieved title differs from the archived record. Check the original.'}],relations=[],updates=[])
    dates=[]
    for k in ['published-online','published-print','published','issued']:
        parts=message.get(k,{}).get('date-parts',[[]])[0]
        if parts:dates.append('-'.join([str(parts[0])]+[f'{v:02d}' for v in parts[1:]]))
    date=next((d for d in dates if len(d)==10),dates[0] if dates else '')
    differences=[]
    if date and len(date)==10 and p.get('date') and date!=p['date']:differences.append({'zh':f'出版方日期 {date} 与原周报日期 {p["date"]} 不同；保留历史记录。','en':f'Publisher date {date} differs from archived date {p["date"]}; the historical record is preserved.'})
    relations=[]
    for kind,items in message.get('relation',{}).items():
        for item in items:
            if item.get('id-type')=='doi':relations.append({'type':kind,'id':item['id'],'url':'https://doi.org/'+item['id']})
    updates=[{'type':u.get('type','update'),'doi':u.get('DOI',''),'url':'https://doi.org/'+u['DOI']} for u in message.get('update-to',[]) if u.get('DOI')]
    return dict(status='matched',bibliography=dict(title=title,doi=message.get('DOI',''),journal=plain((message.get('container-title')or[''])[0]),date=date,authors=[{k:a[k] for k in ['family','given'] if k in a} for a in message.get('author',[])],type=message.get('type','')),differences=differences,relations=relations,updates=updates)

def verify(force=False):
    papers=read('papers.json',[]);checked=0
    for p in papers:
        old=p.get('metadata',{})
        if not force and old.get('checked_at') and (today()-dt.date.fromisoformat(old['checked_at'][:10])).days<7:continue
        doi=doi_of(p);source='https://api.crossref.org/works/'+urllib.parse.quote(doi,safe='') if doi else 'https://api.crossref.org/works?'+urllib.parse.urlencode({'query.title':p['title'],'rows':1})
        try:
            response=request(source);message=response.get('message',{})
            if not doi:message=next(iter(message.get('items',[])),{})
            result=metadata_from(p,message) if message else {'status':'not_found','relations':[],'updates':[]}
            result.update(checked_at=timestamp(),source_url=source)
            # Crossref's update-to is carried by update notices; query notices targeting this DOI too.
            if result['status']=='matched' and result['bibliography'].get('doi'):
                try:
                    notices=request('https://api.crossref.org/works?'+urllib.parse.urlencode({'filter':'updates:'+result['bibliography']['doi'],'rows':20})).get('message',{}).get('items',[])
                    for notice in notices:
                        target=[u for u in notice.get('update-to',[]) if u.get('DOI','').lower()==result['bibliography']['doi'].lower()]
                        if target and notice.get('DOI'):result['updates'].append({'type':target[0].get('type','update'),'doi':notice['DOI'],'url':'https://doi.org/'+notice['DOI']})
                    result['update_check']='completed'
                except Exception:result['update_check']='unavailable'
            if old and old.get('bibliography')!=result.get('bibliography'):result['history']=old.get('history',[])+[{'at':old.get('checked_at'),'status':old.get('status'),'bibliography':old.get('bibliography')}]
            elif old.get('history'):result['history']=old['history']
            p['metadata']=result
        except Exception as exc:
            if old.get('status')=='matched':p['metadata']={**old,'last_attempt_at':timestamp(),'last_error':type(exc).__name__}
            else:p['metadata']={'status':'not_found' if isinstance(exc,HTTPError) and exc.code==404 else 'error','checked_at':timestamp(),'source_url':source,'error':type(exc).__name__}
        checked+=1
    write('papers.json',papers);print(f'Bibliographic checks: {checked}; statuses: '+json.dumps({s:sum(p.get('metadata',{}).get('status')==s for p in papers) for s in ['matched','conflict','not_found','error']}))
if __name__=='__main__':collect();verify()
