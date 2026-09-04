"""Resolve a DOI to an abstract-backed candidate; never fetch arbitrary input URLs."""
import datetime as dt
import urllib.parse
try:
    from .identity import doi,duplicate
    from .refresh_resources import request,plain,timestamp
except ImportError:
    from identity import doi,duplicate
    from refresh_resources import request,plain,timestamp

def resolve(value,papers):
    key=doi(value)
    if not key:raise ValueError('Enter a DOI or a link containing a DOI.')
    # Strip publisher display suffixes only for known preprint URLs.
    if any(host in value.lower() for host in ['biorxiv.org/','medrxiv.org/']):
        import re
        key=re.sub(r'(v\d+)?(?:\.full(?:-text)?|\.abstract)?/?$','',key)
    existing=duplicate({'doi':key,'title':''},papers)
    if existing:return None,existing
    query=urllib.parse.urlencode({'query':'DOI:"'+key+'"','format':'json','resultType':'core','pageSize':10})
    records=request('https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+query).get('resultList',{}).get('result',[])
    r=next((r for r in records if doi(r.get('doi'))==key and plain(r.get('abstractText'))),None)
    if not r:raise ValueError('No matching indexed abstract found for this DOI. Nothing was added; try again after indexing or supply the paper for manual review.')
    record=dict(key=key,doi=key,title=plain(r.get('title')),abstract=plain(r['abstractText']),date=r.get('firstPublicationDate',''),journal=r.get('journalInfo',{}).get('journal',{}).get('title') or 'Europe PMC',kind='预印本' if r.get('source')=='PPR' else '期刊记录（审稿状态请核对原文）',url='https://doi.org/'+key,score=0,lanes=['manual'],recommended=False,last_seen=timestamp(),first_seen=timestamp(),source='Europe PMC')
    if not record['title']:raise ValueError('Missing source title; nothing added.')
    return record,duplicate(record,papers)
