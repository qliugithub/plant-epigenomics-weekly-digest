"""Offline tests: match identity, distinguish zero/missing, preserve cache and revisions."""
import sys,copy,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
import refresh_openalex as oa,store
p={'title':'Chromatin in pepper','doi':'10.1234/pepper','date':'2026-01-01'}
w={'id':'https://openalex.org/W123','title':p['title'],'doi':'https://doi.org/10.1234/pepper','cited_by_count':0,'referenced_works':['https://openalex.org/W42'],'counts_by_year':[{'year':2026,'cited_by_count':0}],'open_access':{'is_oa':True,'oa_url':'https://example.org/paper'},'best_oa_location':{'is_oa':True,'pdf_url':'javascript:alert(1)'},'authorships':[{'author':{'display_name':'A Researcher','id':'https://openalex.org/A42'},'institutions':[{'id':'https://openalex.org/I42','display_name':'Institute'}]}]}
r=oa.normalize_work(p,w,'doi_title');assert r['cited_by_count']==0 and r['referenced_works_count']==1 and r['pdf_url'] is None
assert oa.normalize_work(p,{**w,'cited_by_count':None},'doi_title')['cited_by_count'] is None
for bad in [{**w,'title':'An entirely different study'},{**w,'doi':'https://doi.org/10.1234/other'}]:
 try:oa.normalize_work(p,bad,'doi_title');raise AssertionError('Mismatch accepted')
 except ValueError:pass
no_doi={k:v for k,v in p.items() if k!='doi'}
oa.request=lambda _: {'results':[{**w,'publication_year':2026}]}
assert oa.fetch_paper(no_doi)['match_method']=='exact_title_year'
oa.request=lambda _: {'results':[{**w,'publication_year':2026},{**w,'publication_year':2026}]}
try:oa.fetch_paper(no_doi);raise AssertionError('Ambiguous title accepted')
except ValueError:pass
with tempfile.TemporaryDirectory() as folder:
 store.ROOT=Path(folder)
 existing={**p,'id':'paper-1','openalex':r};store.write('papers.json',[existing,{**p,'id':'paper-2'}]);store.write('revisions.json',{'sentinel':['unchanged']})
 def fail(_):raise TimeoutError()
 oa.fetch_paper=fail;oa.refresh(force=True)
 saved=store.read('papers.json',[])
 assert saved[0]['openalex']['cited_by_count']==0 and saved[0]['openalex']['last_error']=='unavailable'
 assert saved[1]['openalex']['status']=='unavailable' and 'cited_by_count' not in saved[1]['openalex']
 assert store.read('revisions.json',{})=={'sentinel':['unchanged']}
print('PASS: exact identity, missing versus zero, safe links, title ambiguity, stale cache and immutable commentary.')
