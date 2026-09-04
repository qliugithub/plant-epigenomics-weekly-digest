import sys,json,tempfile,os,copy
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
import store,update_digest as u,refresh_resources as rr,build_site as build
from catalog import TAXONOMY
papers=store.read('papers.json',[])
assert len(papers)>=13
for p in papers:
 assert len(p['sections'])==len(p['translations']['en']['sections'])==6
assert rr.doi_of({'url':'https://www.biorxiv.org/content/10.1234/2026.01.01.42v2.full-text'})=='10.1234/2026.01.01.42'
p={'title':'Chromatin accessibility in pepper fruit','date':'2026-08-20'}
m={'title':[p['title']],'DOI':'10.test/x','published-online':{'date-parts':[[2026,8,19]]},'author':[{'given':'A','family':'Liu'}],'relation':{'is-preprint-of':[{'id-type':'doi','id':'10.test/y'}]}}
r=rr.metadata_from(p,m);assert r['status']=='matched' and r['differences'] and r['relations']
assert rr.metadata_from(p,{**m,'title':['Completely unrelated study']})['status']=='conflict'
with tempfile.TemporaryDirectory() as folder:
 store.ROOT=u.ROOT=Path(folder);(store.ROOT/'dist').mkdir()
 store.write('issues.json',[]);store.write('papers.json',[])
 record={'key':'10.test/42','title':'Tomato fruit chromatin','abstract':'Evidence','doi':'10.test/42','date':str(rr.today()),'journal':'Test','kind':'预印本','url':'https://doi.org/10.test/42','score':12,'lanes':['solanaceae'],'recommended':False,'last_seen':str(rr.today())}
 pool={'records':[record],'searches':[{'ok':True}],'retrieved':1,'partial':False}
 u.collect=lambda:copy.deepcopy(pool);os.environ['OPENAI_API_KEY']='offline-test'
 result={'summary':'中文','summary_en':'English','papers':[{'id':0,'heading':'标题','priority':'全文精读','tags':[],'classification':{k:[] for k in TAXONOMY},'sections':[{'label':v,'text':'Test'} for v in ['真正的新发现','机制或方法上的关键点','与你的辣椒研究关系','对22组织图谱的具体启示','需要注意','建议优先看']],'translations':{'en':{'heading':'Title','sections':[{'label':v,'text':'Evidence'} for v in ['What is new','Mechanistic or methodological key point','Relevance to pepper research','Implications for the 22-tissue atlas','Limitations','What to read first']]}}}]}
 u.request=lambda *args,**kwargs:{'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(result)}]}]}
 u.main();assert len(store.read('papers.json',[]))==1
 assert store.read('issues.json',[])[0]['entries'][0]['revision']==1
 before=store.read('issues.json',[]);u.main();assert store.read('issues.json',[])==before
 # English omissions must fail before adding an issue or changing paper records.
 store.write('issues.json',[]);before=store.read('papers.json',[]);store.write('papers.json',[]);result['papers'][0]['translations']['en']['sections'].pop()
 try:u.main();raise AssertionError('Missing English accepted')
 except ValueError:pass
 assert store.read('papers.json',[])==[] and store.read('issues.json',[])==[]
 # A revision leaves the prior snapshot intact.
 p=before[0];p['heading']='Revised';store.record_revision(p,'test');assert p['revision']==2
 h=store.read('revisions.json',{})[p['id']];assert h[0]['content']['heading']=='标题'
 # Partial retrieval retains prior records and exposes failure.
 store.write('candidates.json',{'records':[record],'searches':[]})
 def mock(url):
  if 'Capsicum' in url:raise TimeoutError()
  return {'resultList':{'result':[{'id':'99','source':'MED','title':'Plant chromatin','doi':'10.test/99','abstractText':'A'}]},'hitCount':1}
 rr.request=mock;out=rr.collect(force=True);assert out['partial'] and any(r['key']=='10.test/42' for r in out['records'])
print('PASS: metadata mismatch, DOI version handling, bilingual generator validation, idempotence, immutable revisions and partial retrieval preservation.')
